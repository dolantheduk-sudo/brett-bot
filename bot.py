# --- at top with imports ---
import os, asyncio, traceback
import discord
from discord.ext import commands

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.presences = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   intents=INTENTS, case_insensitive=True,
                   help_command=None)

@bot.command()
async def ping(ctx):  # sanity check that bot base is alive
    await ctx.send("pong")

async def load_extensions():
    for ext in ("cogs.stats", "cogs.core_games", "cogs.help", "cogs.brettventures"):
        try:
            await bot.load_extension(ext)
            print(f"[EXT OK] {ext}")
        except Exception as e:
            print(f"[EXT LOAD ERROR] {ext}: {e}")
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    # Show how many prefix commands actually registered
    print("[COMMANDS]", sorted([c.name for c in bot.commands]))
    print("Type !ping")

@bot.event
async def on_command_error(ctx, error):
    # avoid double-handling CommandNotFound if you prefer
    if isinstance(error, commands.CommandNotFound):
        return
    traceback.print_exception(type(error), error, error.__traceback__)

async def main():
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN in the environment.")
    async with bot:
        await load_extensions()         # <--- MAKE SURE THIS LINE EXISTS
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
