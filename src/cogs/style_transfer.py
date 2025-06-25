"""
Cog for handling style transfer requests.
"""

import discord
from discord.ext import commands
import aiohttp

from src import config
from src.utils.prompt import STYLE_PROMPTS
from src.utils.llm import llm_model


class StyleTransfer(commands.Cog):
    """Cog for handling style transfer requests."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model
        # Cooldown: 1 message per 10 seconds per user
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 10.0, commands.BucketType.user
        )
        # 建立一個整合的 style map，方便管理
        self.style_map = {
            config.STYLE_TRANSFER_SAKIKO_CHANNEL_ID: {
                "prompt_key": "sakiko",
                "webhook_url": config.STYLE_TRANSFER_SAKIKO_WEBHOOK_URL,
                "username": "祥子",
                "avatar_url": "https://cdn.cybassets.com/media/W1siZiIsIjE2NzgwL3Byb2R1Y3RzLzU0NTkzNTY2LzE3NDI3NDgwMjBfYjI0ODdjZGIxMmQzYzEyMDI2OWMucG5nIl0sWyJwIiwidGh1bWIiLCIyMDQ4eDIwNDgiXV0.png?sha=af6e73a2db61f48c",
            },
            config.STYLE_TRANSFER_WENYAN_CHANNEL_ID: {
                "prompt_key": "wenyan",
                "webhook_url": config.STYLE_TRANSFER_WENYAN_WEBHOOK_URL,
                "username": "東漢書院諸葛亮",
                "avatar_url": "https://i.meee.com.tw/0heQE1b.png",
            },
            config.STYLE_TRANSFER_CATGIRL_CHANNEL_ID: {
                "prompt_key": "catgirl",
                "webhook_url": config.STYLE_TRANSFER_CATGIRL_WEBHOOK_URL,
                "username": "你的專屬貓娘",
                "avatar_url": "https://i.meee.com.tw/IGfduzQ.png",
            },
            config.STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID: {
                "prompt_key": "chuunibyou",
                "webhook_url": config.STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL,
                "username": "漆黑的墮天使",
                "avatar_url": "https://i.meee.com.tw/CAKQSUn.png",
            },
            config.STYLE_TRANSFER_TSUNDERE_CHANNEL_ID: {
                "prompt_key": "tsundere",
                "webhook_url": config.STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL,
                "username": "傲嬌大小姐",
                "avatar_url": "https://i.meee.com.tw/9dNqy3N.png",
            },
        }
        # 過濾掉未設定頻道的項目
        self.style_map = {k: v for k, v in self.style_map.items() if k is not None}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages in style transfer channels."""
        if message.author.bot:
            return

        if message.channel.id in self.style_map:
            # Check for cooldown
            bucket = self._cd.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                # We can't send a reply in the style transfer channel, so we send a DM
                try:
                    await message.author.send(
                        f"你在 **#{message.channel.name}** 的發言太快了，請在 {retry_after:.2f} 秒後再試一次。"
                    )
                except discord.Forbidden:
                    # If the user has DMs disabled, we can't do much.
                    pass
                # We still need to delete the original message to keep the channel clean
                await message.delete()
                return
            await self.handle_style_transfer(message)

    async def handle_style_transfer(self, message: discord.Message):
        """Handle the style transfer logic using Webhooks."""
        if not self.model:
            return

        style_info = self.style_map.get(message.channel.id)
        if not style_info:
            return

        webhook_url = style_info.get("webhook_url")
        if not webhook_url:
            print(f"錯誤：頻道 {message.channel.id} 的 Webhook URL 未設定。")
            # 可以在此發送一個提示訊息，但為避免洗版，暫時只在後台提示
            return

        prompt_key = style_info.get("prompt_key")
        prompt = STYLE_PROMPTS.get(prompt_key)
        if not prompt:
            return

        async with aiohttp.ClientSession() as session:
            try:
                # 產生 LLM 回應
                final_prompt = f"{prompt}\n\n使用者輸入：\n```{message.content}```"
                llm_response = await self.model.generate_content_async(final_prompt)

                # 透過 Webhook 發送訊息
                payload = {
                    "content": llm_response.text,
                    "username": style_info.get("username"),
                    "avatar_url": style_info.get("avatar_url"),
                }
                async with session.post(webhook_url, json=payload) as response:
                    if not response.ok:
                        print(f"使用 Webhook 發送訊息失敗: {response.status}")

            except Exception as e:
                print(f"處理風格轉換時發生錯誤: {e}")
                # 可以在此透過 Webhook 發送錯誤訊息
                error_payload = {
                    "content": "抱歉，轉換時出了點問題，請稍後再試。",
                    "username": style_info.get("username"),
                    "avatar_url": style_info.get("avatar_url"),
                }
                await session.post(webhook_url, json=error_payload)


async def setup(bot: commands.Bot):
    """Set up the StyleTransfer cog."""
    await bot.add_cog(StyleTransfer(bot))
