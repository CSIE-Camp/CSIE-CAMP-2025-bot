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
import json
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
    LINKS_FILE,
    Colors,
)
from src import config


class General(commands.Cog):
    """一般功能指令集合"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                self.link_list = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.link_list = []

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
        for link in self.link_list:
            embed.add_field(
                name=link["name"],
                value=link["value"],
                inline=False,
            )
        embed.set_footer(text="NTNU CSIE Camp 2025")
        await interaction.response.send_message(embed=embed)

    def _get_game_channel_mention(self):
        # 只取第一個允許遊戲的頻道
        if config.ALLOWED_GAME_CHANNEL_IDS:
            cid = config.ALLOWED_GAME_CHANNEL_IDS[0]
            return f"<#{cid}>"
        return "指定頻道"

    @commands.hybrid_command(name="help", description="顯示所有玩家可用功能與玩法說明")
    async def help(self, ctx: commands.Context):
        """顯示玩家可用功能與玩法說明（僅自己可見）"""
        game_channel_mention = self._get_game_channel_mention()
        # 取得頻道超連結
        game_channel_link = game_channel_mention
        if game_channel_mention.startswith("<#") and game_channel_mention.endswith(">"):
            channel_id = game_channel_mention[2:-1]
            game_channel_link = (
                f"[遊戲頻道](https://discord.com/channels/{ctx.guild.id}/{channel_id})"
            )

        # 風格轉換頻道連結
        style_channels = []
        style_channel_names = [
            ("文言文", getattr(config, "STYLE_TRANSFER_WENYAN_CHANNEL_ID", None)),
            ("貓娘", getattr(config, "STYLE_TRANSFER_CATGIRL_CHANNEL_ID", None)),
            ("中二", getattr(config, "STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID", None)),
            ("傲嬌", getattr(config, "STYLE_TRANSFER_TSUNDERE_CHANNEL_ID", None)),
            ("祥子", getattr(config, "STYLE_TRANSFER_SAKIKO_CHANNEL_ID", None)),
        ]
        for name, cid in style_channel_names:
            if cid:
                style_channels.append(
                    f"[{name}](https://discord.com/channels/{ctx.guild.id}/{cid})"
                )
        style_channels_str = "、".join(style_channels) if style_channels else "指定頻道"

        bot_name = self.bot.user.display_name if self.bot.user else "機器人"

        embed = discord.Embed(
            title="🎮 師大資工營 Discord Bot 玩家功能總覽",
            description="歡迎來到資工營！以下是你可以體驗的所有互動功能與玩法：\n\n"
            + "**所有指令皆可用 `/` 或觸發。**\n\n"
            + "如需查詢特定指令用法，請輸入 `/help <指令名稱>`。\n\n",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(),
        )
        # 一般功能
        embed.add_field(
            name="🎯 一般功能",
            value="""
/profile — 查詢你的等級、經驗值、金錢
/links — 營隊重要連結
/schedule — 查詢目前活動
/help — 顯示本說明
""",
            inline=False,
        )
        # 遊戲經濟
        embed.add_field(
            name="💰 遊戲與經濟",
            value=f"""
/checkin — 每日簽到抽運勢，獲得金錢、隨機引言與圖片
/scoreboard — 查看經驗值排行榜
/game slot <金額> — 拉霸遊戲
/game dice <金額> — 骰子比大小
/game rps <金額> <選項> — 剪刀石頭布
/game guess <金額> — 猜數字遊戲（互動按鈕）
> **遊戲頻道限制**：請在 {game_channel_link} 使用
""",
            inline=False,
        )
        # 成就與彩蛋
        embed.add_field(
            name="🏆 成就與彩蛋",
            value="""
/achievements — 查看你已解鎖的成就
/egg — 查詢你發現的彩蛋
> **彩蛋提示**：找到彩蛋後，直接在任何群組頻道輸入彩蛋內容即可觸發。
> 彩蛋格式為 `flag{||XXXX||}`，請將 `XXXX` 替換為你發現的彩蛋內容。
""",
            inline=False,
        )
        # MyGo
        embed.add_field(
            name="🎵 MyGo 專屬",
            value="""
/mygo <關鍵字> — 搜尋 MyGO!!!!! 圖片
/mygo_quote — 隨機 MyGO!!!!! 名言
""",
            inline=False,
        )
        # AI 互動
        embed.add_field(
            name="🤖 AI 互動",
            value=f"""
@{bot_name} — 直接提及即可與 AI (Gemini) 聊天
在特定風格頻道發言，訊息自動轉換角色風格：{style_channels_str}
""",
            inline=False,
        )
        embed.set_footer(
            text="NTNU CSIE Camp 2025",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_thumbnail(
            url="https://raw.githubusercontent.com/CSIE-Camp/camp-public-bot/main/assets/camp_logo.png"
        )
        # 僅自己可見
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
