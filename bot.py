import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # Global sync
        print(f"✅ Synced {len(synced)} slash command(s) globally.")
    except Exception as e:
        print(f"❌ Failed to sync global slash commands: {e}")

# -------------------- PING --------------------

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.tree.command(name="ping", description="Check if the bot is online (slash version)")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=False)

# -------------------- KICK --------------------

@bot.hybrid_command(description="Kick a member from the server.")
@commands.has_permissions(kick_members=True)
@app_commands.describe(member="The member to kick", reason="Reason for the kick")
async def kick(ctx: commands.Context, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.send(f"👢 You were kicked from **{ctx.guild.name}**.\n**Reason:** {reason}")
    except discord.Forbidden:
        await ctx.send("⚠️ Couldn't DM the user (they probably have DMs off).", ephemeral=True)
    except discord.HTTPException:
        pass

    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention} | Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick that user.")
    except discord.HTTPException:
        await ctx.send("⚠️ Kick failed due to a network error.")

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-kick @user [reason]`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# -------------------- BAN --------------------

@bot.hybrid_command(description="Ban a member from the server.")
@commands.has_permissions(ban_members=True)
@app_commands.describe(user="The member to ban", reason="Reason for the ban")
async def ban(ctx: commands.Context, user: str, *, reason: str = "No reason provided"):
    # Try resolving as Member first
    member = None
    try:
        member = await commands.MemberConverter().convert(ctx, user)
    except commands.BadArgument:
        # Try to fetch by user ID
        try:
            user_obj = await bot.fetch_user(int(user))
            await ctx.guild.ban(user_obj, reason=reason)
            await ctx.send(f"🔨 Banned `{user_obj}` | Reason: {reason}")
            return
        except Exception as e:
            await ctx.send(f"❌ Couldn't find user with ID `{user}`. Error: {e}")
            return

    # Try to DM
    try:
        await member.send(f"🔨 You were banned from **{ctx.guild.name}**.\n**Reason:** {reason}")
    except:
        pass

    # Attempt to ban
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention} | Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I can't ban that user.")
    except discord.HTTPException:
        await ctx.send("⚠️ Ban failed due to a network error.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-ban @user [reason]`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# -------------------- UNBAN --------------------

@bot.hybrid_command(description="Unban a member by name#1234 or ID.")
@commands.has_permissions(ban_members=True)
@app_commands.describe(user_input="Name#1234 or user ID of the banned user")
async def unban(ctx: commands.Context, *, user_input: str):
    banned_users = [entry async for entry in ctx.guild.bans()]

    user_id = None
    member_name = None
    discriminator = None

    if user_input.isdigit():
        user_id = int(user_input)
    elif "#" in user_input:
        member_name, discriminator = user_input.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user
        if (
            (user_id and user.id == user_id) or
            (member_name and discriminator and user.name == member_name and user.discriminator == discriminator)
        ):
            try:
                await user.send(f"✅ You have been unbanned from **{ctx.guild.name}**.")
            except:
                await ctx.send(f"⚠️ Couldn't DM {user}.", ephemeral=True)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user.mention}")
            return

    await ctx.send("⚠️ User not found in the ban list.")

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-unban name#1234 or ID`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# -------------------- MUTE --------------------

@bot.hybrid_command(description="Mute a user, optionally for a duration (seconds).")
@commands.has_permissions(manage_roles=True)
@app_commands.describe(member="The member to mute", duration="Duration in seconds", reason="Reason for muting")
async def mute(ctx: commands.Context, member: discord.Member, duration: int = None, *, reason: str = "No reason provided"):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not muted_role:
        await ctx.send("❌ 'Muted' role not found. Please create one with no Send Messages/Speak permissions.")
        return

    await member.add_roles(muted_role, reason=reason)

    try:
        await member.send(f"🔇 You have been muted in **{ctx.guild.name}**.\nReason: `{reason}`")
    except:
        await ctx.send("⚠️ Couldn't DM the muted user.", ephemeral=True)

    await ctx.send(f"🔇 Muted {member.mention} | Reason: `{reason}`")

    if duration:
        await asyncio.sleep(duration)
        await member.remove_roles(muted_role)
        try:
            await member.send(f"🔊 You have been unmuted in **{ctx.guild.name}**.")
        except:
            pass
        await ctx.send(f"🔊 Automatically unmuted {member.mention} after `{duration}` seconds.")

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-mute @user [duration] [reason]`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# -------------------- UNMUTE --------------------

@bot.hybrid_command(description="Unmute a muted member.")
@commands.has_permissions(manage_roles=True)
@app_commands.describe(member="The member to unmute")
async def unmute(ctx: commands.Context, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not muted_role:
        await ctx.send("❌ 'Muted' role not found.")
        return

    if muted_role not in member.roles:
        await ctx.send(f"ℹ️ {member.mention} is not muted.")
        return

    await member.remove_roles(muted_role)

    try:
        await member.send(f"🔊 You have been unmuted in **{ctx.guild.name}**.")
    except:
        await ctx.send("⚠️ Couldn't DM the user.", ephemeral=True)

    await ctx.send(f"🔊 {member.mention} has been unmuted.")

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-unmute @user`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# -------------------- WARN --------------------

@bot.hybrid_command(description="Warn a user (with DM).")
@commands.has_permissions(manage_messages=True)
@app_commands.describe(member="The user to warn", reason="The reason for the warning")
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**.\nReason: `{reason}`")
    except (discord.Forbidden, discord.HTTPException):
        await ctx.send("⚠️ Couldn't DM the warned user.", ephemeral=True)

    await ctx.send(f"⚠️ Warned {member.mention} | Reason: `{reason}`")

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-warn @user [reason]`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to warn users.")
    else:
        await ctx.send(f"⚠️ Error: {str(error)}")
    
# --------------------- UTILITY ---------------------

# -------------------- TIME --------------------

import pytz
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

@bot.hybrid_command(description="Get the current time in any location.")
@app_commands.describe(location="City or country name (e.g., Tokyo, Brazil, Chennai)")
async def time(ctx: commands.Context, *, location: str = None):
    if not location:
        await ctx.send("❌ Usage: `-time <city>` — Example: `-time Tokyo`")
        return

    geolocator = Nominatim(user_agent="time-bot")
    tf = TimezoneFinder()

    try:
        loc = geolocator.geocode(location)
        if not loc:
            await ctx.send("⚠️ Location not found.")
            return

        timezone_str = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
        if not timezone_str:
            await ctx.send("⚠️ Could not determine timezone for this location.")
            return

        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await ctx.send(f"🕒 The current time in **{location.title()}** ({timezone_str}) is: `{now}`")

    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: `{str(e)}`")

# -------------------- PURGE --------------------

@bot.hybrid_command(description="Delete bulk messages from a channel.")
@commands.has_permissions(manage_messages=True)
@app_commands.describe(amount="Number of messages to delete (1–100)")
async def purge(ctx: commands.Context, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("⚠️ Please choose a number between 1 and 100.")
        return

    await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    confirm = await ctx.send(f"🧹 Deleted `{amount}` messages.")
    await confirm.delete(delay=3)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `-purge [1–100]`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to manage messages.")
    else:
        await ctx.send(f"⚠️ Error: {str(error)}")

# -------------------- HELP --------------------

@bot.hybrid_command(description="Display a list of moderation commands.")
async def help(ctx: commands.Context):
    prefix = ctx.prefix if hasattr(ctx, 'prefix') else '-'  # fallback for slash usage

    embed = discord.Embed(
        title="🛠️ Moderation Commands",
        description="Here’s a list of commands you can use:",
        color=discord.Color.orange()
    )

    embed.add_field(name=f"{prefix}ping", value="Check if the bot is online", inline=False)
    embed.add_field(name=f"{prefix}kick @user [reason]", value="Kick a user from the server", inline=False)
    embed.add_field(name=f"{prefix}ban @user [reason]", value="Ban a user from the server", inline=False)
    embed.add_field(name=f"{prefix}unban [name#1234 or ID]", value="Unban a user by tag or ID", inline=False)
    embed.add_field(name=f"{prefix}mute @user [seconds] [reason]", value="Mute a user", inline=False)
    embed.add_field(name=f"{prefix}unmute @user", value="Unmute a muted user", inline=False)
    embed.add_field(name=f"{prefix}warn @user [reason]", value="Warn a user", inline=False)
    embed.add_field(name=f"{prefix}purge [1–100]", value="Delete messages in bulk", inline=False)

    embed.set_footer(text="Bot developed by cubicc__ • Use commands responsibly.")

    await ctx.send(embed=embed)

# -------------------- KEEP RENDER ALIVE --------------------
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# -------------------- RUN BOT --------------------

import sys

token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ DISCORD_TOKEN not found in environment variables.")
    sys.exit()

bot.run(token)
