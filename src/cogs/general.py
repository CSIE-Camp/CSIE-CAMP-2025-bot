"""
一般功能模組

提供基礎的機器人功能：
- 用戶資料查詢
- 每日抽籤運勢
- 幫助指令
- 相關連結顯示
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import json
from typing import Optional, List
import datetime
import asyncio
from io import BytesIO

from src.utils.image_gen import generate_image
from src.utils.user_data import user_data_manager
from src.constants import (
    DEFAULT_LEVEL,
    DEFAULT_EXP,
    DEFAULT_MONEY,
    EXP_PER_LEVEL,
    PROGRESS_BAR_LENGTH,
    PROGRESS_BAR_FILLED,
    PROGRESS_BAR_EMPTY,
    FORTUNE_LEVELS,
    ACG_QUOTES_FILE,
    QUOTE_REPLACEMENTS,
    Colors,
)
from src import config


class General(commands.Cog):
    """一般功能指令集合"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.quotes: List[str] = self._load_quotes()

    def _load_quotes(self) -> List[str]:
        """載入動漫名言資料"""
        try:
            with open(ACG_QUOTES_FILE, "r", encoding="utf-8") as f:
                quotes = json.load(f)
                print(f"📚 已載入 {len(quotes)} 條名言")
                return quotes
        except FileNotFoundError:
            print(f"❌ 找不到名言檔案：{ACG_QUOTES_FILE}")
            return []
        except json.JSONDecodeError:
            print(f"❌ 名言檔案格式錯誤：{ACG_QUOTES_FILE}")
            return []

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

    @app_commands.command(name="draw", description="每日運勢抽籤")
    async def draw(self, interaction: discord.Interaction):
        """每日運勢抽籤"""
        await interaction.response.defer(thinking=True)

        user_data = await user_data_manager.get_user(interaction.user)
        today_str = datetime.date.today().isoformat()

        if user_data.get("last_draw_date") == today_str:
            await interaction.followup.send(
                "你今天已經抽過籤了，明天再來吧！", ephemeral=True
            )
            return

        fortune, color, quote = self._get_random_fortune()

        # 建立運勢嵌入訊息
        embed = discord.Embed(
            title="🔮 今日運勢", description=f"**{fortune}**", color=color
        )
        embed.add_field(name="💭 今日語錄", value=f"*{quote}*", inline=False)
        embed.set_footer(text=f"為 {interaction.user.display_name} 抽取")

        # 先更新用戶資料，避免因圖片生成失敗而沒有記錄今日抽籤
        user_data["last_draw_date"] = today_str
        await user_data_manager.update_user_data(interaction.user.id, user_data)

        # 嘗試生成圖片（添加超時保護）
        print(f"正在生成運勢圖片，引用語錄: {quote}")
        image_bytes = None
        try:
            # 添加超時限制，避免卡住太久

            image_bytes = await asyncio.wait_for(
                self._generate_fortune_image(quote), timeout=30.0
            )
        except asyncio.TimeoutError:
            print("⏰ 圖片生成超時，將只顯示文字版本")
        except (ConnectionError, ValueError, ImportError) as e:
            print(f"❌ 圖片生成失敗: {e}")

        # 根據圖片生成結果決定回傳方式
        if image_bytes:
            # 將圖片設置為 embed 的圖片
            file = discord.File(image_bytes, filename="fortune.png")
            embed.set_image(url="attachment://fortune.png")
            await interaction.followup.send(embed=embed, file=file)
        else:
            # 圖片生成失敗時，只顯示文字 embed
            await interaction.followup.send(embed=embed)

    def _get_random_fortune(self) -> tuple[str, int, str]:
        """隨機取得運勢和名言"""
        # 使用權重來選擇運勢
        weights = [weight for _, _, weight in FORTUNE_LEVELS]
        chosen_fortune = random.choices(FORTUNE_LEVELS, weights=weights, k=1)[0]
        fortune, color, _ = chosen_fortune

        # 隨機選擇一個名言並處理替換
        raw_quote = (
            random.choice(self.quotes) if self.quotes else "今天也要元氣滿滿喔！"
        )

        quote = raw_quote
        for old, new in QUOTE_REPLACEMENTS.items():
            quote = quote.replace(old, new)

        return fortune, color, quote

    async def _generate_fortune_image(self, quote: str) -> BytesIO | None:
        """生成運勢圖片"""
        # 如果沒有配置 HUGGINGFACE_TOKEN，則跳過圖片生成

        if not config.HUGGINGFACE_TOKEN:
            print("⚠️  未配置 HUGGINGFACE_TOKEN，跳過圖片生成")
            return None

        return await generate_image(quote)

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
            "🎯 一般功能": ["profile", "links", "draw", "schedule", "help"],
            "💰 遊戲經濟": [
                "sign_in",
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
