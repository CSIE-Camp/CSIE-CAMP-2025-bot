"""
遊戲事件處理 Cog。

負責監聽與遊戲機制相關的背景事件，最主要的就是使用者發言以獲得經驗值。
"""

import discord
from discord.ext import commands
import random
import asyncio

# 導入共享的 user_data_manager 以確保資料操作的同步與一致性
from src.utils.user_data import user_data_manager
from src.constants import Colors
from src import config


class GameEvents(commands.Cog):
    """處理遊戲相關的背景事件，例如訊息經驗值。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 為每個使用者的經驗值操作建立一個鎖，防止同時處理多條訊息時發生競爭條件
        self.user_exp_locks: dict[int, asyncio.Lock] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽所有非指令訊息，為使用者增加經驗值並處理升級。"""
        # 忽略來自機器人的訊息、由指令觸發的訊息，以及來自討論串的訊息
        if (
            message.author.bot
            or message.content.startswith(self.bot.command_prefix)
            or isinstance(message.channel, discord.Thread)
        ):
            return

        user_id = message.author.id
        user_obj = message.author

        # 獲取或為該使用者建立一個鎖
        if user_id not in self.user_exp_locks:
            self.user_exp_locks[user_id] = asyncio.Lock()
        lock = self.user_exp_locks[user_id]

        # 使用該使用者的專屬鎖來確保經驗值計算的原子性
        async with lock:
            user = await user_data_manager.get_user(user_id, user_obj)
            original_level = user.get("lv", 1)

            # --- 經驗值與金錢獎勵 ---
            # 每次發言給予少量經驗值與金錢
            exp_gain = random.randint(1, 3)
            money_gain = random.randint(1, 2)
            user["exp"] += exp_gain
            user["money"] += money_gain

            # --- 隨機事件 ---
            # 有 5% 的機率觸發一個隨機事件
            if random.random() < 0.05:  # 5% 機率
                event_type = random.choice(["money_gain", "money_loss"])

                if event_type == "money_gain":
                    found_money = random.randint(5, 20)
                    user["money"] += found_money
                    event_embed = discord.Embed(
                        title="✨ 好運降臨！",
                        description=f"{message.author.mention} 在路上撿到了 **{found_money}** 元！",
                        color=Colors.WARNING,
                    )
                    await message.channel.send(embed=event_embed)

                elif event_type == "money_loss":
                    lost_money = random.randint(5, 20)
                    # 確保錢不會變負數
                    user["money"] = max(0, user["money"] - lost_money)
                    event_embed = discord.Embed(
                        title="💸 壞事發生了...",
                        description=f"{message.author.mention} 不小心弄丟了 **{lost_money}** 元...",
                        color=Colors.ERROR,
                    )
                    await message.channel.send(embed=event_embed)

            # --- 升級檢查 ---
            # 使用 while 迴圈處理一次獲得大量經驗值時可能發生的連續升級
            new_level = user.get("lv", 1)
            new_exp = user["exp"]

            # 每次迴圈都重新計算當前等級所需的經驗值
            required_exp_for_current_level = 10 * new_level
            while new_exp >= required_exp_for_current_level:
                new_level += 1
                new_exp -= required_exp_for_current_level
                # 更新下一次迴圈的經驗值需求
                required_exp_for_current_level = 10 * new_level

            # 如果等級有變化，才更新等級、經驗值並發送通知
            if new_level > original_level:
                user["lv"] = new_level
                user["exp"] = new_exp

                # 發送升級通知
                level_up_embed = discord.Embed(
                    title="🎉 等級提升！",
                    description=f"恭喜 {message.author.mention} 升級到 **Lv. {user['lv']}**！",
                    color=Colors.PRIMARY,
                )
                level_up_embed.set_thumbnail(
                    url=(
                        message.author.avatar.url
                        if message.author.avatar
                        else message.author.default_avatar.url
                    )
                )
                # 通知到公告頻道
                announce_channel = self.bot.get_channel(config.ANNOUNCEMENT_CHANNEL_ID)
                if announce_channel:
                    await announce_channel.send(embed=level_up_embed)
                else:
                    await message.channel.send(embed=level_up_embed)

            # --- 儲存資料 ---
            # 使用 update_user_data 將更新後的資料寫回檔案
            await user_data_manager.update_user_data(user_id, user)


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(GameEvents(bot))
