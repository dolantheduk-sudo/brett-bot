import io
import json
from discord.ext import commands

from constants import BRETT_RESPONSES, BRETT_QUOTES, EMOJI_FOR, MILESTONES
from utils.storage import load_stats, save_stats
from utils.helpers import emoji_bar, big_emoji_bar, pct

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="OLDhelp")
    async def help_cmd(self, ctx):
        await ctx.send("\n".join(HELP_LINES))

    @commands.command(name="stats")
    async def stats_cmd(self, ctx, member=None):
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member):
            member = ctx.author

        stats = load_stats(BRETT_RESPONSES)
        u = stats.get("users", {}).get(str(member.id))
        if not u:
            await ctx.send(f"{member.display_name} has no Brett stats yet.")
            return

        total = int(u.get("total", 0))
        lines = [f"📊 **{member.display_name}** — {total} roll{'s' if total != 1 else ''}"]
        for name in BRETT_RESPONSES:
            c = int(u["outcomes"].get(name, 0))
            lines.append(f"- {name}: **{c}** ({pct(c, total)})  {emoji_bar(c, total)}")

        streak_days = int(u.get("streak_days", 0))
        if streak_days > 1:
            lines.append(f"🔥 Streak: **{streak_days}** day(s)")

        # Next milestone
        next_m = next((m for m in MILESTONES if total < m), None) if MILESTONES else None
        if next_m:
            lines.append(f"🎯 Next milestone: **{next_m}** rolls (need {next_m - total} more)")

        await ctx.send("\n".join(lines))

    @commands.command(name="allstats")
    async def allstats_cmd(self, ctx):
        stats = load_stats(BRETT_RESPONSES)
        g = stats.get("global", {})
        total = int(g.get("total", 0))
        outcomes = g.get("outcomes", {})

        lines = [f"🌐 **Global Brett Stats** — {total} total roll{'s' if total != 1 else ''}"]
        for name in BRETT_RESPONSES:
            c = int(outcomes.get(name, 0))
            lines.append(f"- {name}: **{c}** ({pct(c, total)})")

        # Server-local top rollers
        rows = []
        guild_members = {m.id: m.display_name for m in ctx.guild.members} if ctx.guild else {}
        for uid_str, u in stats.get("users", {}).items():
            uid = int(uid_str)
            if guild_members and uid not in guild_members:
                continue
            rows.append((int(u.get("total", 0)), guild_members.get(uid, f"User {uid}")))
        rows.sort(reverse=True)

        if rows:
            top = rows[:10]
            lines.append("\n🏆 **Top Rollers**")
            for rank, (count, name) in enumerate(top, start=1):
                lines.append(f"{rank}. **{name}** — {count}")

        await ctx.send("\n".join(lines))

    @commands.command(name="exportstats")
    async def exportstats_cmd(self, ctx, member=None):
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member):
            member = ctx.author

        stats = load_stats(BRETT_RESPONSES)
        u = stats.get("users", {}).get(str(member.id))
        if not u:
            await ctx.send(f"No stats to export for {member.display_name}.")
            return

        payload = json.dumps(u, indent=2).encode("utf-8")
        try:
            await member.send(file=discord.File(fp=io.BytesIO(payload), filename="brett_stats.json"))
        except Exception:
            await ctx.send(file=discord.File(fp=io.BytesIO(payload), filename="brett_stats.json"))
        else:
            await ctx.send("📩 Sent to your DMs.")

    @commands.command(name="chart")
    async def chart_cmd(self, ctx, member=None):
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member):
            member = ctx.author

        stats = load_stats(BRETT_RESPONSES)
        u = stats.get("users", {}).get(str(member.id))
        if not u or not int(u.get("total", 0)):
            await ctx.send(f"{member.display_name} has no stats yet.")
            return

        total = int(u["total"])
        rows = sorted(
            ((int(u["outcomes"].get(n, 0)), n) for n in BRETT_RESPONSES),
            key=lambda x: (-x[0], x[1])
        )

        lines = [
            f"📊 **{member.display_name}** — {total} total roll{'s' if total != 1 else ''}",
            "```"
        ]
        for c, name in rows:
            bar = big_emoji_bar(c, total, width=28)
            lines.append(f"{EMOJI_FOR.get(name, '🎲')} {name:<18} | {bar}  {c:>3} ({(100*c/total):.1f}%)")
        lines.append("```")

        top_count, top_name = rows[0]
        if top_count > 0:
            lines.append(f"⭐ Most rolled: **{top_name}** × {top_count} ({(100*top_count/total):.1f}%)")

        await ctx.send("\n".join(lines))

    @commands.command(name="brettquote")
    async def brettquote_cmd(self, ctx):
        import random
        await ctx.send(f"📢 **Brett Quote of the Day:** {random.choice(BRETT_QUOTES)}")

    @commands.command(name="streak")
    async def streak_cmd(self, ctx, member=None):
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member):
            member = ctx.author

        stats = load_stats(BRETT_RESPONSES)
        u = stats.get("users", {}).get(str(member.id))
        if not u or int(u.get("streak_days", 0)) == 0:
            await ctx.send(f"{member.display_name} has no current streak.")
            return

        await ctx.send(f"🔥 {member.display_name} streak: **{int(u['streak_days'])}** day(s)")

    @commands.command(name="odds")
    async def odds_cmd(self, ctx):
        per = 100 / len(BRETT_RESPONSES)
        lines = ["🎯 **Brett Odds (default)**"]
        for name in BRETT_RESPONSES:
            lines.append(f"- {name}: {per:.1f}%")
        await ctx.send("\n".join(lines))

    @commands.command(name="leaderboard", aliases=["top", "lb"])
    async def leaderboard_cmd(self, ctx):
        stats = load_stats(BRETT_RESPONSES)
        users = stats.get("users", {})
        rows = sorted(((int(u.get("total", 0)), int(uid)) for uid, u in users.items()),
                      reverse=True)[:10]

        if not rows:
            await ctx.send("No rolls yet — time to `!brett`!")
            return

        lines = ["🏆 **Brett Leaderboard** (global)"]
        for rank, (count, uid) in enumerate(rows, start=1):
            name = None
            if ctx.guild:
                m = ctx.guild.get_member(uid)
                if m:
                    name = m.display_name
            if not name:
                try:
                    usr = await self.bot.fetch_user(uid)
                    name = usr.name
                except Exception:
                    name = f"User {uid}"
            lines.append(f"{rank}. **{name}** — {count}")

        await ctx.send("\n".join(lines))

    # ----------------- Admin/global reset -----------------
    @commands.command(name="resetstats")
    @commands.has_permissions(administrator=True)  # swap to @commands.is_owner() if you prefer
    async def resetstats_cmd(self, ctx):
        """Reset ALL Brett stats (global + users). Admin only."""
        blank = {
            "global": {"total": 0, "outcomes": {k: 0 for k in BRETT_RESPONSES}},
            "users": {}
        }
        save_stats(blank)
        await ctx.send("🧹 All Brett stats have been reset.")

    # ----------------- Per-user reset -----------------
    @commands.command(name="resetmystats")
    async def reset_my_stats_cmd(self, ctx):
        """Reset only your Brett stats."""
        data = load_stats(BRETT_RESPONSES)
        uid = str(ctx.author.id)
        data.setdefault("users", {})[uid] = {
            "total": 0,
            "outcomes": {k: 0 for k in BRETT_RESPONSES},
            "streak_days": 0
        }
        save_stats(data)
        await ctx.send("🧼 Your Brett stats have been reset.")


async def setup(bot):
    await bot.add_cog(Stats(bot))
