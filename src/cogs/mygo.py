"""
Cog for MyGo related commands.
"""

import discord
from discord.ext import commands
import aiohttp
import random
import json

from src import config
from src.utils.llm import llm_model
from src.constants import MYGO_FILE


class MyGo(commands.Cog):
    """Cog for MyGo related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model
        # Cooldown: 1 message per 10 seconds per user for LLM part
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 10.0, commands.BucketType.user
        )
        # Load MyGo quotes
        try:
            with open(MYGO_FILE, "r", encoding="utf-8") as f:
                self.mygo_quotes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.mygo_quotes = []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages in the MyGo channel."""
        if message.author.bot:
            return

        if message.channel.id == config.MYGO_CHANNEL_ID:
            await self.handle_mygo_search(message)

    async def handle_mygo_search(self, message: discord.Message):
        """Handle MyGo image search with LLM fallback."""
        keyword = message.content
        if not keyword:
            return

        async with aiohttp.ClientSession() as session:
            try:
                # --- 1. First attempt: Direct search ---
                api_url = f"https://mygoapi.miyago9267.com/mygo/img?keyword={keyword}"
                async with session.get(api_url) as response:
                    response.raise_for_status()
                    result = await response.json()

                if result.get("urls"):
                    image_url = random.choice(result["urls"])["url"]
                    await message.channel.send(image_url)
                    return

                # --- If no direct match, proceed to LLM fallbacks ---
                if not self.model or not self.mygo_quotes:
                    return  # Can't do anything else

                # --- Check Cooldown for any LLM usage ---
                bucket = self._cd.get_bucket(message)
                retry_after = bucket.update_rate_limit()
                if retry_after:
                    await message.reply(
                        f"你問得太快了，AI 需要時間思考！請在 {retry_after:.2f} 秒後再試一次。",
                        delete_after=5,
                    )
                    return

                async with message.channel.typing():
                    # --- 2. Second attempt: Find similar quote ---
                    await message.channel.send(
                        "找不到完全符合的圖片，我試著找找看接近的台詞..."
                    )

                    quotes_str = "\n".join(self.mygo_quotes)
                    prompt1 = f"從以下《MyGO!!!!!》的台詞列表中，選出與使用者輸入的「{keyword}」語意最接近或最相關的一句台詞。請「只」回傳那句台詞，不要包含任何其他文字或引號。\n\n台詞列表：\n{quotes_str}"

                    closest_quote_response = await self.model.generate_content_async(
                        prompt1
                    )
                    closest_quote = closest_quote_response.text.strip()

                    if closest_quote:
                        api_url_2 = f"https://mygoapi.miyago9267.com/mygo/img?keyword={closest_quote}"
                        async with session.get(api_url_2) as response_2:
                            if response_2.ok:
                                result_2 = await response_2.json()
                                if result_2.get("urls"):
                                    await message.channel.send(
                                        f"我找到了這個，應該差不多吧？\n> {closest_quote}"
                                    )
                                    image_url_2 = random.choice(result_2["urls"])["url"]
                                    await message.channel.send(image_url_2)
                                    return

                    # --- 3. Third attempt: Generate new sentence ---
                    await message.channel.send("還是找不到相關圖片，讓我想想... 🤔")
                    prompt2 = f"「{keyword}」這句話聽起來像是 MyGO!!!!! 裡的哪個角色會說的台詞？請你扮演那個角色，並用該角色的口吻，生成一句全新的、風格相似的台詞。"
                    llm_response = await self.model.generate_content_async(prompt2)
                    await message.channel.send(llm_response.text)

            except aiohttp.ClientError as e:
                print(f"呼叫 MyGo API 時發生網路錯誤: {e}")
                await message.channel.send("抱歉，MyGo 圖庫好像連不上了，請稍後再試。")
            except Exception as e:
                print(f"處理 MyGo 搜尋時發生未預期錯誤: {e}")
                await message.channel.send("處理你的請求時發生了一點問題... 😵")


async def setup(bot: commands.Bot):
    """Set up the MyGo cog."""
    await bot.add_cog(MyGo(bot))
