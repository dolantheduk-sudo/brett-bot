import random
import typing
import discord
from discord.ext import commands

# --- constants fallbacks (so the cog still loads if constants.py is missing) ---
try:  # use your real constants if available
    from constants import (
        BRETTISMS, EIGHTBALL, OUTCOMES, BRETT_SCORE,
        INSULTS, COMPLIMENTS, BRETT_MOODS,
    )
except Exception:
    BRETTISMS = [
        "Brett approves.",
        "Brett denies.",
        "Brett is… thinking…",
    ]
    EIGHTBALL = [
        "Yes.", "No.", "Maybe.", "Ask again later.",
    ]
    OUTCOMES = ["Skull", "Bolt", "Star", "Warp"]
    BRETT_SCORE = {"Skull": 1, "Bolt": 2, "Star": 3, "Warp": 0}
    INSULTS = ["buffoon", "goober", "clown"]
    COMPLIMENTS = ["legend", "genius", "rockstar"]
    BRETT_MOODS = [("chill", "🧊"), ("chaotic", "🔥"), ("sleepy", "😴")]


def _safe_member_from_ctx_or_arg(
    ctx: commands.Context,
    user: typing.Optional[discord.Member],
) -> discord.Member:
    """Return a target member or fallback to first mention/author."""
    if isinstance(user, discord.Member):
        return user
    if ctx.message.mentions:
        m = ctx.message.mentions[0]
        if isinstance(m, discord.Member):
            return m
    return ctx.author


class CoreGames(commands.Cog):
    """Fun/random commands for Brett Bot.

    All commands are designed to be resilient: they handle missing args,
    prefer converters for members, and fail gracefully.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- persistence hooks (best-effort; won't crash if utils.db changes) ---
    def record_roll(self, user_id: int, outcome: str) -> None:
        try:
            from utils import db  # type: ignore
        except Exception:
            return
        try:
            if hasattr(db, "record_roll"):
                db.record_roll(user_id, outcome)
            elif hasattr(db, "increment_roll"):
                db.increment_roll(user_id, outcome)
        except Exception:
            # stats are best-effort; never break a game message due to DB
            pass

    # ------------------ Simple randomizers ------------------
    @commands.command(name="brett")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def brett_cmd(self, ctx: commands.Context) -> None:
        """Brett says a thing."""
        msg = random.choice(BRETTISMS)
        await ctx.send(msg)

    @commands.command(name="doublebrett")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def doublebrett_cmd(self, ctx: commands.Context) -> None:
        """Brett says two things."""
        a, b = random.choice(BRETTISMS), random.choice(BRETTISMS)
        await ctx.send(f"{a}\n{b}")

    @commands.command(name="8brett", aliases=["8ball", "brett8"])  # usage: !8brett
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def eight_brett_cmd(self, ctx: commands.Context, *, question: str = "") -> None:
        """Brett answers questions like a magic 8-ball."""
        if not question.strip():
            await ctx.send("Ask a question, e.g. `!8brett Is Brett real?`")
            return
        await ctx.send(random.choice(EIGHTBALL))

    @commands.command(name="coin")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def coin_cmd(self, ctx: commands.Context) -> None:
        """Flip a coin."""
        await ctx.send(random.choice(["Heads", "Tails"]))

    @commands.command(name="choose")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def choose_cmd(self, ctx: commands.Context, *, options: str = "") -> None:
        """Choose among options. Use `|` to separate or provide space-separated words.
        Examples: `!choose pizza | tacos | burgers` or `!choose red blue green`.
        """
        if not options.strip():
            await ctx.send("Give me options, e.g. `!choose pizza | tacos | sushi`")
            return
        if "|" in options:
            parts = [p.strip() for p in options.split("|") if p.strip()]
        else:
            parts = [p for p in options.split() if p]
        if len(parts) < 2:
            await ctx.send("Give me at least two options.")
            return
        await ctx.send(random.choice(parts))

    # ------------------ Social fun ------------------
    @commands.command(name="insult")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def insult_cmd(
        self,
        ctx: commands.Context,
        member: typing.Optional[discord.Member] = None,
    ) -> None:
        """Light-hearted insult. Defaults to the caller if no user given."""
        target = _safe_member_from_ctx_or_arg(ctx, member)
        insult = random.choice(INSULTS)
        await ctx.send(f"{target.mention}, you {insult}.")

    @commands.command(name="compliment")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def compliment_cmd(
        self,
        ctx: commands.Context,
        member: typing.Optional[discord.Member] = None,
    ) -> None:
        """Give someone a compliment. Defaults to caller."""
        target = _safe_member_from_ctx_or_arg(ctx, member)
        comp = random.choice(COMPLIMENTS)
        await ctx.send(f"{target.mention} is a certified {comp} ✨")

    @commands.command(name="mood")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mood_cmd(
        self,
        ctx: commands.Context,
        member: typing.Optional[discord.Member] = None,
    ) -> None:
        """Report someone's mood. `!mood @user` or defaults to caller."""
        target = _safe_member_from_ctx_or_arg(ctx, member)
        label, emoji = random.choice(BRETT_MOODS)
        await ctx.send(f"{emoji} **{target.display_name}** feels *{label}* today.")

    # ------------------ Versus ------------------
    @commands.command(name="brettbattle", aliases=["battle", "duel", "fight"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def brettbattle_cmd(
        self,
        ctx: commands.Context,
        opponent: typing.Optional[discord.Member] = None,
    ) -> None:
        """Battle another user: `!brettbattle @user`. Highest roll wins."""
        opponent = _safe_member_from_ctx_or_arg(ctx, opponent)
        if opponent.id == ctx.author.id:
            await ctx.send("You can’t battle yourself — find a worthy foe.")
            return
        if opponent.bot:
            await ctx.send("Brett refuses to battle bots 😤")
            return

        p1, p2 = ctx.author, opponent
        o1, o2 = random.choice(OUTCOMES), random.choice(OUTCOMES)
        self.record_roll(p1.id, o1)
        self.record_roll(p2.id, o2)
        s1, s2 = BRETT_SCORE.get(o1, 0), BRETT_SCORE.get(o2, 0)

        if s1 == s2:
            verdict = "🤝 It’s a tie. The Warp is fickle."
        elif s1 > s2:
            verdict = f"🏆 **{p1.display_name}** wins!"
        else:
            verdict = f"🏆 **{p2.display_name}** wins!"

        await ctx.send(
            "\n".join([
                "⚔️ **Brett Battle!**",
                f"{p1.mention} rolled **{o1}** vs {p2.mention} rolled **{o2}**",
                verdict,
            ])
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoreGames(bot))
