"""
Cog for handling style transfer requests.
"""

import discord
from discord.ext import commands

from src import config
from src.utils.prompt import STYLE_PROMPTS
from src.utils.llm import llm_model


class StyleTransfer(commands.Cog):
    """Cog for handling style transfer requests."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model
        self.style_channel_map = {
            config.STYLE_TRANSFER_WENYAN_CHANNEL_ID: "wenyan",
            config.STYLE_TRANSFER_CATGIRL_CHANNEL_ID: "catgirl",
            config.STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID: "chuunibyou",
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages in style transfer channels."""
        if message.author.bot:
            return

        if message.channel.id in self.style_channel_map:
            await self.handle_style_transfer(message)

    async def handle_style_transfer(self, message: discord.Message):
        """Handle the style transfer logic."""
        if not self.model:
            return

        style_name = self.style_channel_map.get(message.channel.id)
        if not style_name:
            return

        prompt = STYLE_PROMPTS.get(style_name)
        if not prompt:
            return

        async with message.channel.typing():
            try:
                # The prompt already contains the system instruction for the style.
                # The user's message is the final part of the content.
                final_prompt = f"{prompt}\n\n使用者輸入：\n```{message.content}```"
                llm_response = await self.model.generate_content_async(final_prompt)
                await message.channel.send(llm_response.text)
            except Exception as e:
                print(f"處理風格轉換時發生錯誤: {e}")
                await message.channel.send("抱歉，轉換時出了點問題，請稍後再試。")


async def setup(bot: commands.Bot):
    """Set up the StyleTransfer cog."""
    await bot.add_cog(StyleTransfer(bot))
