"""
Cog for general LLM chat.
"""

import discord
from discord.ext import commands

from src.utils.prompt import BOT_PROMPT
from src.utils.llm import llm_model
from datetime import datetime

from src.utils.achievements import achievement_manager
from src.utils.user_data import user_data_manager


class Chat(commands.Cog):
    """Cog for general LLM chat."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model
        # Cooldown: 1 message per 30 seconds per user
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 30.0, commands.BucketType.user
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for mentions."""
        if message.author.bot:
            return

        if self.model and self.bot.user in message.mentions:
            # Check for cooldown
            bucket = self._cd.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                await message.reply(
                    f"你問得太快了，讓我先喘口氣！請在 {retry_after:.2f} 秒後再試一次。",
                    delete_after=5,
                )
                return
            await self.handle_llm_response(message)

                # 檢查成就
        user_id = message.user.id
        today = datetime.date.today()
        today_str = today.isoformat()

        # 獲取用戶資料
        user = await user_data_manager.get_user(user_id, message.author)

        last_checkin_str = user.get("last_tag_bot")

        # 計算連續簽到天數
        yesterday = today - datetime.timedelta(days=1)
        current_streak = user.get("tag_bot_streak", 0)

        if last_checkin_str == yesterday.isoformat():
            # 如果昨天有簽到，連續天數+1
            new_streak = current_streak + 1
        else:
            # 如果昨天沒簽到 (中斷或首次)，則重置為 1
            new_streak = 1

        if new_streak == 4:
            achievement_manager.unlock_achievement(user_id, "daily", self.bot)

    

    async def handle_llm_response(self, message: discord.Message):
        """Handle a response from the LLM."""
        prompt = (
            message.content.replace(f"<@{self.bot.user.id}>", "")
            .replace(f"<@!{self.bot.user.id}>", "")
            .strip()
        )

        if not prompt:
            await message.channel.send("找我有什麼事嗎？")
            return

        async with message.channel.typing():
            try:
                response = await self.model.generate_content_async([BOT_PROMPT, prompt])
                # Discord 訊息長度限制為 2000 字元
                if len(response.text) > 2000:
                    await message.channel.send(response.text[:1990] + "...")
                else:
                    await message.channel.send(response.text)
            except Exception as e:
                await message.channel.send("抱歉，我的腦袋好像有點短路了... 😵")
                print(f"使用 Gemini 生成內容時發生錯誤: {e}")


async def setup(bot: commands.Bot):
    """Set up the Chat cog."""
    await bot.add_cog(Chat(bot))
