import discord
from discord import app_commands
from discord.ext import commands

from src.utils.user_data import user_data_manager
from src.constants import Emojis, Colors
from src import config


class Admin(commands.Cog):
    @app_commands.command(
        name="scoreboard",
        description="[管理員] 強制立即更新排行榜 (Scoreboard)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def scoreboard(self, interaction: discord.Interaction):
        """強制立即更新排行榜"""
        await interaction.response.defer(ephemeral=True)
        scoreboard_cog = self.bot.get_cog("Scoreboard")
        if scoreboard_cog:
            await scoreboard_cog.update_scoreboard()
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 排行榜已強制更新",
                description="排行榜已立即更新。",
                color=Colors.SUCCESS,
            )
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} 找不到 Scoreboard 模組",
                description="請確認 Scoreboard cog 是否已正確載入。",
                color=Colors.ERROR,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager

    @app_commands.command(
        name="reload",
        description="[管理員] 重載指定的功能模組",
    )
    @app_commands.describe(cog_name="要重載的模組名稱")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str):
        """重載指定的 Cog"""
        await interaction.response.defer(ephemeral=True)

        extension_name = f"src.cogs.{cog_name.lower()}"
        try:
            await self.bot.reload_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組重載成功",
                description=f"模組 `{cog_name}` 已成功重載",
                color=Colors.SUCCESS,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except commands.ExtensionNotLoaded:
            await self._load_new_extension(interaction, extension_name, cog_name)
        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(
                interaction, f"重載模組 `{cog_name}` 失敗", str(e)
            )

    async def _load_new_extension(
        self, interaction: discord.Interaction, extension_name: str, cog_name: str
    ):
        try:
            await self.bot.load_extension(extension_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 模組載入成功",
                description=f"模組 `{cog_name}` 已成功載入",
                color=Colors.SUCCESS,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except (commands.ExtensionError, ImportError) as e:
            await self._send_error_message(
                interaction, f"載入模組 `{cog_name}` 失敗", str(e)
            )

    async def _send_error_message(
        self, interaction: discord.Interaction, title: str, error: str
    ):
        embed = discord.Embed(
            title=f"{Emojis.ERROR} {title}",
            description=f"```{error}```",
            color=Colors.ERROR,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="status",
        description="[管理員] 顯示機器人運行狀態",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def status(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 機器人狀態", color=Colors.INFO)

        embed.add_field(
            name="📊 基本資訊",
            value=(
                f"延遲: `{round(self.bot.latency * 1000)}ms`\n"
                f"伺服器數: `{len(self.bot.guilds)}`\n"
                f"用戶數: `{len(self.bot.users)}`"
            ),
            inline=True,
        )

        loaded_cogs = list(self.bot.cogs.keys())
        embed.add_field(
            name="🔧 載入的模組",
            value=f"{', '.join(loaded_cogs)}",
            inline=False,
        )

        user_count = len(self.user_data.users)
        embed.add_field(
            name="👥 用戶資料",
            value=f"已儲存 `{user_count}` 位用戶",
            inline=True,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="reset_flags",
        description="[管理員] 重置所有用戶的彩蛋觸發狀態",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def reset_flags(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.user_data.reset_all_flags()
        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} 彩蛋狀態已重置",
            description="所有用戶的彩蛋觸發狀態都已清除。",
            color=Colors.SUCCESS,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="reset_daily_data",
        description="[管理員] 重置所有用戶的每日簽到數據",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def reset_daily_data(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        count = 0
        for user_data in self.user_data.users.values():
            if user_data.get("last_sign_in"):
                user_data["last_sign_in"] = None
                count += 1
        await self.user_data.update_user_data(0, {})
        await interaction.followup.send(
            f"✅ 已重置 {count} 位用戶的每日簽到數據！所有用戶現在都可以重新簽到。",
            ephemeral=True,
        )

    @app_commands.command(
        name="announce",
        description="[管理員] 發送自訂公告到公告頻道 (@everyone)",
    )
    @app_commands.describe(message="要公告的內容")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def announce(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        channel_id = getattr(config, "ANNOUNCEMENT_CHANNEL_ID", None)
        channel = self.bot.get_channel(channel_id) if channel_id else None
        if channel:
            await channel.send(message)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 公告已發送",
                description="已在公告頻道發送訊息。",
                color=Colors.SUCCESS,
            )
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} 找不到公告頻道",
                description="請確認 ANNOUNCEMENT_CHANNEL_ID 是否正確設定。",
                color=Colors.ERROR,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="announce_features",
        description="[管理員] 公告：公開功能介紹並 @everyone（管理員專用）",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def announce_features(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        intro_message = (
            "@everyone 嗨大家好！我是你們的營隊小幫手「大傢伙」 🤖\n\n"
            "很高興在 NTNU CSIE Camp 2025 跟大家見面！\n\n"
            "✨ **我能幫你做什麼？**\n"
            "- 每天簽到賺經驗，累積成就，還有機會發現隱藏彩蛋！\n"
            "- 和大家一起玩小遊戲、互動聊天，讓營隊生活更有趣。\n"
            "- 查詢自己的等級、金錢、成就、彩蛋收集進度等。\n"
            "- 更多功能和驚喜，請直接輸入 `/` 查看所有指令！\n\n"
            "💡 **小提醒**\n"
            "- 有任何問題或建議，歡迎隨時 @管理員 或私訊我們！\n"
            "- 如果你發現有趣的彩蛋，記得和朋友分享哦！\n\n"
            "祝大家在營隊玩得開心、交到好朋友，也別忘了每天來找我玩！🎉\n"
            "— 你的 Discord 小夥伴 大傢伙"
        )
        channel_id = getattr(config, "ANNOUNCEMENT_CHANNEL_ID", None)
        channel = self.bot.get_channel(channel_id) if channel_id else None
        if channel:
            await channel.send(intro_message)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} 公告發送完成",
                description="已在公告頻道發送自我介紹。",
                color=Colors.SUCCESS,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} 找不到公告頻道",
                description="請確認 ANNOUNCEMENT_CHANNEL_ID 是否正確設定。",
                color=Colors.ERROR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="user_info", description="[管理員] 查看指定用戶的詳細資料"
    )
    @app_commands.describe(user="要查看的用戶")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def user_info(self, interaction: discord.Interaction, user: discord.Member):
        user_data = await self.user_data.get_user(user.id, user)
        embed = discord.Embed(
            title=f"👤 用戶詳細資料 - {user.display_name}",
            color=Colors.INFO,
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
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(
        discord.Permissions(administrator=True), manage_messages=True
    )
    async def modify_money(
        self, interaction: discord.Interaction, user: discord.Member, amount: int
    ):
        user_data = await self.user_data.get_user(user.id, user)
        old_money = user_data.get("money", 0)
        user_data["money"] = max(0, old_money + amount)
        await self.user_data.update_user_data(user.id, user_data)
        action = "增加" if amount > 0 else "減少"
        await interaction.response.send_message(
            f"✅ 已為 {user.mention} {action} {abs(amount)} 元！\n"
            f"原有金錢: {old_money} 元 → 現有金錢: {user_data['money']} 元",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ 需要管理員權限才能執行。", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
