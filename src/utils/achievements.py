"""
成就系統模組。

此模組定義了各種成就和獎勵系統，並提供檢查和授予成就的功能。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import discord
from src.utils.user_data import user_data_manager


class Achievement:
    """成就類別"""
    
    def __init__(self, id: str, name: str, description: str, icon: str, reward_money: int = 0):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.reward_money = reward_money


# 定義所有成就
ACHIEVEMENTS = {
    "slot_jackpot": Achievement(
        id="slot_jackpot",
        name="拉霸大獎",
        description="在拉霸遊戲中中了五個相同符號",
        icon="🎰",
        reward_money=500
    ),
    "slot_master": Achievement(
        id="slot_master",
        name="拉霸高手",
        description="在拉霸遊戲中中了四個相同符號",
        icon="🎯",
        reward_money=100
    ),
    "lucky_streak": Achievement(
        id="lucky_streak",
        name="幸運連擊",
        description="連續簽到7天",
        icon="🍀",
        reward_money=200
    ),
    "rich_player": Achievement(
        id="rich_player",
        name="小富豪",
        description="擁有超過10000元",
        icon="💰",
        reward_money=1000
    )
}


class AchievementManager:
    """成就管理器"""
    
    @staticmethod
    async def check_and_award_achievement(user_id: int, achievement_id: str, ctx=None) -> bool:
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
        user["money"] += achievement.reward_money
        
        await user_data_manager.update_user_data(user_id, user)
        
        # 如果有context，發送成就獲得訊息
        if ctx:
            embed = discord.Embed(
                title="🎉 恭喜獲得成就！",
                description=f"**{achievement.icon} {achievement.name}**\n{achievement.description}",
                color=0xFFD700
            )
            if achievement.reward_money > 0:
                embed.add_field(
                    name="獎勵", 
                    value=f"💰 {achievement.reward_money} 元", 
                    inline=False
                )
            embed.set_footer(text=f"成就獲得時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await ctx.send(embed=embed)
        
        return True
    
    @staticmethod
    async def get_user_achievements(user_id: int) -> List[Achievement]:
        """獲取使用者的所有成就"""
        user = await user_data_manager.get_user(user_id)
        
        if "achievements" not in user:
            return []
        
        return [ACHIEVEMENTS[achievement_id] for achievement_id in user["achievements"] 
                if achievement_id in ACHIEVEMENTS]
    
    @staticmethod
    async def check_money_achievements(user_id: int, current_money: int, ctx=None):
        """檢查金錢相關成就"""
        if current_money >= 10000:
            await AchievementManager.check_and_award_achievement(user_id, "rich_player", ctx)
    
    @staticmethod
    async def check_slot_achievements(user_id: int, max_count: int, ctx=None):
        """檢查拉霸相關成就"""
        if max_count == 5:
            await AchievementManager.check_and_award_achievement(user_id, "slot_jackpot", ctx)
        elif max_count == 4:
            await AchievementManager.check_and_award_achievement(user_id, "slot_master", ctx)


# 建立全域成就管理器實例
achievement_manager = AchievementManager()
