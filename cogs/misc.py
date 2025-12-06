# cogs/misc.py
from discord.ext import commands
import discord
import pytz
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # hybrid ping (works as -ping and /ping)
    @commands.hybrid_command(name="ping", description="Check if the bot is online (hybrid)")
    async def ping(self, ctx):
        await ctx.send("🏓 Pong!")

    # help (hybrid so both prefix & slash can call it)
    @commands.hybrid_command(name="help", description="Display a list of moderation commands.")
    async def help(self, ctx):
        prefix = ctx.prefix if hasattr(ctx, 'prefix') else '-'
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

    # mutual (hybrid)
    @commands.hybrid_command(name="mutual", description="Check how many mutual servers you share with a user ID.")
    @commands.describe(user_id="The Discord ID of the user")
    async def mutual(self, ctx, user_id: str):
        if not user_id.isdigit():
            await ctx.send("❌ Please enter a valid user ID.")
            return

        uid = int(user_id)
        mutual_guilds = []

        for guild in self.bot.guilds:
            member = guild.get_member(uid)
            if member:
                mutual_guilds.append(guild.name)
                continue
            try:
                await guild.fetch_member(uid)
                mutual_guilds.append(guild.name)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        count = len(mutual_guilds)
        if count == 0:
            await ctx.send(f"ℹ️ No mutual servers found with `{user_id}`.")
            return

        if count > 10:
            preview = ', '.join(mutual_guilds[:10])
            more = count - 10
            await ctx.send(
                f"🤝 **Mutual Servers:** {count}\n🔹 **First 10:** {preview}... (+{more} more)"
            )
        else:
            await ctx.send(f"🤝 **Mutual Servers ({count}):** {', '.join(mutual_guilds)}")

    # time command
    @commands.hybrid_command(name="time", description="Get the current time in any location.")
    @commands.describe(location="City or country name (e.g., Tokyo, Brazil, Chennai)")
    async def time(self, ctx, *, location: str = None):
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

async def setup(bot):
    await bot.add_cog(Misc(bot))
