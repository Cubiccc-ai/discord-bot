from discord.ext import commands
import discord

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="testping")
    async def testping(self, ctx):
        await ctx.send("Test pong from cog!")

async def setup(bot):
    await bot.add_cog(Misc(bot))
