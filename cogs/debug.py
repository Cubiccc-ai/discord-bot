# cogs/debug.py
from discord.ext import commands

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="whoami")
    async def whoami(self, ctx):
        # tells which bot user is replying and its id
        user = getattr(self.bot, "user", None)
        await ctx.send(f"Bot user: {user}  (id={getattr(user,'id',None)})")

    @commands.command(name="listcmds")
    async def listcmds(self, ctx):
        names = [c.name for c in self.bot.commands]
        await ctx.send("Prefix commands: " + (", ".join(names) or "NONE"))

    @commands.command(name="listapp")
    async def listapp(self, ctx):
        names = [c.name for c in self.bot.tree.walk_commands()]
        await ctx.send("App/tree commands: " + (", ".join(names) or "NONE"))

async def setup(bot):
    await bot.add_cog(Debug(bot))
