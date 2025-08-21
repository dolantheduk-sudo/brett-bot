import inspect
from typing import Dict, List, Tuple
import discord
from discord.ext import commands

# Map cog names to a nice title + emoji
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
    # e.g. !choose <option|option|option>
    prefix = "!"
    params = []
    for name, p in cmd.clean_params.items():
        # Optional gets []
        if p.default is not inspect._empty:
            params.append(f"[{name}]")
        else:
            params.append(f"<{name}>")
    sig = f"{prefix}{cmd.name}"
    if params:
        sig += " " + " ".join(params)
    return sig

def format_command_line(cmd: commands.Command) -> str:
    desc = cmd.help.splitlines()[0] if (cmd.help and cmd.help.strip()) else ""
    return f"`{command_signature(cmd)}` — {desc}".strip()

class HelpSelect(discord.ui.Select):
    def __init__(self, pages: Dict[str, discord.Embed], order: List[str]):
        options = [
            discord.SelectOption(label=label, value=key)
            for key, label in order
        ]
        super().__init__(placeholder="Select a category…", options=options, min_values=1, max_values=1)
        self.pages = pages
        self.order = order

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        await interaction.response.edit_message(embed=self.pages[key], view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, pages: Dict[str, discord.Embed], order: List[str]):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(pages, order))

class PrettyHelp(commands.Cog):
    """Custom, pretty help with categories and grids."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        # Build pages from loaded cogs & commands
        pages: Dict[str, discord.Embed] = {}
        order: List[Tuple[str, str]] = []  # (key, label)

        # Group commands by cog (that are visible and can run)
        grouped: Dict[str, List[commands.Command]] = {}
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if cmd.hidden:
                continue
            # Check if user can run it (ignore failures silently)
            try:
                can_run = await cmd.can_run(ctx)
            except Exception:
                can_run = True
            if not can_run:
                continue

            cog_name = cmd.cog_name or "Other"
            grouped.setdefault(cog_name, []).append(cmd)
            # remove self from dropdown
            grouped.pop("PrettyHelp", None)

        # Create an embed page per known cog in COG_META order first
        used_keys = set()
        for cog_name, (label, _) in sorted(COG_META.items(), key=lambda x: x[1][1]):
            cmds = grouped.get(cog_name, [])
            if not cmds:
                continue
            emb = self._embed_for(ctx, label, cmds)
            pages[cog_name] = emb
            order.append((cog_name, label))
            used_keys.add(cog_name)

        # Any other cogs not listed in COG_META get a simple page
        for cog_name, cmds in grouped.items():
            if cog_name in used_keys:
                continue
            label = f"📦 {cog_name}"
            emb = self._embed_for(ctx, label, cmds)
            pages[cog_name] = emb
            order.append((cog_name, label))

        # If nothing, show a fallback
        if not pages:
            fallback = discord.Embed(
                title="Brett Bot Help",
                description="No commands available here. Try again later.",
                color=discord.Color.blurple(),
            )
            await ctx.send(embed=fallback)
            return

        # If only one page, send a single embed
        if len(pages) == 1:
            await ctx.send(embed=next(iter(pages.values())))
            return

        # Otherwise send with dropdown to switch categories
        first_key = order[0][0]
        await ctx.send(embed=pages[first_key], view=HelpView(pages, order))

    def _embed_for(self, ctx: commands.Context, title: str, cmds: List[commands.Command]) -> discord.Embed:
        emb = discord.Embed(
            title=title,
            color=discord.Color.blurple()
        )
        emb.set_footer(text=f"Requested by {ctx.author.display_name}")

        # Format as a “grid”: two columns of lines using inline fields
        lines = [format_command_line(c) for c in cmds]
        # two columns
        columns = chunk(lines, (len(lines) + 1) // 2)
        # Ensure exactly 2 columns
        if len(columns) == 1:
            columns.append([])

        left = "\n".join(columns[0]) or "—"
        right = "\n".join(columns[1]) or "—"

        emb.add_field(name="Commands", value=left, inline=True)
        emb.add_field(name="\u200b", value=right, inline=True)

        # Tip
        emb.add_field(
            name="\u200b",
            value="*Tip:* Use backticks for arguments with spaces, e.g. `!choose pizza | tacos | sushi`",
            inline=False
        )
        return emb

async def setup(bot: commands.Bot):
    # Disable default help (if not already)
    bot.help_command = None
    await bot.add_cog(PrettyHelp(bot))
