import os
import json
import random
import discord
from discord.ext import commands

# ---- Intents (must keep these!) ----
intents = discord.Intents.all()
intents.message_content = True
print("[DEBUG] message_content:", intents.message_content)

bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Stats ----
STATS_FILE = "stats.json"
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
else:
    stats = {"rolls": {}, "total": 0}

OUTCOMES = [
    "Nah",
    "You Betcha",
    "Maybe Later",
    "Could Be",
    "Don't Bet on It",
    "Chances Are Good",
]

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

@bot.event
async def on_ready():
    print(f"[DEBUG] Logged in as {bot.user} (id={bot.user.id})")

@bot.command()
async def brett(ctx):
    outcome = random.choice(OUTCOMES)
    user = str(ctx.author.id)
    stats["total"] += 1
    stats["rolls"].setdefault(user, {"count": 0})
    stats["rolls"][user]["count"] += 1
    save_stats()
    await ctx.send(f"{ctx.author.mention} Brett says: **{outcome}**")

@bot.command(name="stats")
async def stats_cmd(ctx):
    user = str(ctx.author.id)
    if user in stats["rolls"]:
        count = stats["rolls"][user]["count"]
        await ctx.send(f"{ctx.author.mention}, you have rolled Brett {count} times.")
    else:
        await ctx.send(f"{ctx.author.mention}, you haven't rolled Brett yet.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)

