"""
每日簽到功能 Cog。
"""

import discord
from discord.ext import commands
import datetime
import random

# 導入共享的 user_data_manager 實例，確保資料操作的同步與一致性
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager


class SignIn(commands.Cog):
    """處理每日簽到相關的指令。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sign_in", aliases=["簽到"])
    async def sign_in(self, ctx: commands.Context):
        """
        每日簽到以領取獎勵。
        連續簽到可以獲得額外獎勵！
        """
        user_id = ctx.author.id
        today = datetime.date.today()

        # 使用異步方法從共享的 manager 獲取使用者資料
        user = await user_data_manager.get_user(user_id)

        last_sign_in_str = user.get("last_sign_in")

        if last_sign_in_str == today.isoformat():
            await ctx.send(
                f"👋 {ctx.author.mention} 你今天已經簽到過了！明天再來吧。",
                ephemeral=True,
            )
            return

        # --- 計算連續簽到 ---
        yesterday = today - datetime.timedelta(days=1)
        current_streak = user.get("sign_in_streak", 0)

        if last_sign_in_str == yesterday.isoformat():
            # 如果昨天有簽到，連續天數+1
            new_streak = current_streak + 1
        else:
            # 如果昨天沒簽到 (中斷或首次)，則重置為 1
            new_streak = 1

        # --- 計算獎勵 ---
        base_reward = random.randint(50, 100)
        streak_bonus = new_streak * 5  # 每連續一天，額外獎勵增加 5 元
        total_reward = base_reward + streak_bonus

        # --- 更新使用者資料 ---
        user["money"] += total_reward
        user["last_sign_in"] = today.isoformat()
        user["sign_in_streak"] = new_streak

        # 使用異步方法將更新後的資料寫回檔案
        await user_data_manager.update_user_data(user_id, user)

        # --- 檢查成就 ---
        # 檢查連續簽到成就
        if new_streak >= 7:
            await achievement_manager.check_and_award_achievement(
                user_id, "lucky_streak", ctx
            )

        # 檢查金錢成就
        await achievement_manager.check_money_achievements(user_id, user["money"], ctx)

        # --- 發送美化後的回應訊息 ---
        embed = discord.Embed(
            title="簽到成功！",
            description=f"🎉 {ctx.author.mention} 你好！",
            color=discord.Color.gold(),
        )
        embed.add_field(name="基本獎勵", value=f"💰 {base_reward}", inline=True)
        embed.add_field(name="連續簽到", value=f"🔥 {new_streak} 天", inline=True)
        embed.add_field(name="額外獎勵", value=f"💰 {streak_bonus}", inline=True)
        embed.set_footer(text=f"總共獲得 {total_reward} 籌碼！")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(SignIn(bot))
