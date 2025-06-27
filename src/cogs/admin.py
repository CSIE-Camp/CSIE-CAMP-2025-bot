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
    檢查使用者是否具有管理員身份組。
    - 只有擁有 ADMIN_ROLE_ID 身份組的成員才擁有權限。
    - 如果未設定 ADMIN_ROLE_ID，則所有指令都無法使用。
    """
    admin_role_id = config.ADMIN_ROLE_ID
    if not admin_role_id:
        return False  # 未設定身份組

    if isinstance(interaction.user, discord.Member):
        return any(role.id == admin_role_id for role in interaction.user.roles)

    return False


class Admin(commands.Cog):
    """管理員專用指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager

    @app_commands.command(name="reload", description="[管理員] 重載指定的功能模組")
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

    @app_commands.command(name="status", description="[管理員] 顯示機器人運行狀態")
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
        description="[管理員] 重置所有用戶的彩蛋觸發狀態",
    )
    @app_commands.check(check_admin_permissions)
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

    @app_commands.command(
        name="reset_daily_data",
        description="[管理員] 重置所有用戶的每日簽到數據",
    )
    @app_commands.check(check_admin_permissions)
    async def reset_daily_data(self, interaction: discord.Interaction):
        """重置所有用戶的每日簽到數據"""
        await interaction.response.defer(thinking=True)
        count = 0
        for user_data in self.user_data.users.values():
            if user_data.get("last_sign_in"):
                user_data["last_sign_in"] = None
                count += 1
        # 直接保存所有更改
        await self.user_data.update_user_data(0, {})  # 觸發保存
        await interaction.followup.send(
            f"✅ 已重置 {count} 位用戶的每日簽到數據！所有用戶現在都可以重新簽到。",
            ephemeral=True,
        )

    @app_commands.command(
        name="announce_features",
        description="[管理員] 公告：公開功能介紹並 @everyone（管理員專用）",
    )
    @app_commands.check(check_admin_permissions)
    async def announce_features(self, interaction: discord.Interaction):
        """公告：公開功能介紹並 @everyone（管理員專用）"""
        await interaction.response.defer(ephemeral=True)

        # 取得所有伺服器
        guilds = self.bot.guilds

        # 對每個伺服器進行公告
        for guild in guilds:
            try:
                # 取得預設頻道
                channel = guild.system_channel

                if channel is not None:
                    # 發送公告訊息
                    await channel.send(
                        f"@everyone 我是你們的管理員機器人！以下是我的功能介紹：\n"
                        f"- **重載模組**：管理員可以使用 `/reload` 指令重載指定的功能模組。\n"
                        f"- **顯示狀態**：使用 `/status` 指令查看機器人當前狀態。\n"
                        f"- **重置彩蛋**：透過 `/reset_flags` 指令重置所有用戶的彩蛋觸發狀態。\n"
                        f"如需更多資訊，請聯繫伺服器管理員。",
                    )
            except Exception as e:
                print(f"無法在伺服器 {guild.name} 發送公告：{e}")

        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} 公告發送完成",
            description="已在所有伺服器的預設頻道發送功能介紹公告。",
            color=Colors.SUCCESS,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="user_info", description="[管理員] 查看指定用戶的詳細資料"
    )
    @app_commands.describe(user="要查看的用戶")
    @app_commands.check(check_admin_permissions)
    async def user_info(self, interaction: discord.Interaction, user: discord.Member):
        """查看用戶的詳細資料"""
        user_data = await self.user_data.get_user(user.id, user)
        embed = discord.Embed(
            title=f"👤 用戶詳細資料 - {user.display_name}", color=Colors.INFO
        )
        embed.add_field(name="用戶ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="等級", value=f"Lv.{user_data.get('lv', 1)}", inline=True)
        embed.add_field(name="經驗值", value=f"{user_data.get('exp', 0)}", inline=True)
        embed.add_field(
            name="金錢", value=f"{user_data.get('money', 0)} 元", inline=True
        )
        embed.add_field(
            name="債務", value=f"{user_data.get('debt', 0)} 次", inline=True
        )
        embed.add_field(
            name="連續簽到",
            value=f"{user_data.get('sign_in_streak', 0)} 天",
            inline=True,
        )
        embed.add_field(
            name="上次簽到", value=user_data.get("last_sign_in", "未簽到"), inline=True
        )
        embed.add_field(
            name="成就數量",
            value=f"{len(user_data.get('achievements', []))} 個",
            inline=True,
        )
        embed.add_field(
            name="彩蛋數量",
            value=f"{len(user_data.get('found_flags', []))} 個",
            inline=True,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="modify_money", description="[管理員] 修改用戶的金錢")
    @app_commands.describe(user="要修改的用戶", amount="金錢數量（可為負數）")
    @app_commands.check(check_admin_permissions)
    async def modify_money(
        self, interaction: discord.Interaction, user: discord.Member, amount: int
    ):
        """修改用戶的金錢"""
        user_data = await self.user_data.get_user(user.id, user)
        old_money = user_data.get("money", 0)
        user_data["money"] = max(0, old_money + amount)  # 確保金錢不會變成負數
        await self.user_data.update_user_data(user.id, user_data)
        action = "增加" if amount > 0 else "減少"
        await interaction.response.send_message(
            f"✅ 已為 {user.mention} {action} {abs(amount)} 元！\n"
            f"原有金錢: {old_money} 元 → 現有金錢: {user_data['money']} 元",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
