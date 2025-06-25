# -*- coding: utf-8 -*-
"""
AI 相關功能 Cog。

包含由 AI 驅動的功能，例如：
- 在特定頻道監聽訊息，進行 MyGo 圖片搜尋。
- 當圖片搜尋無果時，使用 Gemini LLM 生成相關台詞。
- 當機器人被提及時，使用 Gemini LLM 進行對話。
"""
import discord
from discord.ext import commands
import aiohttp
import random
from src import config

# 嘗試 import google.generativeai，如果失敗則無法使用 LLM 功能
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# --- Gemini AI 初始化 ---
# 只有在套件存在且提供了 API Key 的情況下才進行設定
if GENAI_AVAILABLE and config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
else:
    GENAI_AVAILABLE = False  # 如果沒有 key，也視為不可用


class AI(commands.Cog):
    """AI 相關功能，包括 MyGo 圖片搜尋和 LLM 互動。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 同樣，只有在可用時才初始化模型
        if GENAI_AVAILABLE:
            self.model = genai.GenerativeModel("gemini-pro")
        else:
            self.model = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽訊息，根據頻道和內容觸發不同 AI 功能。"""
        if message.author.bot:
            return

        # --- MyGo 圖片搜尋功能 ---
        if message.channel.id == config.MYGO_CHANNEL_ID:
            await self.handle_mygo_search(message)

        # --- LLM 回應功能 (被 @ 時觸發) ---
        if self.model and self.bot.user in message.mentions:
            # 避免在 MyGo 頻道對同一則訊息重複回應
            if message.channel.id == config.MYGO_CHANNEL_ID:
                return
            await self.handle_llm_response(message)

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
                    elif self.model:
                        # 如果找不到圖片，使用 LLM 生成一句相關台詞
                        async with message.channel.typing():
                            await message.channel.send("找不到相關圖片，讓我想想... 🤔")
                            prompt = f"「{keyword}」這句話聽起來像是 MyGO!!!!! 裡的哪個角色會說的台詞？請你扮演那個角色，並用該角色的口吻，生成一句全新的、風格相似的台詞。"
                            llm_response = await self.model.generate_content_async(
                                prompt
                            )
                            await message.channel.send(llm_response.text)
            except aiohttp.ClientError as e:
                print(f"呼叫 MyGo API 時發生網路錯誤: {e}")
            except Exception as e:
                print(f"處理 MyGo 搜尋時發生未預期錯誤: {e}")

    async def handle_llm_response(self, message: discord.Message):
        """處理 LLM 的回應請求。"""
        # 移除 mention，取得純文字內容
        prompt = message.content.replace(f"<@!{self.bot.user.id}>", "").strip()
        if not prompt:
            await message.channel.send("找我有什麼事嗎？")
            return

        async with message.channel.typing():
            try:
                response = await self.model.generate_content_async(prompt)
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
    if not GENAI_AVAILABLE:
        print(
            "警告：`google-generativeai` 套件未安裝或 GEMINI_API_KEY 未設定，AI Cog 的 LLM 功能將被停用。"
        )
    if not config.MYGO_CHANNEL_ID or config.MYGO_CHANNEL_ID == 0:
        print("警告：MYGO_CHANNEL_ID 未設定，MyGo 圖片搜尋功能將無法在特定頻道作用。")
    await bot.add_cog(AI(bot))
