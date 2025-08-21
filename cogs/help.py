# cogs/help.py
import inspect
from typing import Dict, List, Tuple
import discord
from discord.ext import commands

# Map cog names to a nice title + emoji + order
COG_META = {
    "CoreGames": ("🎯 Core Games", 0),
    "Stats": ("📊 Stats", 1),
    # Add more cogs here if you like:
    # "Economy": ("💰 Economy", 2),
    # "Quests": ("🗺️ Quests", 3),
    # "Admin": ("🛠️ Admin", 4),
}

def chunk(lst: List[str], n: int) -> List[List[str]]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def command_signature(cmd: commands.Command) -> str:
    """Make a compact prefix-style signature, e.g. !choose <options>"""
    prefix = "!"
    params = []
    for name, p in cmd.clean_params.items():
        # Optional -> [arg], required -> <arg>
        if p.default is not inspect._empty:
            params.append(f"[{name}]")
        else:
            params.append(f"<{name}>")
    sig = f"{prefix}{cmd.name}"
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
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
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
            pages[cog_name] = self._embed_for(ctx, label, cmds)
            order.append((cog_name, label))
            used.add(cog_name)

        for cog_name, cmds in grouped.items():
            if cog_name in used:
                continue
            label = f"📦 {cog_name}"
            pages[cog_name] = self._embed_for(ctx, label, cmds)
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

    def _embed_for(self, ctx: commands.Context, title: str, cmds: List[commands.Command]) -> discord.Embed:
        emb = discord.Embed(title=title, color=discord.Color.blurple())
        emb.set_footer(text=f"Requested by {ctx.author.display_name}")

        # Build compact signatures like `!choose <options>`
        sigs = [f"`{command_signature(c)}`" for c in cmds]

        # Split safely into two columns
        mid = (len(sigs) + 1) // 2  # ceil(len/2)
        left_col = sigs[:mid]
        right_col = sigs[mid:]

        left = "\n".join(left_col) if left_col else "—"
        right = "\n".join(right_col) if right_col else "—"

        emb.add_field(name="Commands", value=left, inline=True)
        emb.add_field(name="\u200b", value=right, inline=True)
        emb.add_field(
            name="\u200b",
            value="*Tip:* Separate list options with `|`, e.g. `!choose pizza | tacos | sushi`",
            inline=False,
        )
        return emb


async def setup(bot: commands.Bot):
    bot.help_command = None  # disable default
    await bot.add_cog(PrettyHelp(bot))
