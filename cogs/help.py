# cogs/help.py
import inspect
from typing import Dict, List, Tuple
import discord
from discord.ext import commands

# Map cog class names to a nice title + emoji + order
# NOTE: Keys must match each Cog class name (e.g., class CoreGames(...): -> "CoreGames")
COG_META = {
    "CoreGames": ("🎯 Core Games", 0),
    "Brettventures": ("🧭 Brettventures", 1),
    "Stats": ("📊 Stats & Leaderboards", 2),
    # Add more cogs here if you like:
    # "Economy": ("💰 Economy", 3),
    # "Quests": ("🗺️ Quests", 4),
    # "Admin": ("🛠️ Admin", 5),
}

# Optional per-cog usage tips shown at the bottom of each page
COG_TIPS = {
    "CoreGames": "*Tip:* Separate list options with `|`, e.g. `!choose pizza | tacos | sushi`",
    "Brettventures": (
        "**Brettventures basics**\n"
        "• Start: `!adventure start`\n"
        "• Your stats: `!adventure stats`\n"
        "• Explore (uses stamina): `!adventure explore`\n"
        "• Train a stat: `!adventure train <STR|AGI|INT|POW|SMT>`\n"
        "• Rest / stamina: `!adventure rest`\n"
        "_Stamina regenerates over time; check `!adventure stats` for ETA._"
    ),
    "Stats": "*Tip:* Try `!leaderboard` and `!mystats` after you’ve been rolling for a bit.",
}

def chunk(lst: List[str], n: int) -> List[List[str]]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def command_signature(cmd: commands.Command) -> str:
    """Make a compact prefix-style signature, e.g. !adventure start <arg>"""
    prefix = "!"
    # Use qualified_name so subcommands show as 'adventure start'
    sig = f"{prefix}{cmd.qualified_name}"
    params: List[str] = []
    for name, p in cmd.clean_params.items():
        # Optional -> [arg], required -> <arg>
        if p.default is not inspect._empty:
            params.append(f"[{name}]")
        else:
            params.append(f"<{name}>")
    if params:
        sig += " " + " ".join(params)
    return sig

class HelpSelect(discord.ui.Select):
    def __init__(self, pages: Dict[str, discord.Embed], order: List[Tuple[str, str]]):
        options = [discord.SelectOption(label=label, value=key) for key, label in order]
        super().__init__(placeholder="Select a category…", options=options, min_values=1, max_values=1)
        self.pages = pages
        self.order = order

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        await interaction.response.edit_message(embed=self.pages[key], view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, pages: Dict[str, discord.Embed], order: List[Tuple[str, str]]):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(pages, order))

class PrettyHelp(commands.Cog):
    """Custom, pretty help with categories and grids."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        # 1) Group commands by cog (only those the user can run)
        grouped: Dict[str, List[commands.Command]] = {}
        for cmd in sorted(self.bot.commands, key=lambda c: c.qualified_name):
            if cmd.hidden:
                continue
            try:
                if not await cmd.can_run(ctx):
                    continue
            except Exception:
                # If can_run check fails for any reason, show it anyway
                pass

            cog_name = cmd.cog_name or "Other"
            grouped.setdefault(cog_name, []).append(cmd)

        # Hide this help cog from the dropdown
        grouped.pop("PrettyHelp", None)

        # 2) Build pages in COG_META order, then add any leftovers
        pages: Dict[str, discord.Embed] = {}
        order: List[Tuple[str, str]] = []
        used = set()

        for cog_name, (label, _) in sorted(COG_META.items(), key=lambda x: x[1][1]):
            cmds = grouped.get(cog_name, [])
            if not cmds:
                continue
            pages[cog_name] = self._embed_for(ctx, label, cmds, tip=COG_TIPS.get(cog_name))
            order.append((cog_name, label))
            used.add(cog_name)

        for cog_name, cmds in grouped.items():
            if cog_name in used:
                continue
            label = f"📦 {cog_name}"
            pages[cog_name] = self._embed_for(ctx, label, cmds, tip=COG_TIPS.get(cog_name))
            order.append((cog_name, label))

        if not pages:
            await ctx.send(embed=discord.Embed(
                title="Brett Bot Help",
                description="No commands available here. Try again later.",
                color=discord.Color.blurple(),
            ))
            return

        if len(pages) == 1:
            await ctx.send(embed=next(iter(pages.values())))
            return

        first_key = order[0][0]
        await ctx.send(embed=pages[first_key], view=HelpView(pages, order))

    def _embed_for(self, ctx: commands.Context, title: str, cmds: List[commands.Command], tip: str | None = None) -> discord.Embed:
        emb = discord.Embed(title=title, color=discord.Color.blurple())
        emb.set_footer(text=f"Requested by {ctx.author.display_name}")

        # Build compact signatures like `!adventure start <options>`
        sigs = [f"`{command_signature(c)}`" for c in cmds]

        # Split safely into two columns
        mid = (len(sigs) + 1) // 2  # ceil(len/2)
        left_col = sigs[:mid]
        right_col = sigs[mid:]

        left = "\n".join(left_col) if left_col else "—"
        right = "\n".join(right_col) if right_col else "—"

        emb.add_field(name="Commands", value=left, inline=True)
        emb.add_field(name="\u200b", value=right, inline=True)

        if tip:
            emb.add_field(name="\u200b", value=tip, inline=False)

        return emb


async def setup(bot: commands.Bot):
    bot.help_command = None  # disable default
    await bot.add_cog(PrettyHelp(bot))
