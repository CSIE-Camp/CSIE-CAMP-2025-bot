"""
每日簽到抽籤功能 Cog。

整合了簽到和抽籤功能，用戶簽到後會自動抽取今日運勢，
並根據運勢等級獲得不同的金錢獎勵，同時顯示隨機引言和生成圖片。
"""

import discord
from discord import app_commands
from discord.ext import commands
import datetime
import random
import asyncio
from io import BytesIO

# 導入共享的 user_data_manager 實例，確保資料操作的同步與一致性
from src.utils.user_data import user_data_manager
from src.utils.achievements import AchievementManager
from src.utils.image_gen import generate_image
from src.constants import FORTUNE_LEVELS, QUOTE_REPLACEMENTS, ACG_QUOTES_FILE
from src import config


class DailyCheckin(commands.Cog):
    """處理每日簽到抽籤相關的指令。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 載入 ACG 名言
        self.quotes = self._load_quotes()
        self.checkin_count: dict[datetime.date, int] = {}

    def _load_quotes(self) -> list:
        """載入 ACG 名言"""
        try:
            import json

            with open(ACG_QUOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ 載入名言失敗: {e}")
            return ["今天也要元氣滿滿喔！", "加油！你一定可以的！", "相信自己的力量！"]

    @app_commands.command(
        name="checkin", description="每日簽到抽籤！簽到後會自動抽取今日運勢並獲得獎勵！"
    )
    async def checkin(self, interaction: discord.Interaction):
        """
        每日簽到抽籤功能。
        用戶簽到後會自動抽取今日運勢，並根據運勢等級獲得不同的金錢獎勵。
        """
        user_id = interaction.user.id
        today = datetime.date.today()
        today_str = today.isoformat()

        now = datetime.datetime.now()
        if now < datetime.datetime(now.year, now.month, now.day, 7, 50):
            await AchievementManager.check_and_award_achievement(user_id, "early_bird", self.bot)
            count = self.checkin_count.get(now.date(), 0)
            if count < 3:
                await AchievementManager.check_and_award_achievement(user_id, "early_bird_eat_worm", self.bot)
                self.checkin_count[now.date()] = count + 1

        # 獲取用戶資料
        user = await user_data_manager.get_user(user_id, interaction.user)

        last_checkin_str = user.get("last_sign_in")
        if last_checkin_str == today_str:
            await interaction.response.send_message(
                f"👋 {interaction.user.mention} 你今天已經簽到過了！明天再來吧。",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)

        # 計算連續簽到天數
        yesterday = today - datetime.timedelta(days=1)
        current_streak = user.get("sign_in_streak", 0)

        if last_checkin_str == yesterday.isoformat():
            # 如果昨天有簽到，連續天數+1
            new_streak = current_streak + 1
        else:
            # 如果昨天沒簽到 (中斷或首次)，則重置為 1
            new_streak = 1

        if new_streak == 4:
            await AchievementManager.check_and_award_achievement(
                user_id, "attendance_award", self.bot
            )
            
        # 抽取今日運勢
        fortune, color, quote = self._get_random_fortune()

        # 根據運勢等級計算金錢獎勵
        base_reward = self._calculate_fortune_reward(fortune)
        streak_bonus = new_streak * 5  # 每連續一天，額外獎勵增加 5 元
        total_reward = base_reward + streak_bonus

        # 更新用戶資料
        user["money"] += total_reward
        user["last_sign_in"] = today_str
        user["sign_in_streak"] = new_streak

        # 使用異步方法將更新後的資料寫回檔案
        await user_data_manager.update_user_data(user_id, user)

        # 檢查成就
        await self._check_achievements(user_id, new_streak, user["money"], interaction)

        # 建立簽到結果嵌入訊息
        embed = discord.Embed(
            title="🔮 每日簽到抽籤",
            description=f"🎉 {interaction.user.mention} 簽到成功！",
            color=color,
        )

        embed.add_field(name="🌟 今日運勢", value=f"**{fortune}**", inline=False)
        embed.add_field(name="💰 運勢獎勵", value=f"{base_reward} 元", inline=True)
        embed.add_field(name="🔥 連續簽到", value=f"{new_streak} 天", inline=True)
        embed.add_field(name="🎁 連續獎勵", value=f"{streak_bonus} 元", inline=True)
        embed.add_field(name="💸 總獲得", value=f"**{total_reward} 元**", inline=False)
        embed.add_field(name="💭 今日語錄", value=f"*{quote}*", inline=False)

        embed.set_footer(
            text=f"為 {interaction.user.display_name} 抽取 | 總金錢: {user['money']} 元"
        )

        # 嘗試生成圖片（添加超時保護）
        image_bytes = None
        try:
            image_bytes = await asyncio.wait_for(
                self._generate_fortune_image(quote), timeout=30.0
            )
        except asyncio.TimeoutError:
            print("⏰ 圖片生成超時，將只顯示文字版本")
        except (ConnectionError, ValueError, ImportError) as e:
            print(f"❌ 圖片生成失敗: {e}")

        # 根據圖片生成結果決定回傳方式
        if image_bytes:
            file = discord.File(image_bytes, filename="fortune.png")
            embed.set_image(url="attachment://fortune.png")
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)
            
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(interaction.user.id, "checkin", interaction)

    def _get_random_fortune(self) -> tuple[str, int, str]:
        """隨機取得運勢和名言"""
        # 使用權重來選擇運勢
        weights = [weight for _, _, weight in FORTUNE_LEVELS]
        chosen_fortune = random.choices(FORTUNE_LEVELS, weights=weights, k=1)[0]
        fortune, color, _ = chosen_fortune

        # 隨機選擇一個名言並處理替換
        raw_quote = (
            random.choice(self.quotes) if self.quotes else "今天也要元氣滿滿喔！"
        )

        quote = raw_quote
        for old, new in QUOTE_REPLACEMENTS.items():
            quote = quote.replace(old, new)

        return fortune, color, quote

    def _calculate_fortune_reward(self, fortune: str) -> int:
        """根據運勢等級計算金錢獎勵"""
        fortune_rewards = {
            "🌟 不可思議的傳說大吉！": random.randint(500, 1000),
            "🚀 超級無敵大吉！": random.randint(300, 500),
            "🎊 無敵大吉！": random.randint(200, 300),
            "😄 大吉！": random.randint(150, 200),
            "😊 中吉！": random.randint(100, 150),
            "🙂 普通吉！": random.randint(80, 120),
            "🤔 小吉！": random.randint(60, 100),
            "🤏 迷你吉！": random.randint(50, 80),
        }
        return fortune_rewards.get(fortune, 100)

    async def _generate_fortune_image(self, quote: str) -> BytesIO | None:
        """生成運勢圖片"""
        # 如果沒有配置 HUGGINGFACE_TOKEN，則跳過圖片生成
        if not config.HUGGINGFACE_TOKEN:
            print("⚠️  未配置 HUGGINGFACE_TOKEN，跳過圖片生成")
            return None

        return await generate_image(quote)

    async def _check_achievements(
        self, user_id: int, streak: int, money: int, interaction: discord.Interaction
    ):
        """檢查並觸發相關成就"""
        try:
            # 檢查連續簽到成就
            if streak >= 7:
                await AchievementManager.check_and_award_achievement(
                    user_id, "lucky_streak", interaction
                )

            # 檢查金錢成就
            await AchievementManager.check_money_achievements(
                user_id, money, interaction
            )
        except (AttributeError, KeyError) as e:
            print(f"⚠️ 檢查成就時出錯: {e}")


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(DailyCheckin(bot))
