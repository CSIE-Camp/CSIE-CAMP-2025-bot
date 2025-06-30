import discord
from discord import app_commands
from discord.ext import commands
from src.utils.achievements import AchievementManager, ACHIEVEMENTS
from src.utils.user_data import user_data_manager
from typing import Optional


class AchievementCog(commands.Cog):
    """成就相關指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="achievements", description="顯示你或指定用戶的成就")
    @app_commands.describe(user="要查詢的用戶")
    async def show_achievements(
        self, interaction: discord.Interaction, user: Optional[discord.Member] = None
    ):
        """顯示成就列表"""
        target_user = user or interaction.user
        user_achievements = await AchievementManager.get_user_achievements(
            target_user.id
        )

        # 創建嵌入式訊息
        embed = discord.Embed(
            title=f"🏆 {target_user.display_name} 的成就",
            color=0x00FF00 if user_achievements else 0x808080,
        )

        if user_achievements:
            # 顯示已獲得的成就
            achieved_text = ""
            for achievement in user_achievements:
                achieved_text += f"{achievement.icon} **{achievement.name}**\n{achievement.description}\n\n"

            embed.add_field(
                name=f"已獲得成就 ({len(user_achievements)}/{len(ACHIEVEMENTS)})",
                value=achieved_text,
                inline=False,
            )
        else:
            embed.add_field(
                name="尚未獲得任何成就",
                value="開始遊戲來獲得你的第一個成就吧！",
                inline=False,
            )

        # 顯示未獲得的成就（作為提示）
        user = await user_data_manager.get_user(target_user.id)

        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        embed.set_footer(text="繼續努力解鎖更多成就吧！")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(interaction.user.id, "achievements", interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementCog(bot))
