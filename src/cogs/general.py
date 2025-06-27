"""
一般功能模組

提供基礎的機器人功能：
- 用戶資料查詢
- 幫助指令
- 相關連結顯示
"""

import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional

from src.utils.user_data import user_data_manager
from src.constants import (
    DEFAULT_LEVEL,
    DEFAULT_EXP,
    DEFAULT_MONEY,
    EXP_PER_LEVEL,
    PROGRESS_BAR_LENGTH,
    PROGRESS_BAR_FILLED,
    PROGRESS_BAR_EMPTY,
    Colors,
)


class General(commands.Cog):
    """一般功能指令集合"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="profile", description="查詢用戶的等級、經驗值和金錢資料"
    )
    @app_commands.describe(member="要查詢的成員")
    async def profile(
        self, interaction: discord.Interaction, member: Optional[discord.Member] = None
    ):
        """查詢用戶的等級、經驗值和金錢資料"""
        target = member or interaction.user

        await interaction.response.defer(thinking=True)
        user_data = await user_data_manager.get_user(target)

        # 取得用戶資料
        level = user_data.get("lv", DEFAULT_LEVEL)
        exp = user_data.get("exp", DEFAULT_EXP)
        money = user_data.get("money", DEFAULT_MONEY)

        # 計算經驗值進度
        required_exp = self._calculate_required_exp(level)
        progress = min(exp / required_exp, 1.0)
        progress_bar = self._create_progress_bar(progress)

        # 建立資料嵌入
        embed = self._create_profile_embed(
            target, level, exp, required_exp, money, progress_bar
        )

        await interaction.followup.send(embed=embed)

    def _calculate_required_exp(self, level: int) -> int:
        """計算升級所需經驗值"""
        return EXP_PER_LEVEL * level

    def _create_progress_bar(
        self, progress: float, length: int = PROGRESS_BAR_LENGTH
    ) -> str:
        """建立經驗值進度條"""
        filled_length = int(length * progress)
        return PROGRESS_BAR_FILLED * filled_length + PROGRESS_BAR_EMPTY * (
            length - filled_length
        )

    def _create_profile_embed(
        self,
        user: discord.Member,
        level: int,
        exp: int,
        required_exp: int,
        money: int,
        progress_bar: str,
    ) -> discord.Embed:
        """建立個人資料的嵌入訊息"""
        embed = discord.Embed(
            title=f"✨ {user.display_name} 的個人資料",
            color=user.color,
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="**等級**", value=f"`{level}`", inline=True)
        embed.add_field(name="**金錢**", value=f"`{money}` 元", inline=True)
        embed.add_field(
            name="**經驗值**",
            value=f"`{exp} / {required_exp}`",
            inline=False,
        )
        embed.add_field(name="**進度**", value=f"`{progress_bar}`", inline=False)
        return embed

    @app_commands.command(name="links", description="顯示營隊相關連結")
    async def links(self, interaction: discord.Interaction):
        """顯示營隊相關連結"""
        embed = discord.Embed(
            title="🔗 營隊相關連結",
            description="以下是本次資工營的相關連結，歡迎多加利用！",
            color=Colors.INFO,
        )
        embed.add_field(
            name="<:github:1257997891954475079> GitHub",
            value="[https://github.com/CSIE-Camp/camp-public-bot](https://github.com/CSIE-Camp/camp-public-bot)",
            inline=False,
        )
        embed.add_field(
            name="<:ig:1257998497655689237> Instagram",
            value="[https://www.instagram.com/ntnu_csie_camp_2025/](https://www.instagram.com/ntnu_csie_camp_2025/)",
            inline=False,
        )
        embed.set_thumbnail(
            url="https://raw.githubusercontent.com/CSIE-Camp/camp-public-bot/main/assets/camp_logo.png"
        )
        embed.set_footer(text="NTNU CSIE Camp 2025")
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="help", description="顯示所有指令的說明")
    async def help(self, ctx: commands.Context):
        """顯示幫助訊息"""
        embed = discord.Embed(
            title="🤖 師大資工營 Discord Bot 指令大全",
            description="安安！我是師大資工營的專屬機器人，這裡是我會的所有指令！\n"
            "大部分指令都支援斜線 `/` 或前綴 `?` 來使用。\n"
            "若想查看特定指令的詳細用法，請使用 `/help <指令名稱>`。",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(),
        )

        # 從 cogs 中動態生成指令列表
        cogs = {
            "🎯 一般功能": ["profile", "links", "schedule", "help"],
            "💰 遊戲經濟": [
                "checkin",
                "scoreboard",
                "game slot",
                "game dice",
                "game rps",
                "game guess",
            ],
            "🏆 成就彩蛋": ["achievements", "egg"],
            "🎵 MyGo 專屬": ["mygo", "quote"],
            "🛠️ 管理功能": ["reload", "status", "reset_flags", "cogs", "set_schedule"],
        }

        for category, command_list in cogs.items():
            command_descriptions = []
            for cmd_name in command_list:
                # 從機器人找到指令物件
                cmd = self.bot.get_command(cmd_name)
                if cmd:
                    # 優先使用 description，若無則使用 help
                    description = cmd.description or cmd.help or "沒有說明"
                    # 格式化指令，只顯示斜線用法
                    command_descriptions.append(f"🔹 **/{cmd.name}**: {description}")
                else:
                    command_descriptions.append(f"🔹 **/{cmd_name}**: *指令不存在*")

            if command_descriptions:
                embed.add_field(
                    name=f"**{category}**",
                    value="\n".join(command_descriptions),
                    inline=False,
                )

        # 新增自動功能的說明
        embed.add_field(
            name="✨ 自動功能 (無須指令)",
            value="除了指令外，我還有一些酷酷的自動功能：\n"
            "- **經驗與金錢**: 在任何頻道發言（指令除外）都能獲得經驗值和金錢，還可能觸發隨機事件！\n"
            "- **AI 智慧聊天**: 直接**提及 (mention)** 我 (`@NTNU CSIE Camp Bot`) 就可以跟我聊天。\n"
            "- **角色風格轉換**: 在特定的風格轉換頻道發言，訊息會自動變成該角色的風格。\n"
            "- **彩蛋系統**: 在任何地方輸入隱藏的「彩蛋關鍵字」來發現驚喜！",
            inline=False,
        )

        embed.set_footer(
            text="NTNU CSIE Camp 2025",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_thumbnail(
            url="https://raw.githubusercontent.com/CSIE-Camp/camp-public-bot/main/assets/camp_logo.png"
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
