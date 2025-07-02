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
from src.utils.achievements import AchievementManager
from src.utils.achievements import achievement_manager
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

    @app_commands.command(name="profile", description="查詢你的等級、經驗值和金錢資料")
    @app_commands.describe(show="讓所有人都看到你的個人資料")
    async def profile(self, interaction: discord.Interaction, show: bool = False):
        """查詢用戶的等級、經驗值和金錢資料
        一般使用者只能查自己，管理員可查詢任何人
        """
        # 只能查自己
        target = interaction.user
        ephemeral = not show
        await interaction.response.defer(thinking=True, ephemeral=ephemeral)
        user_data = await user_data_manager.get_user(target)

        # 取得用戶資料
        level = user_data.get("lv", DEFAULT_LEVEL)
        exp = user_data.get("exp", DEFAULT_EXP)
        money = user_data.get("money", DEFAULT_MONEY)
        achievements = user_data.get("achievements", [])
        found_flags = user_data.get("found_flags", [])
        sign_in_streak = user_data.get("sign_in_streak", 0)
        nickname = target.nick if target.nick else target.display_name

        # 計算經驗值進度
        required_exp = self._calculate_required_exp(level)
        progress = min(exp / required_exp, 1.0)
        progress_bar = self._create_progress_bar(progress)
        exp_to_next = max(required_exp - exp, 0)

        # 取得所有用戶資料以計算排名
        all_user_data = user_data_manager.users
        user_list = list(all_user_data.values())
        # 等級排名
        sorted_by_level = sorted(
            user_list, key=lambda u: (-u.get("lv", 0), -u.get("exp", 0))
        )
        level_total = len(sorted_by_level)
        level_rank = next(
            (
                i + 1
                for i, u in enumerate(sorted_by_level)
                if u.get("name") == user_data.get("name")
            ),
            None,
        )
        # 金錢排名
        sorted_by_money = sorted(user_list, key=lambda u: -u.get("money", 0))
        money_total = len(sorted_by_money)
        money_rank = next(
            (
                i + 1
                for i, u in enumerate(sorted_by_money)
                if u.get("name") == user_data.get("name")
            ),
            None,
        )

        # 成就與彩蛋數
        achievements_count = len(achievements)
        found_flags_count = len(found_flags)

        # 建立資料嵌入
        embed = self._create_profile_embed(
            target,
            level,
            exp,
            required_exp,
            money,
            progress_bar,
            nickname=nickname,
            exp_to_next=exp_to_next,
            level_rank=level_rank,
            level_total=level_total,
            money_rank=money_rank,
            money_total=money_total,
            achievements_count=achievements_count,
            found_flags_count=found_flags_count,
            sign_in_streak=sign_in_streak,
        )

        await interaction.followup.send(embed=embed)

        # 追蹤功能使用並檢查成就
        await AchievementManager.track_feature_usage(target.id, "profile", self.bot)
        await AchievementManager.check_money_achievements(target.id, money, self.bot)
        if show and money >= 10000:
            await AchievementManager.check_and_award_achievement(target.id, "rich_player", self.bot)

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
        nickname: str = None,
        exp_to_next: int = None,
        level_rank: int = None,
        level_total: int = None,
        money_rank: int = None,
        money_total: int = None,
        achievements_count: int = None,
        found_flags_count: int = None,
        sign_in_streak: int = None,
    ) -> discord.Embed:
        """建立個人資料的嵌入訊息，含更多統計"""
        embed = discord.Embed(
            title=f"✨ {user.display_name} 的個人資料",
            color=user.color,
        )
        embed.set_thumbnail(url=user.avatar.url)

        # ── 基本資料 ──
        basic_info = f"暱稱：{nickname}\n金錢：{money} 元"
        embed.add_field(name="👤 基本資料", value=basic_info, inline=False)

        # ── 等級／經驗值 ──
        level_exp_info = (
            f"等級：{level}\n經驗值：{exp} / {required_exp}\n{progress_bar}"
        )
        embed.add_field(
            name="⭐ 等級／經驗值",
            value=level_exp_info,
            inline=False,
        )

        # ── 排名、成就、彩蛋、連續簽到合併顯示 ──
        info_lines = []
        rank_line = None
        if (
            level_rank is not None
            and level_total is not None
            and money_rank is not None
            and money_total is not None
        ):
            rank_line = f"🏅 等級排名 #{level_rank}/{level_total}｜💰 金錢排名 #{money_rank}/{money_total}"
        elif level_rank is not None and level_total is not None:
            rank_line = f"🏅 等級排名 #{level_rank}/{level_total}"
        elif money_rank is not None and money_total is not None:
            rank_line = f"💰 金錢排名 #{money_rank}/{money_total}"
        if rank_line:
            info_lines.append(rank_line)

        if achievements_count is not None and found_flags_count is not None:
            info_lines.append(
                f"🏆 獲得成就 {achievements_count}｜🥚 獲得彩蛋 {found_flags_count}"
            )
        elif achievements_count is not None:
            info_lines.append(f"🏆 獲得成就 {achievements_count}")
        elif found_flags_count is not None:
            info_lines.append(f"🥚 獲得彩蛋 {found_flags_count}")

        if sign_in_streak is not None:
            info_lines.append(f"📅 連續簽到 {sign_in_streak}")

        if info_lines:
            embed.add_field(
                name="📊 其他資訊", value="\n".join(info_lines), inline=False
            )

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
        
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(interaction.user.id, "links", self.bot)

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
/gift <金額> <對象> - 贈與對方一定量的金錢
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
            name="🎵 MyGo/ave-mujica 專屬",
            value="""
/mygo <關鍵字> — 搜尋 MyGO!!!!! / ave-mujica 圖片
/quote — 隨機 MyGO!!!!! / ave-mujica 名言
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
        # 寵物系統
        embed.add_field(
            name="🐾 虛擬寵物",
            value="""
/adopt <寵物名字> — 認養一隻虛擬寵物（會創建專屬討論串）
/pet_status — 查看你的寵物狀態和好感度
/play_ball — 跟寵物玩球遊戲
/feed_pet — 餵食寵物（增加好感度）
/pet_ranking — 查看好感度排行榜
/show_off_pet — 在公共頻道炫耀你的寵物
/pet_thread — 快速前往寵物專屬討論串
> **🏠 專屬小窩**：每隻寵物都有專屬討論串，寵物會在裡面與你互動
> **🌟 炫耀功能**：可以向大家展示你和寵物的感情深度
> **🤖 AI 驅動**：寵物使用 Webhook 以自己的身份說話，彷彿真實存在
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

    @app_commands.command(name = "rear_room_manual", description = "顯示 7/3 相關內容")
    async def _rear_room_link(self, interaction: discord.Interaction):
        date = datetime.datetime.today()
        if date < datetime.datetime(2025, 7, 3, 19, 0):
            embed = discord.Embed(title = "時候還沒到喔！", color = 0xFF0000)
            embed.add_field(
                name = "⚠ 禁止暴雷 ⚠",
                value = "還想要偷看呀！",
                inline = False
            )
            await AchievementManager.check_and_award_achievement(interaction.user.id, "boom_light_bad", self.bot)
        elif date < datetime.datetime(2025, 7, 4):
            embed = discord.Embed(title = "遊戲介紹")
            embed.add_field(
                name = "手冊連結",
                value = "[【點我！！】](https://drive.google.com/file/d/10gHC5_721gVMX4exWC0NVeLNwWw243TA/view?usp=drivesdk)",
                inline = False
            )
        else:
            embed = discord.Embed(title = "時候還沒到喔！", color = 0xFF0000)
            embed.add_field(
                name = "⁉ 遊戲結束了 ⁉",
                value = """你也太慢半拍了吧…
`flag{||4db02ceb09e30901cd50b6e25dbabf||}`
[不過你真的想要看也是可以啦](https://drive.google.com/file/d/10gHC5_721gVMX4exWC0NVeLNwWw243TA/view?usp=drivesdk)""",
                inline = False
            )
        await interaction.response.send_message(embed = embed, ephemeral = True)

    @app_commands.command(name = "gift", description = "送禮！免手續費！")
    @app_commands.describe(amount = "想要送多少金額")
    async def _gift(self, interaction: discord.Interaction, amount: int, receiver: discord.User):
        user_data = await user_data_manager.get_user(interaction.user.id, interaction.user)
        money = user_data["money"]
        if amount < 0:
            await interaction.response.send_message(
                f"還想要偷別人的錢啊！\n`flag{{||60f2ea488d296e2f2f079d00e713e6||}}`",
                ephemeral = True
            )
            return
        if money < amount:
            await interaction.response.send_message(
                f"你沒有足夠的錢可以用來給予！{money}/{amount}",
                ephemeral = True
            )
            return
        if not receiver or receiver.bot:
            await interaction.response.send_message(
                f"你只能贈送金錢給活人，不可以給 Bot",
                ephemeral = True
            )
            return
        receiver_data = await user_data_manager.get_user(receiver.id, receiver)
        user_data["money"] -= amount
        receiver_data["money"] += amount
        await user_data_manager.update_user_data(interaction.user.id, user_data)
        await user_data_manager.update_user_data(receiver.id, receiver_data)
        await interaction.response.send_message(
            f"{interaction.user.mention} 贈送了 {amount} 元給 {receiver.mention}",
            silent = True
        )
        await AchievementManager.track_feature_usage(
            interaction.user.id, "gift", self.bot
        )
        await AchievementManager.check_money_achievements(
                interaction.user.id, user_data["money"], self.bot
        )
        await AchievementManager.check_money_achievements(
                receiver.id, receiver_data["money"], self.bot
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
