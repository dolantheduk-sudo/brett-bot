import os
import discord
from discord.ext import commands

# Optional: load .env locally; on Render it's harmless (no .env present)
try:
    from dotenv import load_dotenv  # pip install python-dotenv (optional)
    load_dotenv()
except Exception:
    pass

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
    for ext in ("cogs.stats", "cogs.core_games"):
        try:
            bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"[EXT LOAD ERROR] {ext}: {e}")

if __name__ == "__main__":
    load_extensions()
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN in the environment.")
    bot.run(token)
