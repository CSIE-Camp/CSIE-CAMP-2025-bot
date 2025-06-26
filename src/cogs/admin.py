"""
管理員專用指令 Cog。

包含一些只有機器人擁有者才能使用的指令，
例如設定頻道、重載 cogs 等。
"""

from discord.ext import commands
import json
from src.utils.user_data import user_data_manager


class Admin(commands.Cog):
    """管理員相關指令的集合。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager
        self.flags_data = self.load_flags_data()

    def load_flags_data(self):
        with open("data/flags.json", "r", encoding="utf-8") as f:
            return json.load(f)

    @commands.command(name="reload", aliases=["重載"])
    @commands.is_owner()
    async def reload_cog(self, ctx: commands.Context, cog_name: str):
        """重載指定的 Cog 模組。"""
        extension_name = f"src.cogs.{cog_name.lower()}"
        try:
            await self.bot.reload_extension(extension_name)
            await ctx.send(f"✅ Cog '{cog_name}' 已成功重載。")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"⚠️ Cog '{cog_name}' 尚未載入，正在嘗試載入...")
            try:
                await self.bot.load_extension(extension_name)
                await ctx.send(f"✅ Cog '{cog_name}' 已成功載入。")
            except Exception as e:
                await ctx.send(f"❌ 載入 Cog '{cog_name}' 失敗: {e}")
        except Exception as e:
            await ctx.send(f"❌ 重載 Cog '{cog_name}' 失敗: {e}")

    @commands.command(name="reset_flags", aliases=["重置彩蛋"])
    @commands.has_permissions(administrator=True)
    async def reset_flags(self, ctx):
        """重置所有彩蛋的狀態。"""
        all_users = self.user_data.users
        for user_id, user_data in all_users.items():
            if "found_flags" in user_data:
                user_data["found_flags"] = []
                await self.user_data.update_user_data(int(user_id), user_data)

        await ctx.send("所有彩蛋都已重置。")

    @commands.command(name="scoreboard", aliases=["排行榜"])
    @commands.has_permissions(administrator=True)
    async def scoreboard(self, ctx: commands.Context):
        """手動更新排行榜訊息。"""
        scoreboard_cog = self.bot.get_cog("Scoreboard")
        if scoreboard_cog:
            scoreboard_cog.update_scoreboard.restart()
            await ctx.send("✅ 已手動觸發排行榜更新。")
        else:
            await ctx.send("❌ Scoreboard 功能未載入。")


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(Admin(bot))
