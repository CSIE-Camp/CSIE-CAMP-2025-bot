# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import random
from src.utils.user_data import UserData
from src import config


class Slot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = UserData(config.USER_DATA_FILE)

    @commands.command(name="拉霸")
    async def slot(self, ctx, amount: int):
        """拉霸遊戲"""
        user = self.user_data.get_user(ctx.author.id)
        current_money = user["money"]

        if amount > current_money:
            await ctx.send(
                f"你現在只有 {current_money} 元，你卻想花 {amount} 元，我們不支援賒帳系統啦>.<"
            )
            return
        if amount <= 0:
            await ctx.send("請輸入大於 0 的金額！")
            return

        symbols = [
            "<:discord:1385577039838449704>",
            "<:python:1385577058184466502>",
            "<:block:1385577076865630300>",
            "<:mushroom:1385577154775089182>",
            "<:dino:1385577110965321840>",
            "<:money:1385577138727686286>",
            "<:block:1385577076865630300>",
        ]

        result = [random.choice(symbols) for _ in range(5)]
        result_str = "".join(result)
        author_mention = ctx.author.mention
        author_name = ctx.author.name
        await ctx.send(f"{result_str}")

        max_count = max(result.count(symbol) for symbol in symbols)
        winnings = 0

        if max_count == 5:
            winnings = 100 * amount
            add_msgs = [
                "原...原來，你的幸運值已經突破系統上限了>.<",
                "是百年難得一見的拉霸奇才！",
                "你該不會駭入系統了吧！？",
            ]
            msg = f"{author_mention} 恭喜你中了五個！！！賺了 {winnings} 元！{random.choice(add_msgs)}"
        elif max_count == 4:
            winnings = 10 * amount
            add_msgs = [
                "搞不好能遇到好事喔~",
                "下一代拉霸幫幫主就是你:O",
                "去找別人單挑猜拳吧",
            ]
            msg = f"{author_mention} 中了四個！！賺了 {winnings} 元！{random.choice(add_msgs)}"
        elif max_count == 3:
            winnings = amount
            msg = f"{author_name} 中了三個！賺了 {winnings} 元！運氣還不錯～"
        elif max_count == 2:
            winnings = -(amount // 2)
            msg = f"有兩個一樣，但還是損失了 {abs(winnings)} 元..."
        else:
            winnings = -amount
            add_msgs = [
                "只能說...菜就多練=v=",
                "也算變相的運氣好...啦T-T",
                "恭喜你把壞運用光了q-q",
            ]
            msg = f"沒有相同的...損失 {abs(winnings)} 元...{random.choice(add_msgs)}"

        user["money"] += winnings
        self.user_data.save_data()
        await ctx.send(msg)

    @slot.error
    async def slot_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("請輸入一個有效的數字作為籌碼數量！")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("請輸入要下的籌碼數量！")


async def setup(bot):
    await bot.add_cog(Slot(bot))
