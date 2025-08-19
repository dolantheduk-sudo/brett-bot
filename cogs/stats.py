import io
import json
from discord.ext import commands

from constants import OUTCOMES, BRETT_QUOTES, EMOJI_FOR, MILESTONES
from core.db import load_stats, ensure_user
from core.utils import emoji_bar, big_emoji_bar, pct

HELP_LINES = [
    🎲 Brett Bot Commands,
    Case Sensitive, Jankem Spankem,
    `!brett` — Roll the Brett die,
    `!doublebrett` — Roll twice,
    `!stats` — Your personal roll stats,
    `!allstats` — Global stats & top rollers,
    `!exportstats` — DM you a JSON of your stats,
    `!brettquote` — Brett Quote of the Day,
    `!chart` — Emoji chart of your outcomes,
    `!streak` — Show your daily roll streak,
    `!odds` — Show Brett’s odds,
    `!8brett question` — Magic 8-Ball mode (20 responses, no stats),
    `!resetstats` — (Admin) Reset all stats,
    !brettbattle @user — Battle another user with Brett rolls,
    !leaderboard — Show top rollers in this server,
    !mood [@user] — Reveal a random mood with emoji, optionally add username,
    !chaos — Invoke the Warp,
]

class Stats(commands.Cog)
    def __init__(self, bot commands.Bot)
        self.bot = bot

    @commands.command(name=help)
    async def help_cmd(self, ctx)
        await ctx.send(n.join(HELP_LINES))

    @commands.command(name=stats)
    async def stats_cmd(self, ctx, member=None)
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member)
            member = ctx.author

        stats = load_stats(OUTCOMES)
        u = stats[users].get(str(member.id))
        if not u
            await ctx.send(f{member.display_name} has no Brett stats yet.)
            return

        total = u[total]
        lines = [f📊 {member.display_name} — {total} roll{'s' if total!=1 else ''}]
        for name in OUTCOMES
            c = u[outcomes].get(name, 0)
            lines.append(f- {name} {c} ({pct(c, total)})  {emoji_bar(c, total)})
        if u.get(streak_days, 0)  1
            lines.append(f🔥 Streak {u['streak_days']} day(s))

        # Next milestone (simple)
        next_m = next((m for m in MILESTONES if total  m), None)
        if next_m
            lines.append(f🎯 Next milestone {next_m} rolls (need {next_m - total} more))
        await ctx.send(n.join(lines))

    @commands.command(name=allstats)
    async def allstats_cmd(self, ctx)
        stats = load_stats(OUTCOMES)
        g = stats[global]
        total = g[total]
        lines = [f🌐 Global Brett Stats — {total} total roll{'s' if total!=1 else ''}]
        for name in OUTCOMES
            c = g[outcomes].get(name, 0)
            lines.append(f- {name} {c} ({pct(c, total)}))

        # Top rollers (prefer guild names when available)
        rows = []
        guild_members = {m.id m.display_name for m in ctx.guild.members} if ctx.guild else {}
        for uid_str, u in stats[users].items()
            uid = int(uid_str)
            if guild_members and uid not in guild_members
                continue
            rows.append((u.get(total, 0), guild_members.get(uid, fUser {uid})))
        rows.sort(reverse=True)

        if rows
            top = rows[10]
            lines.append(n🏆 Top Rollers)
            for rank, (count, name) in enumerate(top, start=1)
                lines.append(f{rank}. {name} — {count})
        await ctx.send(n.join(lines))

    @commands.command(name=exportstats)
    async def exportstats_cmd(self, ctx, member=None)
        import io, discord
        member = member or ctx.author
        if not isinstance(member, discord.Member)
            member = ctx.author

        stats = load_stats(OUTCOMES)
        u = stats[users].get(str(member.id))
        if not u
            await ctx.send(fNo stats to export for {member.display_name}.)
            return

        payload = json.dumps(u, indent=2).encode()
        try
            await member.send(
                file=discord.File(fp=io.BytesIO(payload), filename=brett_stats.json)
            )
        except Exception
            await ctx.send(file=discord.File(fp=io.BytesIO(payload), filename=brett_stats.json))
        else
            await ctx.send(📩 Sent to your DMs.)

    @commands.command(name=chart)
    async def chart_cmd(self, ctx, member=None)
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member)
            member = ctx.author
        stats = load_stats(OUTCOMES)
        u = stats[users].get(str(member.id))
        if not u or not u.get(total)
            await ctx.send(f{member.display_name} has no stats yet.)
            return

        total = int(u[total])
        rows = []
        for name in OUTCOMES
            c = int(u[outcomes].get(name, 0))
            rows.append((c, name))
        rows.sort(key=lambda x (-x[0], x[1]))

        lines = [
            f📊 {member.display_name} — {total} total roll{'s' if total != 1 else ''},
            ```
        ]
        for c, name in rows
            emoji = EMOJI_FOR.get(name, 🎲)
            bar = big_emoji_bar(c, total, width=28)
            lines.append(f{emoji} {name18}  {bar}  {c3} ({(100ctotal).1f}%))
        lines.append(```)

        top_count, top_name = rows[0]
        if top_count  0
            lines.append(f⭐ Most rolled {top_name} × {top_count} ({(100top_counttotal).1f}%))
        await ctx.send(n.join(lines))

    @commands.command(name=brettquote)
    async def brettquote_cmd(self, ctx)
        import random
        await ctx.send(f📢 Brett Quote of the Day {random.choice(BRETT_QUOTES)})

    @commands.command(name=streak)
    async def streak_cmd(self, ctx, member=None)
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member)
            member = ctx.author
        stats = load_stats(OUTCOMES)
        u = stats[users].get(str(member.id))
        if not u or u.get(streak_days, 0) == 0
            await ctx.send(f{member.display_name} has no current streak.)
            return
        await ctx.send(f🔥 {member.display_name} streak {u['streak_days']} day(s))

    @commands.command(name=odds)
    async def odds_cmd(self, ctx)
        per = 100  len(OUTCOMES)
        lines = [🎯 Brett Odds (default)]
        for name in OUTCOMES
            lines.append(f- {name} {per.1f}%)
        await ctx.send(n.join(lines))

    @commands.command(name=leaderboard, aliases=[top, lb])
    async def leaderboard_cmd(self, ctx)
        Global top rollers (no members intent required).
        stats = load_stats(OUTCOMES)
        users = stats.get(users, {})
        rows = sorted(
            ((u.get(total, 0), int(uid)) for uid, u in users.items()),
            reverse=True
        )[10]

        if not rows
            await ctx.send(No rolls yet — time to `!brett`!)
            return

        lines = [🏆 Brett Leaderboard (global)]
        for rank, (count, uid) in enumerate(rows, start=1)
            name = None
            if ctx.guild
                m = ctx.guild.get_member(uid)
                if m
                    name = m.display_name
            if not name
                try
                    usr = await self.bot.fetch_user(uid)
                    name = usr.name
                except Exception
                    name = fUser {uid}
            lines.append(f{rank}. {name} — {count})

        await ctx.send(n.join(lines))

async def setup(bot commands.Bot)
    await bot.add_cog(Stats(bot))
def setup(bot commands.Bot)  # sync loader (discord.py  2.x compatibility)
    bot.add_cog(Stats(bot))
