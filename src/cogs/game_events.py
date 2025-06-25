# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.utils.user_data import UserData
from src import config


class GameEvents(commands.Cog):
    """處理遊戲相關的背景事件，例如訊息經驗值。"""

    def __init__(self, bot):
        self.bot = bot
        self.user_data = UserData(config.USER_DATA_FILE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽所有非指令訊息，為使用者增加經驗值並處理升級。"""
        # 忽略機器人或指令
        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            return

        user = self.user_data.get_user(message.author.id)
        user["exp"] += 2

        required_exp = 10 * user["lv"]
        if user["exp"] >= required_exp:
            user["lv"] += 1
            user["exp"] -= required_exp  # 將多餘的經驗值保留到下一級
            await message.channel.send(
                f'恭喜 {message.author.mention} 升級到 Lv. {user["lv"]}！'
            )

        self.user_data.save_data()


async def setup(bot):
    await bot.add_cog(GameEvents(bot))
