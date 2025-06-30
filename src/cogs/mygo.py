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
from datetime import datetime

from src.utils.prompt import MYGO_QUOTE_SIMILAR_PROMPT, MYGO_CHARACTER_GEN_PROMPT
from src import config
from src.utils.llm import llm_model
from src.constants import MYGO_FILE
import io
from datetime import datetime
from src.utils.achievements import AchievementManager
from src.utils.user_data import user_data_manager


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

    @app_commands.command(name="mygo", description="從 MyGO!!!!! 和 ave-mujica 圖庫中搜尋一張圖片。")
    @app_commands.describe(keyword="要搜尋的台詞或關鍵字")
    async def mygo_slash(self, interaction: discord.Interaction, keyword: str):
        """Searches for a MyGo image."""
        await self.handle_mygo_search(interaction, keyword)
        
        user = user_data_manager.get_user(interaction.user.id)
        mygo_date = user.get("mygo_search_date", datetime.now().date())
        mygo_times = user.get("today_mygo_search_times", 0)
        if mygo_date != datetime.now().date():
            # Reset daily search count if it's a new day
            user["mygo_search_date"] = datetime.now().date()
            user["today_mygo_search_times"] = 1
            mygo_times = 1
        if mygo_times == 10:
            await AchievementManager.check_and_award_achievement(
                interaction.user.id, "mygo_good", self.bot
            )
        elif mygo_times == 25:
            await AchievementManager.check_and_award_achievement(
                interaction.user.id, "mygo_love", self.bot
            )
        elif mygo_times == 50:
            await AchievementManager.check_and_award_achievement(
                interaction.user.id, "mygo_fan", self.bot
            )
        
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(interaction.user.id, "mygo", self.bot)


    @app_commands.command(name="quote", description=f"隨機取得一句和 MyGo/ave-mujica 經典台詞")
    async def quote(self, interaction: discord.Interaction):
        """隨機回傳一個 MyGo 的名言"""
        try:
            if not self.mygo_quotes:
                await interaction.response.send_message(
                    "抱歉，我找不到任何 MyGo/ave-mujica 的名言。", ephemeral=True
                )
                return

            quote = random.choice(self.mygo_quotes)
            await interaction.response.send_message(f"💭 {quote}")
        except Exception as e:
            print(f"Quote 命令錯誤: {e}")
            await interaction.response.send_message(
                "抱歉，取得名言時發生錯誤。", ephemeral=True
            )

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

        # Helper to send messages and return the message object
        async def send(content, **kwargs):
            if isinstance(context, discord.Interaction):
                return await context.followup.send(content, **kwargs)
            else:
                return await context.channel.send(content, **kwargs)

        # Helper to edit messages
        async def edit_message(message, content):
            if message is None:
                return
            try:
                await message.edit(content=content)
            except discord.HTTPException:
                pass  # Ignore edit failures

        # Track the status message for editing
        status_message = None

        try:
            # --- 1. First attempt: Direct search in local JSON ---
            matches = [
                item for item in self.mygo_quotes
                if isinstance(item, dict) and keyword in item.get("alt", "")
            ]
            if matches:
                index = random.randint(0,len(matches))
                image_url = matches[index]['url']
                image_alt = matches[index]['alt']
                if 'ave-mujica' in image_url:
                    async with aiohttp.ClientSession() as sess:
                        async with sess.get(image_url) as resp:
                            if resp.status != 200:
                                return await send('讀取失敗')
                            data = await resp.read()
                    random_color = random.randint(0, 0xFFFFFF)
                    file = discord.File(fp=io.BytesIO(data), filename="image.webp")
                    embed = discord.Embed(description=image_alt, color=random_color, timestamp=datetime.now())
                    embed.set_image(url="attachment://image.webp")
                    embed.set_footer(text="ave-mujica 廚 in.")
                    await send('從最相關的多張圖片中隨機選擇一張',embed=embed, file=file)
                    return
                else:
                    random_color = random.randint(0, 0xFFFFFF)
                    embed = discord.Embed(description=image_alt, color=random_color, timestamp=datetime.now())
                    embed.set_image(url=image_url)
                    embed.set_footer(text="mygo 廚 in.")
                    await send('我找找喔，你是說這張對吧',embed=embed)
                    return

            # --- If no direct match, show searching message and proceed to LLM fallbacks ---
            status_message = await send(
                f"我沒找到包含{keyword}這段話的圖片誒，還是你是說這張呢？"
            )

            if not self.model or not self.mygo_quotes:
                if status_message:
                    await edit_message(
                        status_message, f"找不到「{keyword}」的相關圖片... 😵"
                    )
                return  # Can't do anything else
            
             # --- 2. Second attempt: Find similar quote using LLM ---
            typing_context = context.channel
            async with typing_context.typing():
                if status_message:
                    await edit_message(
                        status_message,
                        f"試著找找看與「{keyword}」接近的台詞...",
                    )

                quotes_str = "\n".join(
                    item["alt"] for item in self.mygo_quotes if isinstance(item, dict) and "alt" in item
                )
                prompt1 = f"從以下《MyGO!!!!!》以及《ave-mujica》的台詞列表中，選出與使用者輸入的「{keyword}」語意最接近或最相關的一句台詞。請「只」回傳那句台詞，不要包含任何其他文字或引號。\n\n台詞列表：\n{quotes_str}"

                closest_quote_response = await self.model.generate_content_async(
                    prompt1
                )
                closest_quote = closest_quote_response.text.strip()

                if closest_quote:
                    matches2 = [
                        item for item in self.mygo_quotes
                        if isinstance(item, dict) and closest_quote in item.get("alt", "")
                    ]
                    if matches2:
                        if status_message:
                            await edit_message(
                                status_message,
                                f"沒有找到「{keyword}」，但我找到了這個，應該差不多吧？\n> {closest_quote}",
                            )
                        image_url_2 = random.choice(matches2)["url"]
                        await send(image_url_2)
                        return

                    # --- 3. Third attempt: Generate new sentence ---
                if status_message:
                    await edit_message(
                        status_message,
                        f"還是找不到「{keyword}」的相關圖片，讓我想想... 🤔",
                    )
                prompt2 = f"「{keyword}」這句話聽起來像是 MyGO!!!!!/ave-mujica 裡的哪個角色會說的台詞？請你扮演那個角色，並用該角色的口吻，生成一句全新的、風格相似的台詞。"
                llm_response = await self.model.generate_content_async(prompt2)
                if status_message:
                    await edit_message(
                        status_message,
                        f"雖然找不到「{keyword}」的圖片，但讓我想到了這個...",
                    )
                await send(llm_response.text)

        except Exception as e:
            print(f"處理 MyGo/ave-mujica 搜尋時發生未預期錯誤: {e}")
            if status_message:
                await edit_message(
                    status_message,
                    f"處理「{keyword}」的搜尋請求時發生了一點問題... 😵",
                )
            else:
                await send("處理你的請求時發生了一點問題... 😵")


async def setup(bot: commands.Bot):
    """Set up the MyGo cog."""
    await bot.add_cog(MyGo(bot))
