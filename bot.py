import discord
from discord.ext import commands
import random
import json
import os

# Load or initialize stats
STATS_FILE = "stats.json"
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
else:
    stats = {"rolls": {}, "total": 0}

# Outcomes
OUTCOMES = [
    "Nah",
    "You Betcha",
    "Maybe Later",
    "Could Be",
    "Don't Bet on It",
    "Chances Are Good"
]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def brett(ctx):
    outcome = random.choice(OUTCOMES)
    user = str(ctx.author.id)
    stats["total"] += 1
    stats["rolls"].setdefault(user, {"count": 0})
    stats["rolls"][user]["count"] += 1
    save_stats()
    await ctx.send(f"{ctx.author.mention} Brett says: **{outcome}**")

@bot.command()
async def stats(ctx):
    user = str(ctx.author.id)
    if user in stats["rolls"]:
        count = stats["rolls"][user]["count"]
        await ctx.send(f"{ctx.author.mention}, you have rolled Brett {count} times.")
    else:
        await ctx.send(f"{ctx.author.mention}, you haven't rolled Brett yet.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
