"""
風格轉換功能模組

提供多種角色風格的文字轉換功能：
- 自動檢測特定頻道的訊息
- 使用 AI 將訊息轉換為指定風格
- 透過 Webhook 以角色身份發送轉換後的訊息
- 包含冷卻時間機制防止濫用
"""

import discord
from discord.ext import commands
import aiohttp
from typing import Dict, Any
import datetime
from src.utils.user_data import user_data_manager

from src import config
from src.utils.prompt import STYLE_PROMPTS
from src.utils.llm import llm_model


class StyleTransfer(commands.Cog):
    """風格轉換功能處理器"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.model = llm_model

        # 冷卻時間：每個用戶 10 秒內最多 1 則訊息
        self._cooldown = commands.CooldownMapping.from_cooldown(
            1, 10.0, commands.BucketType.user
        )

        # 初始化風格映射配置
        self._init_style_config()

    def _init_style_config(self) -> None:
        """初始化風格轉換配置"""
        # 角色頭像配置
        avatars = {
            "wenyan": "https://i.meee.com.tw/0heQE1b.png",
            "catgirl": "https://i.meee.com.tw/IGfduzQ.png",
            "chuunibyou": "https://i.meee.com.tw/CAKQSUn.png",
            "tsundere": "https://i.meee.com.tw/9dNqy3N.png",
            "sakiko": "https://cdn.cybassets.com/media/W1siZiIsIjE2NzgwL3Byb2R1Y3RzLzU0NTkzNTY2LzE3NDI3NDgwMjBfYjI0ODdjZGIxMmQzYzEyMDI2OWMucG5nIl0sWyJwIiwidGh1bWIiLCIyMDQ4eDIwNDgiXV0.png?sha=af6e73a2db61f48c",
        }

        # 建立頻道到風格的映射
        self.style_mapping: Dict[int, Dict[str, Any]] = {}

        for style_key, style_config in config.STYLE_TRANSFER_CONFIG.items():
            channel_id = style_config["channel_id"]
            webhook_url = style_config["webhook_url"]

            # 只添加完整配置的風格
            if channel_id and webhook_url:
                self.style_mapping[channel_id] = {
                    "style_key": style_key,
                    "webhook_url": webhook_url,
                    "username": style_config["character"],
                    "avatar_url": avatars.get(style_key, ""),
                    "description": style_config["description"],
                }

        print(f"🎭 已載入 {len(self.style_mapping)} 個風格轉換配置")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """監聽訊息並處理風格轉換"""
        # 忽略機器人訊息
        if message.author.bot:
            return

        # 檢查是否為風格轉換頻道
        if message.channel.id not in self.style_mapping:
            return
        now = datetime.datetime.now()
        if  datetime.datetime(2025, 7, 1, 13, 30) < now < datetime.datetime(2025, 7, 1, 17, 30) or\
            datetime.datetime(2025, 7, 2,  9, 40) < now < datetime.datetime(2025, 7, 2, 12, 10) or\
            datetime.datetime(2025, 7, 2, 13, 30) < now < datetime.datetime(2025, 7, 2, 15,  0) or\
            datetime.datetime(2025, 7, 2, 15, 10) < now < datetime.datetime(2025, 7, 2, 17, 40) or\
            datetime.datetime(2025, 7, 3,  9, 40) < now < datetime.datetime(2025, 7, 3, 12, 10) or\
            datetime.datetime(2025, 7, 3, 13, 30) < now < datetime.datetime(2025, 7, 3, 15,  0):
            await message.channel.send('再不專心上課，我要生氣氣囉 ><\n你因為上課不專心不小心弄丟了 10 元')
            user_data = await user_data_manager.get_user(message.author.id, message.author)
            user_data["money"] -= 10
            if user_data["money"] < 0:
                user_data["money"] = 0
            await user_data_manager.update_user_data(message.author.id, user_data)
            return 
        
        # 檢查冷卻時間
        bucket = self._cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            # 直接刪除訊息，不發送任何警告
            try:
                await message.delete()
            except discord.Forbidden:
                pass  # 沒有刪除權限時忽略
            return

        await self._process_style_transfer(message)

    async def _process_style_transfer(self, message: discord.Message) -> None:
        """處理風格轉換邏輯"""
        if not self.model:
            print("❌ LLM 模型未初始化")
            return

        style_config = self.style_mapping[message.channel.id]
        style_key = style_config["style_key"]

        # 獲取風格提示詞
        prompt = STYLE_PROMPTS.get(style_key)
        if not prompt:
            print(f"❌ 找不到風格 {style_key} 的提示詞")
            return

        try:
            # 顯示機器人正在輸入的狀態
            async with message.channel.typing():
                await self._send_style_transfer_message(
                    message.content, style_config, prompt
                )

        except aiohttp.ClientError as e:
            print(f"❌ 網路請求失敗：{e}")
            # 發送錯誤訊息
            error_payload = {
                "content": "抱歉，處理你的訊息時出了點問題，請稍後再試～",
                "username": style_config["username"],
                "avatar_url": style_config["avatar_url"],
            }
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(style_config["webhook_url"], json=error_payload)
            except Exception:
                pass  # 忽略錯誤訊息發送失敗的情況
        except (ValueError, AttributeError, KeyError) as e:
            print(f"❌ 資料處理失敗：{e}")
            # 發送錯誤訊息
            error_payload = {
                "content": "抱歉，處理你的訊息時出了點問題，請稍後再試～",
                "username": style_config["username"],
                "avatar_url": style_config["avatar_url"],
            }
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(style_config["webhook_url"], json=error_payload)
            except Exception:
                pass  # 忽略錯誤訊息發送失敗的情況

    async def _send_style_transfer_message(
        self, original_content: str, style_config: Dict[str, Any], prompt: str
    ) -> None:
        """發送風格轉換後的訊息"""
        # 生成 AI 回應
        full_prompt = f"{prompt}\n\n用戶輸入：\n```{original_content}```"
        response = await self.model.generate_content_async(full_prompt)

        if not response.text or response.text.strip() == "":
            final_content = "🤔 我不知道該說什麼..."
        else:
            final_content = response.text

        # 直接發送最終訊息
        payload = {
            "content": final_content,
            "username": style_config["username"],
            "avatar_url": style_config["avatar_url"],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(style_config["webhook_url"], json=payload) as resp:
                if resp.status not in [200, 204]:
                    raise aiohttp.ClientError(f"Webhook 請求失敗：{resp.status}")


async def setup(bot: commands.Bot) -> None:
    """設置風格轉換 Cog"""
    await bot.add_cog(StyleTransfer(bot))
