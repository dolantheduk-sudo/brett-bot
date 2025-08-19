import os
import discord
from discord.ext import commands

import config

INTENTS = discord.Intents.default()
INTENTS.message_content = True  # required for prefix commands

def make_bot() -> commands.Bot:
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("!"),
        intents=INTENTS,
        case_insensitive=True,
        help_command=None,  # custom help in stats cog
    )
    return bot

bot = make_bot()

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

def load_extensions():
    bot.load_extension("cogs.stats")
    bot.load_extension("cogs.core_games")

if __name__ == "__main__":
    load_extensions()
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN in the environment.")
    bot.run(token)
