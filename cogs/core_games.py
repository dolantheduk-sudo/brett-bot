import random
import typing
import time
import discord
from discord.ext import commands


# ---------- helpers ----------
def _target_member(ctx: commands.Context,
                   member_opt: typing.Optional[discord.Member]) -> discord.Member:
    """Prefer converter arg, else first mention, else author."""
    if isinstance(member_opt, discord.Member):
        return member_opt
    if ctx.message.mentions:
        m = ctx.message.mentions[0]
        if isinstance(m, discord.Member):
            return m
    return ctx.author


def _record_roll_safe(gid: int, uid: int, outcome: str) -> None:
    """Try new storage signature, then legacy; never crash commands."""
    try:
        from utils import storage as _storage  # lazy import
    except Exception:
        return
    ts = int(time.time())
    try:
        # Preferred: record_roll(gid, uid, outcome, ts)
        _storage.record_roll(gid, uid, outcome, ts)  # type: ignore[attr-defined]
        return
    except TypeError:
        pass
    except Exception:
        pass
    try:
        # Legacy: record_roll(uid, outcome)
        _storage.record_roll(uid, outcome)  # type: ignore[misc]
    except Exception:
        pass


class CoreGames(commands.Cog):
    """Fun/random commands for Brett Bot (discord.py 2.x)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- simple randomizers ----------
    @commands.command(name="brett")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def brett_cmd(self, ctx: commands.Context) -> None:
        """Classic Brett response (six outcomes) + hidden roll recorded for stats."""
        try:
            from constants import BRETT_RESPONSES, OUTCOMES
        except Exception:
            BRETT_RESPONSES = [
                "You betcha.", "Nah.", "Maybe later.",
                "Could be.", "Chances are good.", "Don’t bet on it.",
            ]
            OUTCOMES = ["Skull", "Bolt", "Star", "Warp"]

        # record an outcome for stats (invisible to users)
        _record_roll_safe(ctx.guild.id, ctx.author.id, random.choice(OUTCOMES))

        # show classic line
        await ctx.send(random.choice(BRETT_RESPONSES))

    @commands.command(name="doublebrett")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def doublebrett_cmd(self, ctx: commands.Context) -> None:
        try:
            from constants import BRETT_RESPONSES, OUTCOMES
        except Exception:
            BRETT_RESPONSES = [
                "You betcha.", "Nah.", "Maybe later.",
                "Could be.", "Chances are good.", "Don’t bet on it.",
            ]
            OUTCOMES = ["Skull", "Bolt", "Star", "Warp"]

        _record_roll_safe(ctx.guild.id, ctx.author.id, random.choice(OUTCOMES))
        _record_roll_safe(ctx.guild.id, ctx.author.id, random.choice(OUTCOMES))

        a, b = random.choice(BRETT_RESPONSES), random.choice(BRETT_RESPONSES)
        await ctx.send(f"{a}\n{b}")

    @commands.command(name="8brett", aliases=("8ball", "brett8"))
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def eight_brett_cmd(self, ctx: commands.Context, *, question: str = "") -> None:
        """Magic 8-ball style answer (no stats). Usage: !8brett <question>"""
        try:
            from constants import EIGHTBALL
        except Exception:
            EIGHTBALL = ["Yes.", "No.", "Maybe.", "Ask again later."]
        if not question.strip():
            await ctx.send("Ask a question, e.g. `!8brett Is Brett real?`")
            return
        await ctx.send(random.choice(EIGHTBALL))

    @commands.command(name="coin")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def coin_cmd(self, ctx: commands.Context) -> None:
        await ctx.send(random.choice(["Heads", "Tails"]))

    @commands.command(name="choose")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def choose_cmd(self, ctx: commands.Context, *, options: str = "") -> None:
        s = options.strip()
        if not s:
            await ctx.send("Give me options, e.g. `!choose pizza | tacos | sushi`")
            return
        parts = [p.strip() for p in (s.split("|") if "|" in s else s.split()) if p.strip()]
        if len(parts) < 2:
            await ctx.send("Give me at least two options.")
            return
        await ctx.send(random.choice(parts))

    # ---------- social fun ----------
    @commands.command(name="insult")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def insult_cmd(self, ctx: commands.Context,
                         member: typing.Optional[discord.Member] = None) -> None:
        try:
            from constants import INSULTS
        except Exception:
            INSULTS = ["dumbass", "dipshit", "clown", "goober", "piece of shit", "retard", "cumstain", "dick", "asshat"]
        target = _target_member(ctx, member)
        await ctx.send(f"{target.mention}, you {random.choice(INSULTS)}.")

    @commands.command(name="compliment")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def compliment_cmd(self, ctx: commands.Context,
                             member: typing.Optional[discord.Member] = None) -> None:
        try:
            from constants import COMPLIMENTS
        except Exception:
            COMPLIMENTS = ["fucking legend", "genius", "rockstar", "smart guy", "winner", "Bepi", "King", "real fuckin deal", "Man who Fucks"]
        target = _target_member(ctx, member)
        await ctx.send(f"{target.mention} is a certified {random.choice(COMPLIMENTS)} ✨")

    @commands.command(name="mood")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mood_cmd(self, ctx: commands.Context,
                       member: typing.Optional[discord.Member] = None) -> None:
        try:
            from constants import BRETT_MOODS
        except Exception:
            BRETT_MOODS = [
                ("Chill", "🧊"),
                ("Chaotic", "🌀"),
                ("Sleepy", "😴"),
                ("Hyped AF", "⚡"),
                ("Salty", "🧂"),
                ("Mad as fuck actually", "😡"),
                ("Goofy", "🤪"),
                ("Zen", "🪷"),
                ("Fucking Spooky", "👻"),
                ("Lucky", "🍀"),
                ("Edgy", "🗡️"),
                ("Sussy", "🕵️"),
                ("Fucking Cringe", "🙈"),
                ("Fucking Based", "🪙"),
                ("Dank", "💨"),
]
        target = _target_member(ctx, member)
        label, emoji = random.choice(BRETT_MOODS)
        await ctx.send(f"{emoji} **{target.display_name}** feels *{label}* today.")

    # ---------- versus ----------
    @commands.command(name="brettbattle", aliases=("battle", "duel", "fight"))
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def brettbattle_cmd(self, ctx: commands.Context,
                              opponent: typing.Optional[discord.Member] = None) -> None:
        try:
            from constants import OUTCOMES, BRETT_SCORE
        except Exception:
            OUTCOMES = ["Skull", "Bolt", "Star", "Warp"]
            BRETT_SCORE = {"Skull": 1, "Bolt": 2, "Star": 3, "Warp": 0}

        opponent = _target_member(ctx, opponent)
        if opponent.id == ctx.author.id:
            await ctx.send("You can’t battle yourself retard — find a worthy foe.")
            return
        if opponent.bot:
            await ctx.send("Brett refuses to battle mindless bots 😤")
            return

        p1, p2 = ctx.author, opponent
        o1, o2 = random.choice(OUTCOMES), random.choice(OUTCOMES)
        _record_roll_safe(ctx.guild.id, p1.id, o1)
        _record_roll_safe(ctx.guild.id, p2.id, o2)
        s1, s2 = BRETT_SCORE.get(o1, 0), BRETT_SCORE.get(o2, 0)

        verdict = "🤝 It’s a tie. Shit's fucked."
        if s1 > s2:
            verdict = f"🏆 **{p1.display_name}** wins!"
        elif s2 > s1:
            verdict = f"🏆 **{p2.display_name}** wins!"

        await ctx.send(
            "\n".join([
                "⚔️ **Brett Battle!**",
                f"{p1.mention} rolled **{o1}** vs {p2.mention} rolled **{o2}**",
                verdict,
            ])
        )

    # ---------- chaos ----------
    @commands.command(name="chaos")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def chaos_cmd(self, ctx: commands.Context) -> None:
        """Invoke the Warp (random Chaos outcome)."""
        try:
            from constants import CHAOS_OUTCOMES_40K
        except Exception:
            CHAOS_OUTCOMES_40K = ["The Warp is silent... or maybe not wired up?"]
        await ctx.send(f"🔮 CHAOS BRETT decrees: **{random.choice(CHAOS_OUTCOMES_40K)}**")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoreGames(bot))
