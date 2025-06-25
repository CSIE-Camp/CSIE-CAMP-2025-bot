"""
AI 相關功能 Cog。

包含由 AI 驅動的功能，例如：
- 在特定頻道監聽訊息，進行 MyGo 圖片搜尋。
- 當圖片搜尋無果時，使用 Gemini LLM 生成相關台詞。
- 當機器人被提及時，使用 Gemini LLM 進行對話。
"""

import aiohttp
import random

import discord
from discord.ext import commands
from google import genai
from google.genai import types

from src import config
from src.utils.prompt import BOT_PROMPT


class AI(commands.Cog):
    """AI 相關功能，包括 MyGo 圖片搜尋和 LLM 互動。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = "gemini-2.5-flash"
        # 同樣，只有在可用時才初始化模型
        if config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        else:
            self.client = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽訊息，根據頻道和內容觸發不同 AI 功能。"""
        if message.author.bot:
            return

        if self.client and self.bot.user in message.mentions:
            await self.handle_llm_response(message)
            return

        # 若非提及，且在 MyGo 頻道，則觸發圖片搜尋
        if message.channel.id == config.MYGO_CHANNEL_ID:
            await self.handle_mygo_search(message)

    async def handle_mygo_search(self, message: discord.Message):
        """處理 MyGo 圖片搜尋請求。"""
        keyword = message.content
        if not keyword:
            return

        async with aiohttp.ClientSession() as session:
            try:
                api_url = f"https://mygoapi.miyago9267.com/mygo/img?keyword={keyword}"
                async with session.get(api_url) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if result.get("urls"):
                        image_url = random.choice(result["urls"])["url"]
                        await message.channel.send(image_url)
                    elif self.client:
                        # 如果找不到圖片，使用 LLM 生成一句相關台詞
                        async with message.channel.typing():
                            await message.channel.send("找不到相關圖片，讓我想想... 🤔")
                            prompt = f"「{keyword}」這句話聽起來像是 MyGO!!!!! 裡的哪個角色會說的台詞？請你扮演那個角色，並用該角色的口吻，生成一句全新的、風格相似的台詞。"
                            llm_response = await self.client.models.generate_content(
                                model=self.model, contents=prompt
                            )
                            await message.channel.send(llm_response.text)
            except aiohttp.ClientError as e:
                print(f"呼叫 MyGo API 時發生網路錯誤: {e}")
            except Exception as e:
                print(f"處理 MyGo 搜尋時發生未預期錯誤: {e}")

    async def handle_llm_response(self, message: discord.Message):
        """處理 LLM 的回應請求。"""
        # 移除所有對機器人的 mention，取得純文字內容
        # discord.py 的 `user.mention` 會生成 <@ID> 格式
        # 但使用者有伺服器暱稱時，收到的 content 會是 <@!ID> 格式
        # 因此兩種都需要移除
        prompt = (
            message.content.replace(f"<@{self.bot.user.id}>", "")
            .replace(f"<@!{self.bot.user.id}>", "")
            .strip()
        )
        print(f"收到 LLM 請求: {prompt}")
        if not prompt:
            await message.channel.send("找我有什麼事嗎？")
            return

        async with message.channel.typing():
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(system_instruction=BOT_PROMPT),
                    contents=prompt,
                )
                # Discord 訊息長度限制為 2000 字元
                if len(response.text) > 2000:
                    await message.channel.send(response.text[:1990] + "...")
                else:
                    await message.channel.send(response.text)
            except Exception as e:
                await message.channel.send("抱歉，我的腦袋好像有點短路了... 😵")
                print(f"使用 Gemini 生成內容時發生錯誤: {e}")


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(AI(bot))
