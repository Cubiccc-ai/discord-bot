# bot.py (cleaned - commands moved to cogs)
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents, help_command=None)

# --- safe GUILD_ID parsing + diagnostics ---
guild_id_raw = os.getenv("GUILD_ID")
if guild_id_raw:
    try:
        GUILD_ID = int(guild_id_raw)
    except ValueError:
        print(f"❌ GUILD_ID must be numeric. Got: {guild_id_raw!r}")
        GUILD_ID = None
else:
    print("⚠️ GUILD_ID not set. Guild-specific sync will be skipped.")
    GUILD_ID = None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (id={getattr(bot.user,'id',None)})")

    # list prefix commands (names)
    try:
        print("Prefix commands registered:", [c.name for c in bot.commands])
    except Exception as e:
        print("Error listing prefix commands:", e)

    # list app (slash) commands in the tree (local)
    try:
        print("App commands in tree (local):", [c.name for c in bot.tree.walk_commands()])
    except Exception as e:
        print("Error listing app commands:", e)

    # show guilds the bot is in
    try:
        print("Guilds the bot is in:")
        for g in bot.guilds:
            print(f" - {g.name} (id={g.id})")
    except Exception as e:
        print("Error enumerating guilds:", e)

    # sync commands (fast guild sync if GUILD_ID provided)
    try:
        if GUILD_ID:
            guild_obj = discord.Object(id=GUILD_ID)
            synced = await bot.tree.sync(guild=guild_obj)
            print(f"✅ Synced {len(synced)} slash command(s) to guild {GUILD_ID}.")
        else:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} slash command(s) globally.")
    except Exception as e:
        print("❌ Sync error:", repr(e))


# -------------------- ERROR HANDLERS --------------------
@bot.event
async def on_command_error(ctx, error):
    print("Prefix command error:", repr(error))
    try:
        await ctx.send(f"Error: {error}")
    except Exception:
        pass

@bot.tree.error
async def on_app_command_error(interaction, error):
    print("App command error:", repr(error))
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("Command error occurred.", ephemeral=True)
        else:
            await interaction.followup.send("Command error occurred.", ephemeral=True)
    except Exception as e:
        print("Failed to notify user about app command error:", e)


# -------------------- KEEP RENDER ALIVE --------------------
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()


# -------------------- LOAD COGS & RUN --------------------
async def main():
    # load all cogs from the cogs/ folder
    for filename in os.listdir("cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: cogs.{filename[:-3]}")
            except Exception as e:
                print(f"❌ Failed to load cogs.{filename[:-3]}:", e)

    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables.")
        raise SystemExit(1)

    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
