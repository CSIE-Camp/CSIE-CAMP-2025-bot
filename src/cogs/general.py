"""
通用指令 Cog。

包含一些不屬於特定分類的常用指令，例如：
- 顯示連結
- 抽籤
- 查詢個人資料
"""

import discord
from discord.ext import commands
import random
import json
from typing import Optional

from src.utils.image_gen import generate_bytesIO
from src.utils.user_data import user_data_manager

from src.utils.mygo import get_mygo_imgs


class General(commands.Cog):
    """通用指令的集合。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 將資料檔案路徑改由 config 管理
        self.acg_quotes_path = "data/acg_quotes.json"
        self.acg_quotes = self._load_quotes()

    def _load_quotes(self):
        """從 JSON 檔案載入名言。"""
        try:
            with open(self.acg_quotes_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"錯誤：找不到名言檔案 '{self.acg_quotes_path}'")
            return []
        except json.JSONDecodeError:
            print(f"錯誤：無法解析名言檔案 '{self.acg_quotes_path}'")
            return []

    @commands.command(name="profile", aliases=["資料"])
    async def profile(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ):
        """查詢自己或指定成員的等級、經驗值和籌碼。"""
        # 如果沒有指定成員，則預設為指令使用者本人
        target_member = member or ctx.author

        async with ctx.typing():
            user_data = await user_data_manager.get_user(target_member.id)

            level = user_data.get("lv", 1)
            exp = user_data.get("exp", 0)
            money = user_data.get("money", 0)

            # 計算升級所需的經驗值
            required_exp = 10 * level

            # --- 建立進度條 ---
            progress = min(exp / required_exp, 1.0)  # 確保進度不超過 100%
            bar_length = 10  # 長條圖的長度
            filled_length = int(bar_length * progress)
            progress_bar = "🟩" * filled_length + "⬛" * (bar_length - filled_length)

            # --- 建立嵌入式訊息 ---
            embed = discord.Embed(
                title=f"✨ {target_member.display_name} 的個人資料",
                color=target_member.color,
            )
            embed.set_thumbnail(
                url=(
                    target_member.avatar.url
                    if target_member.avatar
                    else target_member.default_avatar.url
                )
            )

            embed.add_field(name="等級 (LV)", value=f"`{level}`", inline=True)
            embed.add_field(name="籌碼 (Money)", value=f"`💰 {money}`", inline=True)
            embed.add_field(
                name="經驗值 (EXP)",
                value=f"`{exp} / {required_exp}`\n{progress_bar} `({progress:.1%})`",
                inline=False,
            )

            embed.set_footer(text=f"由 {self.bot.user.name} 提供 | 使用 ?profile 查詢")

        await ctx.send(embed=embed)

    @commands.command()
    async def test_mg(self, ctx: commands.Context, keyword: str):
        """tt"""
        res = await get_mygo_imgs(keyword)
        print(res)

        await ctx.send(f"```json\n{res.__str__()}\n```")

    @commands.command()
    async def links(self, ctx: commands.Context):
        """顯示各種有用的連結。"""
        embed = discord.Embed(title="各種連結", color=discord.Color.blue())
        embed.add_field(
            name="範例程式碼與指令",
            value="https://github.com/CSIE-Camp/example-code-2025",
            inline=False,
        )
        embed.add_field(
            name="官方網站", value="https://camp.ntnucsie.info/", inline=False
        )
        embed.set_footer(text="NTNU CSIE Camp 2025")
        await ctx.send(embed=embed)

    @commands.command(name="draw", attrs=["抽籤"])
    async def draw_quote(self, ctx: commands.Context):
        """抽籤決定今日運勢，並附上一句動漫名言。"""
        if not self.acg_quotes:
            await ctx.send("抱歉，我找不到任何名言可以抽...看來是我的腦袋空空了。")
            return

        # --- 運勢計算 ---
        result = random.randint(1, 100)
        if result <= 1:
            content = "不可思議的傳說大吉！✨"
        elif result <= 3:
            content = "超級無敵大吉！🚀"
        elif result <= 5:
            content = "無敵大吉！🎉"
        elif result <= 10:
            content = "大吉！😄"
        elif result <= 30:
            content = "中吉！😊"
        elif result <= 50:
            content = "普通吉！🙂"
        elif result <= 70:
            content = "小吉！🤔"
        else:
            content = "迷你吉！🤏"

        # --- 名言處理 ---
        quote = random.choice(self.acg_quotes)
        # 進行關鍵字替換
        replacements = {
            "oooo": "寫黑客松",
            "ooo": "寫程式",
            "oo": "程式",
            "o": "卷",
            "xx": "Python",
        }
        for old, new in replacements.items():
            quote = quote.replace(old, new)

        # --- 圖片生成與訊息發送 ---
        async with ctx.typing():
            # 使用 image_gen 中的 generate_bytesIO
            buffer = await generate_bytesIO(prompt=quote)

            if buffer:
                file = discord.File(buffer, filename="fortune.png")
                embed = discord.Embed(title=content, color=discord.Color.green())
                embed.set_image(url="attachment://fortune.png")
                embed.set_footer(text=f"今日適合你的一句話：{quote}")
                await ctx.send(embed=embed, file=file)
            else:
                # 如果圖片生成失敗，則發送純文字版本
                await ctx.send(f"**{content}**\n今日適合你的一句話：{quote}")

    @commands.command(name="help", aliases=["幫助", "說明"])
    async def help_command(self, ctx: commands.Context):
        """顯示所有指令的說明。"""
        embed = discord.Embed(
            title="🤖 NTNU CSIE Camp 2025 機器人指令說明",
            description="這是有關本機器人所有功能的詳細說明！",
            color=discord.Color.purple(),
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="📖 一般指令",
            value="""
- **`?profile` / `?資料`**: 查詢自己或他人的個人資料。
- **`?links`**: 顯示營隊相關的實用連結。
- **`?draw` / `?抽籤`**: 每日抽籤，獲得運勢與動漫語錄。
- **`?schedule` / `?查詢課表`**: 查詢營隊課程表。
            """,
            inline=False,
        )

        embed.add_field(
            name="💰 遊戲與經濟系統",
            value="""
- **`?sign_in` / `?簽到`**: 每日簽到領取金錢。
- **`?slot <金額>` / `?拉霸 <金額>`**: 玩拉霸機試試手氣。
- **聊天升級**: 在伺服器中聊天即可獲得經驗值。
- **定時金錢活動**: 特定時間會出現特殊活動，把握機會賺錢！
            """,
            inline=False,
        )

        embed.add_field(
            name="🥚 彩蛋系統",
            value="""
- **`?egg` / `?彩蛋`**: 查看你已經收集到的彩蛋。
- **觸發彩蛋**: 在伺服器中輸入隱藏的關鍵字來尋找彩蛋！
            """,
            inline=False,
        )

        embed.add_field(
            name="🧠 AI 智慧功能",
            value="""
- **AI 聊天**: 在任何頻道 `@機器人` 即可與 AI 自由對話。
- **MyGo 專屬頻道**: 輸入關鍵字，自動搜尋 MyGo 角色圖片或生成 AI 台詞。
- **風格轉換頻道**: 在特定頻道發言，訊息會被轉換成文言文、貓娘、中二或傲嬌風格。
            """,
            inline=False,
        )

        embed.add_field(
            name="🛠️ 管理員指令",
            value="""
- **`?reload <cog>`**: 重新載入功能模組 (僅限 Bot 擁有者)。
- **`?reset_flags`**: 重設所有人的彩蛋狀態 (僅限管理員)。
            """,
            inline=False,
        )

        embed.set_footer(
            text=f"由 {self.bot.user.name} 提供 | <> 中的是必要參數，[] 中的是選用參數。"
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(General(bot))
