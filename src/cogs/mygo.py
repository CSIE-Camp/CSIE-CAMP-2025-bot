"""
Cog for MyGo related commands.
"""

import discord
from discord.ext import commands
import aiohttp
import random

from src import config
from src.utils.llm import llm_model


class MyGo(commands.Cog):
    """Cog for MyGo related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages in the MyGo channel."""
        if message.author.bot:
            return

        if message.channel.id == config.MYGO_CHANNEL_ID:
            await self.handle_mygo_search(message)

    async def handle_mygo_search(self, message: discord.Message):
        """Handle MyGo image search."""
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


async def setup(bot: commands.Bot):
    """Set up the MyGo cog."""
    await bot.add_cog(MyGo(bot))
