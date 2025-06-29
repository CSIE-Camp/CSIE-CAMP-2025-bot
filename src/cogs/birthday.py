import discord
from discord.ext import commands


class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return None
        if not self.bot.user:
            print("[⚠ Warning] Not logged in")
            return None
        if not message.mentions:
            return None
        if self.bot.user not in message.mentions:
            return None
        if "生日快樂" in message.content or "happy birthday" in message.content.lower():
            await message.author.send("`flag{||0c371a2a4d311b552963dddf78af59||}`")
            return None
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot))
