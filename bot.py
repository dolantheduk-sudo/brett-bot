import os
import json
import random
import datetime as dt
import discord
from discord.ext import commands

# ---------- Config ----------
STATS_FILE = os.getenv("STATS_FILE", "stats.json")   # on Render w/ disk, set STATS_FILE=/data/stats.json
OUTCOMES = [
    "Nah",
    "You Betcha",
    "Maybe Later",
    "Could Be",
    "Don't Bet on It",
    "Chances Are Good",
]
EIGHT_BALL_OUTCOMES = [
    "It is certain", "It is decidedly so", "Without a doubt", "Yes – definitely",
    "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
    "Yes", "Signs point to yes",
    "Reply hazy, try again", "Ask again later", "Better not tell you now",
    "Cannot predict now", "Concentrate and ask again",
    "Don't count on it", "My reply is no", "My sources say no",
    "Outlook not so good", "Very doubtful"
]
BRETT_QUOTES = [
    "Brett once rolled Double Brett and took the rest of the day off.",
    "You betcha… unless Brett says nah.",
    "Chances are good. Odds are better.",
    "Don’t bet on it — but do roll again.",
    "Maybe later is Brett’s favorite time of day.",
    "Could be… could also not be.",
    "HORSE!",
    "Jankem Spankem, vindaloo",
    "Bepton Sinclair was here",
    "Jared fucked us over with Sea of Thieves, Ben",
    "TURNS!",
    "mmkay",
    "Are you getting this down Austin?",
    "Faggots Beware and the sequel are unrivaled classics",
    "Callie's a bitch shomtimes, shomtimes, shomtimes...",
    "plug it up plug it up, urethra hole",
    "Besner went to law school",
    "Is Baldur's Gate 3 really the best game ever made Jared?",
    "Makoto Niijima #1",
    "Dan please fucking watch Frieren: Beyond Journey's End I beg of you for the love of god",
    "EAT SLEEP SHIT EVERYTHING BRICK SQUAD",
    "Don't give up the ship! - Commodore Oliver Hazard Perry, June 1st 1813"
]

EMOJI_FOR = {
    "Nah": "❌",
    "You Betcha": "✅",
    "Maybe Later": "⏳",
    "Could Be": "🤔",
    "Don't Bet on It": "🚫",
    "Chances Are Good": "🍀",
}

def big_emoji_bar(count: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "—"
    if count <= 0:
        return "░" * width
    filled = max(1, int(round((count / total) * width)))
    return "█" * filled + "░" * (width - filled)

MILESTONES = [10, 25, 50, 100, 250, 500, 1000]  # announce on hit

# ---------- Intents & Bot ----------
intents = discord.Intents.default()
intents.message_content = True  # required for prefix (!) commands

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    case_insensitive=True,
    help_command=None,  # we'll provide a custom !help
)

# ---------- Storage ----------
def _blank_user():
    return {
        "total": 0,
        "outcomes": {k: 0 for k in OUTCOMES},
        "last_roll_date": None,   # "YYYY-MM-DD"
        "streak_days": 0,         # consecutive days with at least one roll
    }

def _blank_stats():
    return {
        "global": {"total": 0, "outcomes": {k: 0 for k in OUTCOMES}},
        "users": {}  # str(user_id) -> user dict
    }

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return _blank_stats()

def save_stats(stats):
    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, STATS_FILE)

def today_str(tz=None):
    # Render dynos are UTC; this keeps it simple
    return dt.date.today().isoformat()

def emoji_bar(count, total, width=20):
    if total <= 0:
        return "—"
    filled = int(round((count / total) * width))
    return "■" * max(1, filled) + "□" * max(0, width - max(1, filled))

def pct(n, d):
    return f"{(100*n/d):.1f}%" if d else "0.0%"

# ---------- Core Roll + bookkeeping ----------
def record_roll(user_id: int, outcome: str):
    stats = load_stats()
    uid = str(user_id)
    if uid not in stats["users"]:
        stats["users"][uid] = _blank_user()
    u = stats["users"][uid]

    # Global
    stats["global"]["total"] += 1
    stats["global"]["outcomes"][outcome] += 1

    # User totals
    u["total"] += 1
    u["outcomes"][outcome] += 1

    # Streak tracking: count days with at least one roll per day
    today = today_str()
    last = u["last_roll_date"]
    if last is None:
        u["streak_days"] = 1
    else:
        try:
            d_last = dt.date.fromisoformat(last)
            d_today = dt.date.fromisoformat(today)
            if (d_today - d_last).days == 1:
                u["streak_days"] += 1
            elif (d_today - d_last).days == 0:
                # same day: keep streak as-is (only first roll per day extends)
                pass
            else:
                u["streak_days"] = 1
        except Exception:
            u["streak_days"] = 1
    u["last_roll_date"] = today

    save_stats(stats)
    return stats, u

def next_milestone(total: int):
    for m in MILESTONES:
        if total < m:
            return m
    return None

# ---------- Events ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    print("Brett Bot is ready. Type !help")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("I didn’t recognize that. Try `!help`.")
    else:
        raise error

# ---------- Commands ----------
@bot.command(name="help")
async def help_cmd(ctx):
    lines = [
        "🎲 **Brett Bot Commands**",
        "*Case Sensitive, Jankem Spankem*",
        "`!brett` — Roll the Brett die",
        "`!doublebrett` — Roll twice",
        "`!stats` — Your personal roll stats",
        "`!allstats` — Global stats & top rollers",
        "`!exportstats` — DM you a JSON of your stats",
        "`!brettquote` — Brett Quote of the Day",
        "`!chart` — Emoji chart of your outcomes",
        "`!streak` — Show your daily roll streak",
        "`!odds` — Show Brett’s odds",
        "`!8brett <question>` — Magic 8-Ball mode (20 responses, no stats)",
        "`!resetstats` — (Admin) Reset all stats",
    ]
    await ctx.send("\n".join(lines))

@bot.command(name="brett")
async def brett_cmd(ctx):
    outcome = random.choice(OUTCOMES)
    stats, u = record_roll(ctx.author.id, outcome)

    msg = f"🎲 {ctx.author.mention} Brett says: **{outcome}**"
    # Milestone ping
    if u["total"] in MILESTONES:
        msg += f"\n🎉 Congrats! You’ve hit **{u['total']}** total rolls!"
    await ctx.send(msg)

@bot.command(name="doublebrett")
async def doublebrett_cmd(ctx):
    out1 = random.choice(OUTCOMES)
    out2 = random.choice(OUTCOMES)
    record_roll(ctx.author.id, out1)
    stats, u = record_roll(ctx.author.id, out2)
    msg = f"🎲 **Double Brett!** {ctx.author.mention} → **{out1}** | **{out2}**"
    if u["total"] in MILESTONES:
        msg += f"\n🎉 Milestone reached: **{u['total']}** rolls!"
    await ctx.send(msg)

@bot.command(name="stats")
async def stats_cmd(ctx, member: discord.Member | None = None):
    member = member or ctx.author
    stats = load_stats()
    u = stats["users"].get(str(member.id))
    if not u:
        await ctx.send(f"{member.display_name} has no Brett stats yet.")
        return

    total = u["total"]
    lines = [f"📊 **{member.display_name}** — {total} roll{'s' if total!=1 else ''}"]
    for name in OUTCOMES:
        c = u["outcomes"].get(name, 0)
        lines.append(f"- {name}: **{c}** ({pct(c, total)})  {emoji_bar(c, total)}")
    # Streak info
    if u.get("streak_days", 0) > 1:
        lines.append(f"🔥 Streak: **{u['streak_days']}** day(s)")
    # Next milestone
    nm = next_milestone(total)
    if nm:
        lines.append(f"🎯 Next milestone: **{nm}** rolls (need {nm-total} more)")
    await ctx.send("\n".join(lines))

@bot.command(name="allstats")
async def allstats_cmd(ctx):
    stats = load_stats()
    g = stats["global"]
    total = g["total"]
    lines = [f"🌐 **Global Brett Stats** — {total} total roll{'s' if total!=1 else ''}"]
    for name in OUTCOMES:
        c = g["outcomes"].get(name, 0)
        lines.append(f"- {name}: **{c}** ({pct(c, total)})")

    # Top rollers (this server only if possible)
    # Build list of (count, name) for members present in this guild
    rows = []
    guild_members = {m.id: m.display_name for m in ctx.guild.members} if ctx.guild else {}
    for uid_str, u in stats["users"].items():
        uid = int(uid_str)
        if guild_members and uid not in guild_members:
            continue
        rows.append((u.get("total", 0), guild_members.get(uid, f"User {uid}")))
    rows.sort(reverse=True)
    if rows:
        top = rows[:10]
        lines.append("\n🏆 **Top Rollers**")
        for rank, (count, name) in enumerate(top, start=1):
            lines.append(f"{rank}. **{name}** — {count}")
    await ctx.send("\n".join(lines))

@bot.command(name="exportstats")
async def exportstats_cmd(ctx, member: discord.Member | None = None):
    member = member or ctx.author
    stats = load_stats()
    u = stats["users"].get(str(member.id))
    if not u:
        await ctx.send(f"No stats to export for {member.display_name}.")
        return
    payload = json.dumps(u, indent=2).encode()
    try:
        await member.send(
            file=discord.File(fp=discord.File(io.BytesIO(payload), filename="brett_stats.json"))
        )
    except Exception:
        # Fallback: send to channel as a file
        await ctx.send(file=discord.File(fp=io.BytesIO(payload), filename="brett_stats.json"))
    else:
        await ctx.send("📩 Sent to your DMs.")

# simpler in-channel version that doesn't depend on matplotlib

@bot.command(name="chart")
async def chart_cmd(ctx, member: discord.Member | None = None):
    """Large emoji bar chart of outcome distribution."""
    member = member or ctx.author
    stats = load_stats()
    u = stats["users"].get(str(member.id))
    if not u or not u.get("total"):
        await ctx.send(f"{member.display_name} has no stats yet.")
        return

    total = int(u["total"])

    # Build rows: (count, name), sorted by count desc then name
    rows = []
    for name in OUTCOMES:
        c = int(u["outcomes"].get(name, 0))
        rows.append((c, name))
    rows.sort(key=lambda x: (-x[0], x[1]))

    # Pretty, wide chart in a code block
    lines = [
        f"📊 **{member.display_name}** — {total} total roll{'s' if total != 1 else ''}",
        "```"
    ]
    for c, name in rows:
        emoji = EMOJI_FOR.get(name, "🎲")
        bar = big_emoji_bar(c, total, width=28)
        # Align name column to be neat
        lines.append(f"{emoji} {name:<18} | {bar}  {c:>3} ({(100*c/total):.1f}%)")
    lines.append("```")

    # Call out the #1 outcome
    top_count, top_name = rows[0]
    if top_count > 0:
        lines.append(f"⭐ Most rolled: **{top_name}** × {top_count} ({(100*top_count/total):.1f}%)")

    await ctx.send("\n".join(lines))


@bot.command(name="brettquote")
async def brettquote_cmd(ctx):
    await ctx.send(f"📢 **Brett Quote of the Day:** {random.choice(BRETT_QUOTES)}")

@bot.command(name="streak")
async def streak_cmd(ctx, member: discord.Member | None = None):
    member = member or ctx.author
    stats = load_stats()
    u = stats["users"].get(str(member.id))
    if not u or u.get("streak_days", 0) == 0:
        await ctx.send(f"{member.display_name} has no current streak.")
        return
    await ctx.send(f"🔥 {member.display_name} streak: **{u['streak_days']}** day(s)")

@bot.command(name="odds")
async def odds_cmd(ctx):
    # Equal odds by default (1/6 each). If you add weights later, adjust here.
    per = 100 / len(OUTCOMES)
    lines = ["🎯 **Brett Odds (default)**"]
    for name in OUTCOMES:
        lines.append(f"- {name}: {per:.1f}%")
    await ctx.send("\n".join(lines))

@bot.command(name="8brett", aliases=["brett8", "8ball", "8b"])
async def eight_brett_cmd(ctx, *, question: str = ""):
    response = random.choice(EIGHT_BALL_OUTCOMES)
    if question.strip():
        await ctx.send(f"❓ {ctx.author.mention} asked: *{question.strip()}*\n🎱 Magic 8-Brett says: **{response}**")
    else:
        await ctx.send(f"🎱 Magic 8-Brett says: **{response}**")

@bot.command(name="resetstats")
@commands.has_permissions(manage_guild=True)
async def resetstats_cmd(ctx):
    save_stats(_blank_stats())
    await ctx.send("🧹 All Brett stats reset.")

@resetstats_cmd.error
async def resetstats_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Manage Server** to use this.")
    else:
        raise error

# ---------- Run ----------
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not TOKEN:
        raise SystemExit("Set DISCORD_BOT_TOKEN in the environment.")
    bot.run(TOKEN)
