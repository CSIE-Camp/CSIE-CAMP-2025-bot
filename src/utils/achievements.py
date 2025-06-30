"""
成就系統模組。

此模組定義了各種成就和獎勵系統，並提供檢查和授予成就的功能。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import discord
from discord.ext import commands
import json
import os
from src.utils.user_data import user_data_manager


class Achievement:
    """成就類別"""

    def __init__(self, id: int, name: str, description: str, icon: str):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon


def load_achievements() -> Dict[str, Achievement]:
    """從 JSON 檔案載入成就資料"""
    achievements_file = os.path.join("data", "achievement.json")
    try:
        with open(achievements_file, "r", encoding="utf-8") as f:
            achievement_data = json.load(f)

        achievements = {}
        for achievement_id, data in achievement_data.items():
            achievements[achievement_id] = Achievement(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                icon=data["icon"],
            )

        print(f"已成功載入 {len(achievements)} 個成就定義")
        return achievements

    except FileNotFoundError:
        print(f"警告：找不到成就檔案 '{achievements_file}'，使用空的成就列表")
        return {}
    except json.JSONDecodeError as e:
        print(f"警告：無法解析成就檔案 '{achievements_file}': {e}")
        return {}
    except Exception as e:
        print(f"載入成就檔案時發生錯誤: {e}")
        return {}


# 載入所有成就
ACHIEVEMENTS = load_achievements()


class AchievementManager:
    """成就管理器"""

    @staticmethod
    async def check_and_award_achievement(
        user_id: int, achievement_id: str, ctx: commands.Bot | commands.Context = None
    ) -> bool:
        """
        檢查並授予成就

        Args:
            user_id: 使用者ID
            achievement_id: 成就ID
            ctx: Discord命令上下文（可選）

        Returns:
            bool: 是否成功授予新成就
        """
        if achievement_id not in ACHIEVEMENTS:
            return False

        user = await user_data_manager.get_user(user_id)

        # 確保使用者有成就列表
        if "achievements" not in user:
            user["achievements"] = []

        # 檢查是否已經擁有此成就
        if achievement_id in user["achievements"]:
            return False

        # 授予成就
        achievement = ACHIEVEMENTS[achievement_id]
        user["achievements"].append(achievement_id)

        await user_data_manager.update_user_data(user_id, user)

        bot: commands.Bot = None
        # 如果有context，發送成就獲得訊息
        if isinstance(ctx, commands.Context):
            bot = ctx.bot
        else:
            bot = ctx
        if bot:
            user_obj = await bot.fetch_user(user_id)
            embed = discord.Embed(
                title="🎉 恭喜獲得成就！",
                description=f"{user_obj.mention} 達成了成就 **{achievement.icon} {achievement.name}**",
                color=discord.Color.gold(),
            )
            channel = await bot.fetch_channel(os.getenv("ANNOUNCEMENT_CHANNEL_ID"))
            await channel.send(embed=embed)

        return True

    @staticmethod
    async def get_user_achievements(user_id: int) -> List[Achievement]:
        """獲取使用者的所有成就"""
        user = await user_data_manager.get_user(user_id)

        if "achievements" not in user:
            return []

        return [
            ACHIEVEMENTS[achievement_id]
            for achievement_id in user["achievements"]
            if achievement_id in ACHIEVEMENTS
        ]

    @staticmethod
    async def check_money_achievements(user_id: int, current_money: int, ctx=None):
        """檢查金錢相關成就"""
        if current_money >= 10000:
            await AchievementManager.check_and_award_achievement(
                user_id, "rich_player", ctx
            )

    @staticmethod
    async def check_slot_achievements(user_id: int, max_count: int, ctx=None):
        """檢查拉霸相關成就"""
        if max_count == 5:
            await AchievementManager.check_and_award_achievement(
                user_id, "slot_god", ctx
            )
        elif max_count == 4:
            await AchievementManager.check_and_award_achievement(
                user_id, "slot_master", ctx
            )

    @staticmethod
    async def check_debt_achievements(user_id: int, debt_count: int, ctx=None):
        """檢查欠債相關成就"""
        if debt_count >= 10:
            await AchievementManager.check_and_award_achievement(
                user_id, "kong_yiji", ctx
            )

    @staticmethod
    async def track_feature_usage(user_id: int, feature_name: str, ctx=None):
        """
        記錄功能使用狀態並檢查"我全都要"成就

        Args:
            user_id: 使用者ID
            feature_name: 功能名稱
            ctx: Discord命令上下文（可選）
        """
        user = await user_data_manager.get_user(user_id)

        # 確保使用者有功能使用記錄
        if "used_features" not in user:
            user["used_features"] = []

        # 如果功能尚未使用過，加入記錄
        if feature_name not in user["used_features"]:
            user["used_features"].append(feature_name)
            await user_data_manager.update_user_data(user_id, user)

            # 檢查是否達成"我全都要"成就
            await AchievementManager.check_i_want_all_achievement(user_id, ctx)

    @staticmethod
    async def check_i_want_all_achievement(user_id: int, ctx=None):
        """
        檢查"我全都要"成就
        需要使用的主要功能：
        - profile: 查看個人資料
        - checkin: 每日簽到
        - game_slot: 拉霸遊戲
        - game_dice: 骰子遊戲
        - game_rps: 剪刀石頭布
        - mygo: MyGO相關功能
        - note_search: 筆記搜尋
        - links: 查看連結
        - achievements: 查看成就
        - egg: 查看彩蛋
        """
        user = await user_data_manager.get_user(user_id)
        used_features = user.get("used_features", [])

        # 定義需要使用的主要功能
        required_features = {
            "profile",  # 查看個人資料
            "checkin",  # 每日簽到
            "game_slot",  # 拉霸遊戲
            "game_dice",  # 骰子遊戲
            "game_rps",  # 剪刀石頭布
            "mygo",  # MyGO相關功能
            "note_search",  # 筆記搜尋
            "links",  # 查看連結
            "achievements",  # 查看成就
            "egg",  # 查看彩蛋
        }

        # 檢查是否使用了所有必要功能
        if required_features.issubset(set(used_features)):
            await AchievementManager.check_and_award_achievement(
                user_id, "i_want_all", ctx
            )


# 建立全域成就管理器實例
achievement_manager = AchievementManager()


# 全域函數，方便其他模組導入使用
async def track_feature_usage(user_id: int, feature_name: str, ctx=None):
    """
    記錄功能使用狀態的全域函數

    Args:
        user_id: 使用者ID
        feature_name: 功能名稱
        ctx: Discord命令上下文（可選）
    """
    await AchievementManager.track_feature_usage(user_id, feature_name, ctx)
