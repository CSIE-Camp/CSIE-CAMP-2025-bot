import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import json
from src.utils.llm import llm_model
from src.utils.achievements import AchievementManager

from src.constants import NOTES_FILE


class Notes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                self.notes_json = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.notes_json = dict()

    notes_group = app_commands.Group(name="note", description="查詢工程師們準備的筆記")

    @notes_group.command(name="list", description="顯示所有筆記名稱")
    @app_commands.describe(show_publicly="。如果選False，則僅你可見；如果選True，則頻道中其他人皆可見。")
    async def list_notes(self, interaction: discord.Interaction, show_publicly: bool = False):
        note_names = list(self.notes_json.keys())
        if len(note_names) == 0:
            await interaction.response.send_message("目前沒有任何筆記。", ephemeral=not show_publicly)
            return
        notes_list = "\n".join(f"- `{name}` — {self.notes_json[name]["ch_comment"]}" for name in note_names)
        embed = discord.Embed(
            title="筆記一覽",
            description=notes_list,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=not show_publicly)

    @notes_group.command(name="search", description="搜尋筆記")
    @app_commands.describe(keyword="筆記的搜尋關鍵詞", show_publicly="如果選False，則僅你可見；如果選True，則頻道中其他人皆可見。")
    async def search(self, interaction: discord.Interaction, keyword: str, show_publicly: bool = False):
        await interaction.response.defer(thinking=True)

        if self.notes_json.get(keyword):
            await interaction.followup.send(self.notes_json[keyword]["content"], ephemeral=not show_publicly)
            # 追蹤功能使用
            await AchievementManager.track_feature_usage(interaction.user.id, "note_search", interaction)
            return
        

        status_message = await interaction.followup.send(f"沒有找到名為「{keyword}」的筆記……", ephemeral=not show_publicly)

        note_names = list(self.notes_json.keys())
        
        # Helper to edit messages
        async def edit_message(message: discord.Message, content):
            if message is None:
                return
            try:
                await message.edit(content=content)
            except discord.HTTPException:
                pass  # Ignore edit failures


        # --- Typing indicator ---
        typing_context = interaction.channel
        async with typing_context.typing():
            # --- 2. Second attempt: Find similar note ---
            if status_message:
                await edit_message(
                    status_message,
                    f"試著根據「{keyword}」尋找接近的筆記...",
                )

            note_names_str = "\n".join(note_names)
            prompt = f"從下的筆記名稱中，選出與使用者輸入的「{keyword}」敘述最符合的一條筆記。請「只」回傳筆記名稱，不要包含任何其他文字或引號。\n\n筆記名稱：\n{note_names_str}\n\n此外此外提供筆記原始資料作為參照：\n```json\n{self.notes_json.__str__()}\n```"

            closest_name_response = await llm_model.generate_content_async(
                prompt
            )
            closest_name = closest_name_response.text.strip()

            if not self.notes_json.get(closest_name):
                interaction.followup.send("抱歉，現在頭腦有點燒機了…", ephemeral=not show_publicly)
                print(f"ERROR(src.cogs.notes): searching {closest_name} from {keyword} by LLM, but it's not in note list.")
                return

            await edit_message(
                status_message,
                f"根據「{keyword}」搜尋到了最接近的筆記：" 
            )
            await edit_message(
                status_message,
                self.notes_json[closest_name]["content"]
            )
            
            # 追蹤功能使用
            await AchievementManager.track_feature_usage(interaction.user.id, "note_search", interaction)
            # await interaction.followup.send(self.notes_json[closest_name]["content"], ephemeral=not show_publicly)
            return

async def setup(bot):
    await bot.add_cog(Notes(bot))