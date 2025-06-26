"""
Cog for MyGo related commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random
import json
from types import SimpleNamespace

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
            await self.handle_mygo_search(message, message.content)

    @app_commands.command(name="mygo", description="從 MyGO!!!!! 圖庫中搜尋一張圖片。")
    @app_commands.describe(keyword="要搜尋的台詞或關鍵字")
    async def mygo_slash(self, interaction: discord.Interaction, keyword: str):
        """Searches for a MyGo image."""
        await self.handle_mygo_search(interaction, keyword)

    @app_commands.command(name="mygo_quote", description="隨機取得一句 MyGo 經典台詞")
    async def mygo_quote(self, interaction: discord.Interaction):
        """隨機回傳一個 MyGo 的名言"""
        if not self.mygo_quotes:
            await interaction.response.send_message(
                "抱歉，我找不到任何 MyGo 的名言。", ephemeral=True
            )
            return

        quote = random.choice(self.mygo_quotes)
        await interaction.response.send_message(quote)

    async def handle_mygo_search(
        self, context: discord.Message | discord.Interaction, keyword: str
    ):
        """Handle MyGo image search with LLM fallback."""
        if not keyword:
            return

        # Defer interaction if it's one
        if isinstance(context, discord.Interaction):
            await context.response.defer(thinking=True)

        # Cooldown check
        bucket_key = (
            context.author if isinstance(context, discord.Message) else context.user
        )
        # Create a mock message for cooldown mapping
        bucket = self._cd.get_bucket(SimpleNamespace(author=bucket_key))
        retry_after = bucket.update_rate_limit()
        if retry_after:
            msg = (
                f"你問得太快了，AI 需要時間思考！請在 {retry_after:.2f} 秒後再試一次。"
            )
            if isinstance(context, discord.Interaction):
                await context.followup.send(msg, ephemeral=True)
            else:
                await context.reply(msg, delete_after=5)
            return

        # Helper to send messages
        async def send(content, **kwargs):
            if isinstance(context, discord.Interaction):
                await context.followup.send(content, **kwargs)
            else:
                await context.channel.send(content, **kwargs)

        async with aiohttp.ClientSession() as session:
            try:
                # --- 1. First attempt: Direct search ---
                api_url = f"https://mygoapi.miyago9267.com/mygo/img?keyword={keyword}"
                async with session.get(api_url) as response:
                    response.raise_for_status()
                    result = await response.json()

                if result.get("urls"):
                    image_url = random.choice(result["urls"])["url"]
                    await send(image_url)
                    return

                # --- If no direct match, proceed to LLM fallbacks ---
                if not self.model or not self.mygo_quotes:
                    return  # Can't do anything else

                # --- Typing indicator ---
                typing_context = context.channel
                async with typing_context.typing():
                    # --- 2. Second attempt: Find similar quote ---
                    await send("找不到完全符合的圖片，我試著找找看接近的台詞...")

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
                                    await send(
                                        f"我找到了這個，應該差不多吧？\n> {closest_quote}"
                                    )
                                    image_url_2 = random.choice(result_2["urls"])["url"]
                                    await send(image_url_2)
                                    return

                    # --- 3. Third attempt: Generate new sentence ---
                    await send("還是找不到相關圖片，讓我想想... 🤔")
                    prompt2 = f"「{keyword}」這句話聽起來像是 MyGO!!!!! 裡的哪個角色會說的台詞？請你扮演那個角色，並用該角色的口吻，生成一句全新的、風格相似的台詞。"
                    llm_response = await self.model.generate_content_async(prompt2)
                    await send(llm_response.text)

            except aiohttp.ClientError as e:
                print(f"呼叫 MyGo API 時發生網路錯誤: {e}")
                await send("抱歉，MyGo 圖庫好像連不上了，請稍後再試。")
            except Exception as e:
                print(f"處理 MyGo 搜尋時發生未預期錯誤: {e}")
                await send("處理你的請求時發生了一點問題... 😵")


async def setup(bot: commands.Bot):
    """Set up the MyGo cog."""
    await bot.add_cog(MyGo(bot))
