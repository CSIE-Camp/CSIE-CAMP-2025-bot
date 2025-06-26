"""
管理員功能模組

提供機器人管理和維護功能：
- Cog 模組管理（重載、載入）
- 用戶資料管理
- 系統狀態監控
- 彩蛋系統重置
"""

import discord
from discord.ext import commands

from src.utils.user_data import user_data_manager
from src.constants import Emojis, Colors


class Admin(commands.Cog):
    """管理員專用指令集合"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager

    def cog_check(self, ctx: commands.Context) -> bool:
        """檢查指令使用權限"""
        return ctx.author.guild_permissions.administrator

    @commands.command(name="reload", aliases=["重載"])
    @commands.is_owner()
    async def reload_cog(self, ctx: commands.Context, cog_name: str):
        """重載指定的功能模組"""
        await ctx.typing()

        extension_name = f"src.cogs.{cog_name.lower()}"

        try:
            # 嘗試重載模組
            await self.bot.reload_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組重載成功",
                description=f"模組 `{cog_name}` 已成功重載",
                color=Colors.SUCCESS,
            )
            await ctx.send(embed=embed)

        except commands.ExtensionNotLoaded:
            # 如果模組未載入，嘗試載入
            await self._load_new_extension(ctx, extension_name, cog_name)

        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(ctx, f"重載模組 `{cog_name}` 失敗", str(e))

    async def _load_new_extension(
        self, ctx: commands.Context, extension_name: str, cog_name: str
    ):
        """載入新的擴展模組"""
        try:
            await self.bot.load_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組載入成功",
                description=f"模組 `{cog_name}` 已成功載入",
                color=Colors.SUCCESS,
            )
            await ctx.send(embed=embed)
        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(ctx, f"載入模組 `{cog_name}` 失敗", str(e))

    async def _send_error_message(self, ctx: commands.Context, title: str, error: str):
        """發送錯誤訊息"""
        embed = discord.Embed(
            title=f"{Emojis.ERROR} {title}",
            description=f"```{error}```",
            color=Colors.ERROR,
        )
        await ctx.send(embed=embed)

    @commands.command(name="status", aliases=["狀態"])
    @commands.is_owner()
    async def status(self, ctx: commands.Context):
        """顯示機器人運行狀態"""
        embed = discord.Embed(title="🤖 機器人狀態", color=Colors.INFO)

        # 基本資訊
        embed.add_field(
            name="📊 基本資訊",
            value=f"延遲: `{round(self.bot.latency * 1000)}ms`\n"
            f"伺服器數: `{len(self.bot.guilds)}`\n"
            f"用戶數: `{len(self.bot.users)}`",
            inline=True,
        )

        # 載入的模組
        loaded_cogs = [cog for cog in self.bot.cogs.keys()]
        embed.add_field(
            name="🔧 載入的模組", value=f"```{', '.join(loaded_cogs)}```", inline=False
        )

        # 用戶資料統計
        user_count = len(self.user_data.users)
        embed.add_field(
            name="👥 用戶資料", value=f"註冊用戶: `{user_count}`", inline=True
        )

        await ctx.send(embed=embed)

    @commands.command(name="reset_flags", aliases=["重置彩蛋"])
    @commands.has_permissions(administrator=True)
    async def reset_flags(self, ctx: commands.Context):
        """重置所有用戶的彩蛋收集狀態"""
        await ctx.typing()

        # 確認操作
        confirm_embed = discord.Embed(
            title="⚠️ 確認重置",
            description="此操作將重置所有用戶的彩蛋收集狀態，是否繼續？",
            color=Colors.WARNING,
        )

        msg = await ctx.send(embed=confirm_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=check
            )

            if str(reaction.emoji) == "✅":
                await self._perform_flags_reset(ctx)
            else:
                await ctx.send("❌ 操作已取消")

        except TimeoutError:
            await ctx.send("⏰ 操作超時，已自動取消")

    async def _perform_flags_reset(self, ctx: commands.Context):
        """執行彩蛋重置操作"""
        reset_count = 0

        for user_id, user_data in self.user_data.users.items():
            if user_data.get("found_flags"):
                user_data["found_flags"] = []
                await self.user_data.update_user_data(int(user_id), user_data)
                reset_count += 1

        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} 彩蛋重置完成",
            description=f"已重置 {reset_count} 位用戶的彩蛋收集狀態",
            color=Colors.SUCCESS,
        )
        await ctx.send(embed=embed)

    @commands.command(name="scoreboard", aliases=["排行榜"])
    @commands.has_permissions(administrator=True)
    async def force_scoreboard_update(self, ctx: commands.Context):
        """手動觸發排行榜更新"""
        scoreboard_cog = self.bot.get_cog("Scoreboard")

        if not scoreboard_cog:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} 模組未載入",
                description="Scoreboard 模組未載入或不可用",
                color=Colors.ERROR,
            )
            await ctx.send(embed=embed)
            return

        try:
            # 重啟排行榜更新任務
            if hasattr(scoreboard_cog, "update_scoreboard"):
                scoreboard_cog.update_scoreboard.restart()

            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 排行榜更新",
                description="已手動觸發排行榜更新任務",
                color=Colors.SUCCESS,
            )
            await ctx.send(embed=embed)

        except (AttributeError, RuntimeError) as e:
            await self._send_error_message(ctx, "排行榜更新失敗", str(e))

    @commands.command(name="cogs", aliases=["模組列表"])
    @commands.is_owner()
    async def list_cogs(self, ctx: commands.Context):
        """列出所有可用的模組"""
        import os
        from src import config

        # 獲取已載入的模組
        loaded_cogs = set(self.bot.cogs.keys())

        # 獲取所有可用的模組
        available_cogs = set()
        if os.path.exists(config.COGS_DIR):
            for filename in os.listdir(config.COGS_DIR):
                if filename.endswith(".py") and not filename.startswith("__"):
                    available_cogs.add(filename[:-3].title())

        embed = discord.Embed(title="🔧 模組狀態", color=Colors.INFO)

        # 已載入的模組
        if loaded_cogs:
            embed.add_field(
                name="✅ 已載入模組",
                value="```" + ", ".join(sorted(loaded_cogs)) + "```",
                inline=False,
            )

        # 未載入的模組
        unloaded_cogs = available_cogs - loaded_cogs
        if unloaded_cogs:
            embed.add_field(
                name="❌ 未載入模組",
                value="```" + ", ".join(sorted(unloaded_cogs)) + "```",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """設置管理員 Cog"""
    await bot.add_cog(Admin(bot))
