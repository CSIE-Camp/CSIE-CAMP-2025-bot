import discord
from discord.ext import commands
import random
import asyncio
from src.utils.user_data import user_data_manager

# --- Game Configuration ---

# 拉霸機的符號
EMOJI_LIST = [
    "<:money:1385577138727686286>",
    "<:discord:1385577039838449704>",
    "<:python:1385577058184466502>",
    "<:dino:1385577110965321840>",
    "<:mushroom:1385577154775089182>",
    "<:block:1385577076865630300>",
]


# --- Helper Functions ---


class Slot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="拉霸", aliases=["slot"])
    @commands.cooldown(1, 10, commands.BucketType.user)  # 10秒冷卻
    async def slot(self, ctx, amount: int):
        """拉霸遊戲！"""
        user = await user_data_manager.get_user(ctx.author.id)
        current_money = user["money"]

        if amount > current_money:
            await ctx.send(
                f"你現在只有 {current_money} 元，想花 {amount} 元？我們不支援賒帳喔！"
            )
            return
        if amount <= 0:
            await ctx.send("請輸入大於 0 的金額！")
            return

        # --- 揭曉動畫 ---
        placeholder = "❓"
        reels = [placeholder] * 5
        slot_message = await ctx.send(f"# {' '.join(reels)}")
        await asyncio.sleep(0.5)

        final_result = random.choices(EMOJI_LIST, k=5)

        # 逐一揭曉結果
        for i in range(5):
            reels[i] = final_result[i]
            await slot_message.edit(content=f"# {' '.join(reels)}")
            await asyncio.sleep(0.5)

        # 刪除動畫訊息
        await slot_message.delete()

        # --- 計算與結果 ---
        counts = {symbol: final_result.count(symbol) for symbol in final_result}
        max_count = max(counts.values()) if counts else 0

        winnings = 0
        result_text = ""

        if max_count == 5:
            winnings = amount * 9  # 贏得賭注的9倍 (總共拿回10倍)
            result_text = "JACKPOT！五個一樣！太神啦！"
        elif max_count == 4:
            winnings = amount * 2  # 贏得賭注的2倍 (總共拿回3倍)
            result_text = "中了四個！運氣真好！"
        elif max_count == 3:
            winnings = 0  # 回本
            result_text = "中了三個！回本了，不賺不賠。"
        elif max_count == 2:
            winnings = -int(amount * 0.5)  # 輸掉一半賭注
            result_text = "只中了兩個，輸了一半..."
        else:  # max_count is 1 (all different)
            winnings = -amount  # 輸掉全部賭注
            result_text = "可惜，沒有中獎...再接再厲！"

        # 更新使用者資料
        user["money"] += winnings
        await user_data_manager.update_user_data(ctx.author.id, user)

        # 建立 Embed 結果
        if winnings > 0:
            color = discord.Color.green()
            title = "🎉 你贏了！ 🎉"
        elif winnings < 0:
            color = discord.Color.red()
            title = "😭 你輸了... 😭"
        else:
            color = discord.Color.yellow()
            title = "😐 打平了 😐"

        embed = discord.Embed(title=title, color=color)
        embed.set_author(
            name=f"{ctx.author.display_name} 的拉霸結果", icon_url=ctx.author.avatar.url
        )
        embed.description = f"# {' '.join(final_result)}"
        embed.add_field(name="說明", value=result_text, inline=False)
        embed.add_field(name="下注金額", value=f"`{amount}` 元", inline=True)
        embed.add_field(name="輸贏", value=f"`{winnings}` 元", inline=True)
        embed.add_field(name="目前餘額", value=f"`{user['money']}` 元", inline=True)

        await ctx.send(embed=embed)

    @slot.error
    async def slot_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("請輸入一個有效的數字作為籌碼數量！")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("請輸入要下的籌碼數量！ `!slot <金額>`")
            await ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"拉霸機還在冷卻中！請在 {error.retry_after:.1f} 秒後再試。")


async def setup(bot):
    await bot.add_cog(Slot(bot))
