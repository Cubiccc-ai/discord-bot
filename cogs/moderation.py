# cogs/moderation.py
from discord.ext import commands
import discord
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # helper: safe reply (ephemeral only when interaction available)
    async def safe_reply(self, ctx, content, *, ephemeral=False):
        try:
            interaction = getattr(ctx, "interaction", None)
            if ephemeral and interaction:
                if not interaction.response.is_done():
                    await interaction.response.send_message(content, ephemeral=True)
                else:
                    await interaction.followup.send(content, ephemeral=True)
            else:
                await ctx.send(content)
        except Exception:
            try:
                await ctx.send(content)
            except:
                pass

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.send(f"👢 You were kicked from **{ctx.guild.name}**.\n**Reason:** {reason}")
        except discord.Forbidden:
            await self.safe_reply(ctx, "⚠️ Couldn't DM the user (they probably have DMs off).", ephemeral=False)
        except discord.HTTPException:
            pass

        try:
            await member.kick(reason=reason)
            await self.safe_reply(ctx, f"👢 Kicked {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self.safe_reply(ctx, "❌ I don't have permission to kick that user.")
        except discord.HTTPException:
            await self.safe_reply(ctx, "⚠️ Kick failed due to a network error.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-kick @user [reason]`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to use this command.")
        else:
            await self.safe_reply(ctx, f"❌ An error occurred: {error}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.describe(user="The member to ban", reason="Reason for the ban")
    async def ban(self, ctx: commands.Context, user: str, *, reason: str = "No reason provided"):
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            try:
                user_obj = await self.bot.fetch_user(int(user))
                await ctx.guild.ban(user_obj, reason=reason)
                await self.safe_reply(ctx, f"🔨 Banned `{user_obj}` | Reason: {reason}")
                return
            except Exception as e:
                await self.safe_reply(ctx, f"❌ Couldn't find user with ID `{user}`. Error: {e}")
                return

        try:
            await member.send(f"🔨 You were banned from **{ctx.guild.name}**.\n**Reason:** {reason}")
        except:
            pass

        try:
            await member.ban(reason=reason)
            await self.safe_reply(ctx, f"🔨 Banned {member.mention} | Reason: {reason}")
        except discord.Forbidden:
            await self.safe_reply(ctx, "❌ I can't ban that user.")
        except discord.HTTPException:
            await self.safe_reply(ctx, "⚠️ Ban failed due to a network error.")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-ban @user [reason]`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to use this command.")
        else:
            await self.safe_reply(ctx, f"❌ An error occurred: {error}")

    @commands.hybrid_command(name="unban", description="Unban a member by name#1234 or ID.")
    @commands.has_permissions(ban_members=True)
    @commands.describe(user_input="Name#1234 or user ID of the banned user")
    async def unban(self, ctx: commands.Context, *, user_input: str):
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
                    await self.safe_reply(ctx, f"⚠️ Couldn't DM {user}.", ephemeral=False)
                await ctx.guild.unban(user)
                await self.safe_reply(ctx, f"✅ Unbanned {user.mention}")
                return

        await self.safe_reply(ctx, "⚠️ User not found in the ban list.")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-unban name#1234 or ID`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to use this command.")
        else:
            await self.safe_reply(ctx, f"❌ An error occurred: {error}")

    @commands.hybrid_command(name="mute", description="Mute a user, optionally for a duration (seconds).")
    @commands.has_permissions(manage_roles=True)
    @commands.describe(member="The member to mute", duration="Duration in seconds", reason="Reason for muting")
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int = None, *, reason: str = "No reason provided"):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            await self.safe_reply(ctx, "❌ 'Muted' role not found. Please create one with no Send Messages/Speak permissions.")
            return

        await member.add_roles(muted_role, reason=reason)

        try:
            await member.send(f"🔇 You have been muted in **{ctx.guild.name}**.\nReason: `{reason}`")
        except:
            await self.safe_reply(ctx, "⚠️ Couldn't DM the muted user.", ephemeral=False)

        await self.safe_reply(ctx, f"🔇 Muted {member.mention} | Reason: `{reason}`")

        if duration:
            await asyncio.sleep(duration)
            await member.remove_roles(muted_role)
            try:
                await member.send(f"🔊 You have been unmuted in **{ctx.guild.name}**.")
            except:
                pass
            await self.safe_reply(ctx, f"🔊 Automatically unmuted {member.mention} after `{duration}` seconds.")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-mute @user [duration] [reason]`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to use this command.")
        else:
            await self.safe_reply(ctx, f"❌ An error occurred: {error}")

    @commands.hybrid_command(name="unmute", description="Unmute a muted member.")
    @commands.has_permissions(manage_roles=True)
    @commands.describe(member="The member to unmute")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            await self.safe_reply(ctx, "❌ 'Muted' role not found.")
            return

        if muted_role not in member.roles:
            await self.safe_reply(ctx, f"ℹ️ {member.mention} is not muted.")
            return

        await member.remove_roles(muted_role)

        try:
            await member.send(f"🔊 You have been unmuted in **{ctx.guild.name}**.")
        except:
            await self.safe_reply(ctx, "⚠️ Couldn't DM the user.", ephemeral=False)

        await self.safe_reply(ctx, f"🔊 {member.mention} has been unmuted.")

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-unmute @user`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to use this command.")
        else:
            await self.safe_reply(ctx, f"❌ An error occurred: {error}")

    @commands.hybrid_command(name="warn", description="Warn a user (with DM).")
    @commands.has_permissions(manage_messages=True)
    @commands.describe(member="The user to warn", reason="The reason for the warning")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**.\nReason: `{reason}`")
        except (discord.Forbidden, discord.HTTPException):
            await self.safe_reply(ctx, "⚠️ Couldn't DM the warned user.", ephemeral=False)

        await self.safe_reply(ctx, f"⚠️ Warned {member.mention} | Reason: `{reason}`")

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-warn @user [reason]`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to warn users.")
        else:
            await self.safe_reply(ctx, f"⚠️ Error: {str(error)}")

    @commands.hybrid_command(name="purge", description="Delete bulk messages from a channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.describe(amount="Number of messages to delete (1–100)")
    async def purge(self, ctx: commands.Context, amount: int):
        if amount < 1 or amount > 100:
            await self.safe_reply(ctx, "⚠️ Please choose a number between 1 and 100.")
            return

        await ctx.channel.purge(limit=amount + 1)
        confirm = await ctx.send(f"🧹 Deleted `{amount}` messages.")
        await confirm.delete(delay=3)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.safe_reply(ctx, "❌ Usage: `-purge [1–100]`")
        elif isinstance(error, commands.MissingPermissions):
            await self.safe_reply(ctx, "❌ You don't have permission to manage messages.")
        else:
            await self.safe_reply(ctx, f"⚠️ Error: {str(error)}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
