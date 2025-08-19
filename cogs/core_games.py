import random
from discord.ext import commands
from constants import OUTCOMES, BRETT_SCORE, BRETT_MOODS, CHAOS_OUTCOMES_40K, MILESTONES
from utils.db import load_stats, save_stats, ensure_user
from utils.helpers import today_str

class CoreGames(commands.Cog):
    def __init__(self, bot): self.bot = bot

    def record_roll(self, user_id: int, outcome: str):
        stats = load_stats(OUTCOMES)
        u = ensure_user(stats, user_id, OUTCOMES)

        stats["global"]["total"] += 1
        stats["global"]["outcomes"][outcome] += 1
        u["total"] += 1
        u["outcomes"][outcome] += 1

        today = today_str()
        last = u.get("last_roll_date")
        if last is None:
            u["streak_days"] = 1
        else:
            import datetime as dt
            try:
                d_last = dt.date.fromisoformat(last)
                d_today = dt.date.fromisoformat(today)
                delta = (d_today - d_last).days
                if delta == 1:
                    u["streak_days"] += 1
                elif delta != 0:
                    u["streak_days"] = 1
            except Exception:
                u["streak_days"] = 1
        u["last_roll_date"] = today

        save_stats(stats)
        return stats, u

    @commands.command(name="brett")
    async def brett_cmd(self, ctx):
        outcome = random.choice(OUTCOMES)
        _, u = self.record_roll(ctx.author.id, outcome)
        msg = f"🎲 {ctx.author.mention} Brett says: **{outcome}**"
        if u["total"] in MILESTONES:
            msg += f"\n🎉 Congrats! You’ve hit **{u['total']}** total rolls!"
        await ctx.send(msg)

    @commands.command(name="doublebrett")
    async def doublebrett_cmd(self, ctx):
        out1 = random.choice(OUTCOMES)
        out2 = random.choice(OUTCOMES)
        self.record_roll(ctx.author.id, out1)
        _, u = self.record_roll(ctx.author.id, out2)
        msg = f"🎲 **Double Brett!** {ctx.author.mention} → **{out1}** | **{out2}**"
        if u["total"] in MILESTONES:
            msg += f"\n🎉 Milestone reached: **{u['total']}** rolls!"
        await ctx.send(msg)

    @commands.command(name="8brett", aliases=["brett8","8ball","8b"])
    async def eight_brett_cmd(self, ctx, *, question: str = ""):
        from constants import EIGHT_BALL_OUTCOMES
        response = random.choice(EIGHT_BALL_OUTCOMES)
        if question.strip():
            await ctx.send(f"❓ {ctx.author.mention} asked: *{question.strip()}*\n🎱 Magic 8-Brett says: **{response}**")
        else:
            await ctx.send(f"🎱 Magic 8-Brett says: **{response}**")

    @commands.command(name="mood")
    async def mood_cmd(self, ctx, member=None):
        import discord
        member = member or ctx.author
        if not isinstance(member, discord.Member): member = ctx.author
        label, emoji = random.choice(BRETT_MOODS)
        await ctx.send(f"{emoji} **{member.display_name}** feels *{label}*.")

    @commands.command(name="chaos", aliases=["wh40k","warp"])
    async def chaos_cmd(self, ctx):
        msg = random.choice(CHAOS_OUTCOMES_40K)
        await ctx.send(f"🌀 **CHAOS**: {msg}")

    @commands.command(name="brettbattle", aliases=["battle","duel"])
    async def brettbattle_cmd(self, ctx, opponent):
        import discord
        if not isinstance(opponent, discord.Member):
            await ctx.send("Tag someone to battle, e.g. `!brettbattle @user`.")
            return
        if opponent.bot:
            await ctx.send("Brett refuses to battle bots 😤")
            return
        p1 = ctx.author; p2 = opponent
        o1 = random.choice(OUTCOMES); o2 = random.choice(OUTCOMES)
        self.record_roll(p1.id, o1); self.record_roll(p2.id, o2)
        s1 = BRETT_SCORE.get(o1, 0); s2 = BRETT_SCORE.get(o2, 0)
        verdict = "🤝 It’s a tie. The Warp is fickle."
        if s1 > s2: verdict = f"🏆 **{p1.display_name}** wins!"
        if s2 > s1: verdict = f"🏆 **{p2.display_name}** wins!"
        await ctx.send(
            f"⚔️ **Brett Battle!**\n"
            f"{p1.mention} rolled **{o1}** vs {p2.mention} rolled **{o2}**\n{verdict}"
        )

    @commands.command(name="resetstats")
    @commands.has_permissions(administrator=True)
    async def resetstats_cmd(self, ctx):
        from utils.db import save_stats, _blank_stats
        save_stats(_blank_stats(OUTCOMES))
        await ctx.send("🔄 All stats have been reset.")

    @resetstats_cmd.error
    async def resetstats_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need **Manage Server** to use this.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(CoreGames(bot))

