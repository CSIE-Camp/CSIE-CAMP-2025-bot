"""
管理員功能模組

提供機器人管理和維護功能：
- Cog 模組管理（重載、載入）
- 用戶資料管理
- 系統狀態監控
- 彩蛋系統重置
"""

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.user_data import user_data_manager
from src.constants import Emojis, Colors
from src import config


async def check_admin_permissions(interaction: discord.Interaction) -> bool:
    """
    檢查使用者是否為機器人擁有者或具有管理員身份組。
    - 機器人擁有者始終擁有權限。
    - 如果設定了 ADMIN_ROLE_ID，則擁有該身份組的成員也擁有權限。
    """
    if await interaction.client.is_owner(interaction.user):
        return True

    admin_role_id = config.ADMIN_ROLE_ID
    if not admin_role_id:
        return False  # 未設定身份組，且非擁有者

    if isinstance(interaction.user, discord.Member):
        return any(role.id == admin_role_id for role in interaction.user.roles)

    return False


class Admin(commands.Cog):
    """管理員專用指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager

    @app_commands.command(name="reload", description="重載指定的功能模組")
    @app_commands.describe(cog_name="要重載的模組名稱")
    @app_commands.check(check_admin_permissions)
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str):
        """重載指定的 Cog"""
        await interaction.response.defer(ephemeral=True)

        extension_name = f"src.cogs.{cog_name.lower()}"

        try:
            # 嘗試重載模組
            await self.bot.reload_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組重載成功",
                description=f"模組 `{cog_name}` 已成功重載",
                color=Colors.SUCCESS,
            )
            await interaction.followup.send(embed=embed)

        except commands.ExtensionNotLoaded:
            # 如果模組未載入，嘗試載入
            await self._load_new_extension(interaction, extension_name, cog_name)

        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(
                interaction, f"重載模組 `{cog_name}` 失敗", str(e)
            )

    async def _load_new_extension(
        self, interaction: discord.Interaction, extension_name: str, cog_name: str
    ):
        """載入新的擴展模組"""
        try:
            await self.bot.load_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組載入成功",
                description=f"模組 `{cog_name}` 已成功載入",
                color=Colors.SUCCESS,
            )
            await interaction.followup.send(embed=embed)
        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(
                interaction, f"載入模組 `{cog_name}` 失敗", str(e)
            )

    async def _send_error_message(
        self, interaction: discord.Interaction, title: str, error: str
    ):
        """發送錯誤訊息"""
        embed = discord.Embed(
            title=f"{Emojis.ERROR} {title}",
            description=f"```{error}```",
            color=Colors.ERROR,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="status", description="顯示機器人運行狀態")
    @app_commands.check(check_admin_permissions)
    async def status(self, interaction: discord.Interaction):
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
            name="🔧 載入的模組",
            value=f"```\n{', '.join(loaded_cogs)}\n```",
            inline=False,
        )

        # 用戶資料統計
        user_count = len(self.user_data.users)
        embed.add_field(
            name="👥 用戶資料", value=f"已儲存 `{user_count}` 位用戶", inline=True
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="reset_flags",
        description="重置所有用戶的彩蛋觸發狀態",
    )
    @app_commands.default_permissions(administrator=True)
    async def reset_flags(self, interaction: discord.Interaction):
        """重置所有用戶的彩蛋旗標"""
        await interaction.response.defer()
        await self.user_data.reset_all_flags()
        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} 彩蛋狀態已重置",
            description="所有用戶的彩蛋觸發狀態都已清除。",
            color=Colors.SUCCESS,
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
