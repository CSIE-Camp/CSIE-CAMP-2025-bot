"""
一般功能模組

提供基礎的機器人功能：
- 用戶資料查詢
- 每日抽籤運勢
- 幫助指令
- 相關連結顯示
"""

import discord
from discord.ext import commands
import random
import json
from typing import Optional, List, Dict, Any

from src.utils.image_gen import generate_bytesIO
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
    QUOTE_REPLACEMENTS,
    ACG_QUOTES_FILE,
    Colors,
)


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

    @commands.command(name="profile", aliases=["資料"])
    async def profile(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ):
        """查詢用戶的等級、經驗值和金錢資料"""
        target = member or ctx.author

        async with ctx.typing():
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
                target, level, exp, required_exp, money, progress_bar, progress
            )

        await ctx.send(embed=embed)

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
        progress: float,
    ) -> discord.Embed:
        """建立用戶資料嵌入訊息"""
        embed = discord.Embed(
            title=f"✨ {user.display_name} 的個人資料",
            color=user.color or Colors.INFO,
        )

        # 設定縮圖
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_thumbnail(url=avatar_url)

        # 添加欄位
        embed.add_field(name="🏆 等級", value=f"`{level}`", inline=True)
        embed.add_field(name="💰 金錢", value=f"`{money:,}`", inline=True)
        embed.add_field(
            name="⭐ 經驗值",
            value=f"`{exp:,} / {required_exp:,}`\n{progress_bar} `({progress:.1%})`",
            inline=False,
        )

        embed.set_footer(text=f"數據由 {self.bot.user.name} 提供")
        return embed

    @commands.command(name="links")
    async def links(self, ctx: commands.Context):
        """顯示營隊相關連結"""
        embed = discord.Embed(
            title="🔗 營隊相關連結",
            color=Colors.INFO,
            description="以下是一些實用的營隊相關連結",
        )

        links_data = [
            ("📋 範例程式碼與指令", "https://github.com/CSIE-Camp/example-code-2025"),
            ("🏠 官方網站", "https://camp.ntnucsie.info/"),
        ]

        for name, url in links_data:
            embed.add_field(name=name, value=url, inline=False)

        embed.set_footer(text="NTNU CSIE Camp 2025")
        await ctx.send(embed=embed)

    @commands.command(name="draw", aliases=["抽籤"])
    async def draw_fortune(self, ctx: commands.Context):
        """每日抽籤，獲得運勢和動漫名言"""
        if not self.quotes:
            await ctx.send("😅 抱歉，名言庫暫時無法使用，請稍後再試")
            return

        # 生成運勢
        fortune_text = self._generate_fortune()

        # 選擇並處理名言
        quote = self._process_quote(random.choice(self.quotes))

        await self._send_fortune_message(ctx, fortune_text, quote)

    def _generate_fortune(self) -> str:
        """生成運勢結果"""
        result = random.randint(1, 100)
        for threshold, text in FORTUNE_LEVELS:
            if result <= threshold:
                return text
        return "🤏 迷你吉！"

    def _process_quote(self, quote: str) -> str:
        """處理名言中的關鍵字替換"""
        for old, new in QUOTE_REPLACEMENTS.items():
            quote = quote.replace(old, new)
        return quote

    async def _send_fortune_message(
        self, ctx: commands.Context, fortune: str, quote: str
    ):
        """發送運勢訊息（包含圖片）"""
        async with ctx.typing():
            # 嘗試生成運勢圖片
            image_buffer = await generate_bytesIO(prompt=quote)

            embed = discord.Embed(title=fortune, color=Colors.SUCCESS)
            embed.set_footer(text=f"今日適合你的一句話：{quote}")

            if image_buffer:
                file = discord.File(image_buffer, filename="fortune.png")
                embed.set_image(url="attachment://fortune.png")
                await ctx.send(embed=embed, file=file)
            else:
                # 圖片生成失敗時發送純文字
                embed.add_field(name="📝 今日名言", value=f"*{quote}*", inline=False)
                await ctx.send(embed=embed)

    @commands.command(name="help", aliases=["幫助", "說明"])
    async def help_command(self, ctx: commands.Context):
        """顯示機器人功能說明"""
        embed = discord.Embed(
            title="🤖 NTNU CSIE Camp 2025 機器人",
            description="歡迎使用營隊機器人！以下是所有可用功能：",
            color=Colors.PRIMARY,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # 功能分類
        help_sections = [
            (
                "📖 一般功能",
                [
                    "`?profile` / `?資料` - 查詢個人資料",
                    "`?links` - 顯示營隊相關連結",
                    "`?draw` / `?抽籤` - 每日運勢抽籤",
                    "`?schedule` / `?查詢課表` - 查詢課程表",
                ],
            ),
            (
                "💰 遊戲經濟",
                [
                    "`?sign_in` / `?簽到` - 每日簽到領金錢",
                    "`?slot <金額>` / `?拉霸 <金額>` - 拉霸遊戲",
                    "💬 聊天升級 - 發言獲得經驗值",
                    "⏰ 定時活動 - 特定時間的金錢活動",
                ],
            ),
            (
                "🥚 收集系統",
                [
                    "`?egg` / `?彩蛋` - 查看收集的彩蛋",
                    "🔍 彩蛋探索 - 輸入特殊關鍵字尋找彩蛋",
                ],
            ),
            (
                "🎭 AI 功能",
                [
                    "@機器人 - 與 AI 自由對話",
                    "🎭 MyGo 頻道 - 角色圖片搜尋和對話",
                    "✨ 風格轉換 - 多種角色風格轉換",
                ],
            ),
            (
                "🛠️ 管理員功能",
                [
                    "`?reload <模組>` / `?重載 <模組>` - 重載指定模組",
                    "`?status` / `?狀態` - 顯示機器人運行狀態",
                    "`?reset_flags` / `?重置彩蛋` - 重置所有用戶彩蛋",
                    "`?scoreboard` / `?排行榜` - 手動更新排行榜",
                    "`?cogs` / `?模組列表` - 列出所有可用模組",
                ],
            ),
        ]

        for section_name, commands_list in help_sections:
            commands_text = "\n".join(f"• {cmd}" for cmd in commands_list)
            embed.add_field(name=section_name, value=commands_text, inline=False)

        embed.set_footer(text=f"由 {self.bot.user.name} 提供服務")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """設置 Cog"""
    await bot.add_cog(General(bot))
