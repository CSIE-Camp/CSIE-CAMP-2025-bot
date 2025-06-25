"""
管理員專用指令 Cog。

包含一些只有機器人擁有者才能使用的指令，
例如設定頻道、重載 cogs 等。
"""

import discord
from discord.ext import commands
from src import config


class Admin(commands.Cog):
    """管理員相關指令的集合。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="set_reward_channel")
    @commands.is_owner()
    async def set_reward_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """設定發放限時獎勵的頻道。"""
        # 這是一個示範，實際上我們現在是從 .env 讀取
        # 但保留此指令可以方便在執行時動態修改
        config.REWARD_CHANNEL_ID = channel.id
        await ctx.send(f"限時獎勵頻道已設定為: {channel.mention}")

    @commands.command(name="reload")
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


async def setup(bot: commands.Bot):
    """設置函數，用於將此 Cog 加入到 bot 中。"""
    await bot.add_cog(Admin(bot))
