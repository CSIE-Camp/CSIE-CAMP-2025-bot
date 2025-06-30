"""
虛擬寵物養成系統

功能說明：
🐱 玩家可以認養虛擬寵物並培養好感度
🎮 寵物會定時送禮物、表達心情、尋找寶物、睡覺休息、跳舞娛樂
🤖 使用 AI 生成寵物的個性、對話和圖片
💖 好感度系統，與寵物互動可增加好感度
🏆 排行榜顯示好感度最高的寵物主人

主要指令：
• /adopt 寵物名字     - 認養一隻新寵物（會創建專屬討論串）
• /pet_status        - 查看寵物狀態和好感度
• /play_ball         - 跟寵物玩球遊戲
• /feed_pet          - 餵食寵物（增加好感度）
• /pet_ranking       - 查看好感度排行榜
• /show_off_pet      - 在公共頻道炫耀你的寵物
• /pet_thread        - 快速前往寵物專屬討論串

特色功能：
• 🏠 專屬討論串：每隻寵物都有自己的小窩
• 🌟 公共炫耀：向大家展示你和寵物的感情
• 🤖 Webhook 互動：寵物以自己的身份說話

寵物行為：
• 每 3-8 分鐘會帶禮物給主人（在專屬討論串中）
• 每 5-12 分鐘會表達心情不好（在專屬討論串中）
• 每 4-10 分鐘會去尋找寶物（在專屬討論串中）
• 每 6-15 分鐘會睡覺休息（在專屬討論串中）
• 每 8-18 分鐘會跳舞娛樂（在專屬討論串中）
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime
import asyncio
import json
import os
from typing import Dict, Any, Optional

from src import config
from src.utils.user_data import user_data_manager
from src.utils.llm import generate_text
from src.utils.pet_ai import pet_ai_generator
from src.utils.achievements import AchievementManager


class PetSystem(commands.Cog):
    """虛擬寵物養成系統"""

    def __init__(self, bot):
        self.bot = bot
        self.pets_data_file = os.path.join(config.DATA_DIR, "pets_data.json")
        self.pets: Dict[str, Dict[str, Any]] = {}
        self.pet_timers: Dict[str, Dict[str, datetime.datetime]] = {}
        self.load_pets_data()

        # 啟動定時檢查任務
        self.timer_task = self.bot.loop.create_task(self.pet_timer_loop())

    def cog_unload(self):
        """Cog 卸載時清理任務"""
        if hasattr(self, 'timer_task'):
            self.timer_task.cancel()

    def load_pets_data(self):
        """載入寵物資料"""
        try:
            if os.path.exists(self.pets_data_file):
                with open(self.pets_data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.pets = data.get("pets", {})
                    self.pet_timers = {}
                    
                    # 重建定時器
                    for user_id, pet in self.pets.items():
                        self.pet_timers[user_id] = self.generate_all_timers()
                    
                    # 啟動時同步用戶資料中的寵物好感度
                    asyncio.create_task(self._sync_all_user_affection())
                    
                print(f"📂 已載入 {len(self.pets)} 隻寵物的資料")
        except Exception as e:
            print(f"❌ 載入寵物資料失敗: {e}")
            self.pets = {}
            self.pet_timers = {}

    async def _sync_all_user_affection(self):
        """同步所有用戶的寵物好感度"""
        try:
            await asyncio.sleep(5)  # 等待機器人完全啟動
            for user_id, pet_data in self.pets.items():
                affection = pet_data.get("affection", 0)
                pet_name = pet_data.get("name", "")
                
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        user_data = await user_data_manager.get_user(user)
                        if user_data.get("pet_name") != pet_name or user_data.get("pet_affection") != affection:
                            user_data["pet_name"] = pet_name
                            user_data["pet_affection"] = affection
                            await user_data_manager.update_user_data(int(user_id), user_data)
                            print(f"🔄 已同步用戶 {user.display_name} 的寵物資料")
                except Exception as e:
                    print(f"❌ 同步用戶 {user_id} 的寵物資料失敗: {e}")
                    
        except Exception as e:
            print(f"❌ 批量同步寵物資料失敗: {e}")
        except Exception as e:
            print(f"❌ 載入寵物資料失敗: {e}")
            self.pets = {}
            self.pet_timers = {}

    def save_pets_data(self):
        """保存寵物資料"""
        try:
            data = {
                "pets": self.pets,
                "last_updated": datetime.datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(self.pets_data_file), exist_ok=True)
            with open(self.pets_data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存寵物資料失敗: {e}")

    def generate_all_timers(self) -> Dict[str, datetime.datetime]:
        """生成所有寵物行為的定時器"""
        now = datetime.datetime.now()
        return {
            "gift": now + datetime.timedelta(minutes=random.randint(3, 8)),
            "bad_mood": now + datetime.timedelta(minutes=random.randint(5, 12)),
            "treasure_hunt": now + datetime.timedelta(minutes=random.randint(4, 10)),
            "sleep": now + datetime.timedelta(minutes=random.randint(6, 15)),
            "dance": now + datetime.timedelta(minutes=random.randint(8, 18))
        }

    def reset_timer(self, user_id: str, timer_type: str):
        """重置指定類型的定時器"""
        if user_id not in self.pet_timers:
            self.pet_timers[user_id] = {}
        
        timer_ranges = {
            "gift": (3, 8),
            "bad_mood": (5, 12),
            "treasure_hunt": (4, 10),
            "sleep": (6, 15),
            "dance": (8, 18)
        }
        
        min_time, max_time = timer_ranges.get(timer_type, (5, 10))
        self.pet_timers[user_id][timer_type] = datetime.datetime.now() + datetime.timedelta(minutes=random.randint(min_time, max_time))

    def increase_affection(self, user_id: str, amount: int = 1):
        """增加寵物好感度"""
        if user_id in self.pets:
            old_affection = self.pets[user_id].get("affection", 0)
            new_affection = old_affection + amount
            self.pets[user_id]["affection"] = new_affection
            self.save_pets_data()
            
            # 同步更新用戶資料中的好感度
            asyncio.create_task(self._sync_user_affection(user_id, new_affection))

    async def _sync_user_affection(self, user_id: str, affection: int):
        """同步用戶資料中的寵物好感度"""
        try:
            user = self.bot.get_user(int(user_id))
            if user:
                user_data = await user_data_manager.get_user(user)
                user_data["pet_affection"] = affection
                await user_data_manager.update_user_data(int(user_id), user_data)
                
                # 檢查好感度相關成就
                await self.check_pet_achievements(int(user_id))
                
        except Exception as e:
            print(f"❌ 同步用戶好感度失敗: {e}")

    async def create_pet_webhook(self, channel, pet_name: str, pet_avatar_data = None):
        """創建寵物 Webhook"""
        try:
            # 檢查機器人是否有管理 Webhook 的權限
            if not channel.permissions_for(channel.guild.me).manage_webhooks:
                print(f"❌ 機器人在頻道 {channel.name} 缺少 Manage Webhooks 權限")
                return None
                
            # 如果有頭像資料且是 bytes 類型，使用它作為頭像
            if pet_avatar_data and isinstance(pet_avatar_data, bytes):
                try:
                    webhook = await channel.create_webhook(name=f"Pet_{pet_name}", avatar=pet_avatar_data)
                except:
                    # 如果使用頭像失敗，創建無頭像的 webhook
                    webhook = await channel.create_webhook(name=f"Pet_{pet_name}")
            else:
                webhook = await channel.create_webhook(name=f"Pet_{pet_name}")
            return webhook
        except discord.Forbidden:
            print(f"❌ 創建 Webhook 被拒絕：機器人可能缺少權限")
            return None
        except discord.HTTPException as e:
            print(f"❌ 創建 Webhook HTTP 錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 創建 Webhook 失敗: {e}")
            return None

    async def pet_timer_loop(self):
        """寵物定時行為檢查循環"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒檢查一次
                current_time = datetime.datetime.now()
                
                for user_id, timers in self.pet_timers.items():
                    if user_id not in self.pets:
                        continue
                    
                    pet = self.pets[user_id]
                    
                    # 檢查各種定時事件
                    for timer_type, due_time in timers.items():
                        if current_time >= due_time:
                            await self.handle_pet_event(user_id, pet, timer_type)
                            self.reset_timer(user_id, timer_type)
                            
            except Exception as e:
                print(f"❌ 寵物定時器錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待更久

    async def handle_pet_event(self, user_id: str, pet: Dict[str, Any], event_type: str):
        """處理寵物事件"""
        try:
            # 優先使用寵物的專屬 Thread
            thread_id = pet.get("thread_id")
            channel = None
            
            if thread_id:
                try:
                    channel = self.bot.get_channel(thread_id)
                    if not channel:  # Thread 可能被刪除了
                        channel = self.bot.get_channel(pet["channel_id"])
                except:
                    channel = self.bot.get_channel(pet["channel_id"])
            else:
                channel = self.bot.get_channel(pet["channel_id"])
                
            if not channel:
                return

            pet_name = pet["name"]
            pet_description = pet["description"]

            # 使用新的 AI 生成器產生行為描述
            response = await pet_ai_generator.generate_pet_behavior_description(pet_name, pet_description, event_type)

            # 使用 Webhook 讓寵物以自己的身份說話
            webhook = await self.create_pet_webhook(channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    # 添加表情符號前綴讓訊息更生動
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    formatted_response = f"{response}"
                    await webhook.send(formatted_response, username=f"{emoji_prefix} {pet_name}")
                    await webhook.delete()  # 使用完畢後刪除 webhook
                except Exception as e:
                    print(f"❌ Webhook 發送失敗: {e}")
                    # 如果 Webhook 失敗，回退到普通訊息
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await channel.send(f"{emoji_prefix} **{pet_name}**: {response}")
            else:
                # 如果無法創建 Webhook，使用普通訊息
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await channel.send(f"{emoji_prefix} **{pet_name}**: {response}")

            # 某些事件會增加好感度
            if event_type in ["gift", "treasure_hunt", "dance"]:
                self.increase_affection(user_id, 1)
                
        except Exception as e:
            print(f"❌ 處理寵物事件失敗: {e}")

    async def generate_pet_avatar(self, pet_name: str, pet_description: str):
        """生成寵物頭像"""
        try:
            print(f"🎨 開始為 {pet_name} 生成專屬頭像...")
            
            # 使用新的 AI 生成器
            avatar_bytes, avatar_emoji = await pet_ai_generator.generate_pet_avatar(pet_name, pet_description)
            
            if avatar_bytes:
                print(f"✅ {pet_name} 的 AI 頭像生成成功！")
                return avatar_bytes, avatar_emoji
            else:
                print(f"⚠️ {pet_name} 的 AI 頭像生成失敗，使用預設表情符號")
                return None, avatar_emoji
                
        except Exception as e:
            print(f"❌ 生成寵物頭像失敗: {e}")
            # 回退到隨機表情符號
            pet_emojis = ["🐱", "🐶", "🐰", "🐹", "🐼", "🦊", "🐺", "🐯", "🦁", "🐸"]
            selected_emoji = random.choice(pet_emojis)
            return None, selected_emoji

    async def check_pet_achievements(self, user_id: int, has_ai_avatar: bool = False):
        """檢查寵物相關成就"""
        try:
            user_str = str(user_id)
            
            # 寵物愛好者成就 - 認養寵物
            if user_str in self.pets:
                await AchievementManager.check_and_award_achievement(user_id, "pet_adopter")
            
            # AI 寵物大師成就 - 成功生成 AI 頭像
            if has_ai_avatar:
                await AchievementManager.check_and_award_achievement(user_id, "ai_pet_master")
            
            # 寵物語者成就 - 好感度達到50
            if user_str in self.pets:
                affection = self.pets[user_str].get("affection", 0)
                if affection >= 50:
                    await AchievementManager.check_and_award_achievement(user_id, "pet_whisperer")
            
            # 資深飼主成就 - 相處超過7天
            if user_str in self.pets:
                adopted_date = datetime.datetime.fromisoformat(self.pets[user_str]["adopted_date"])
                days_together = (datetime.datetime.now() - adopted_date).days
                if days_together >= 7:
                    await AchievementManager.check_and_award_achievement(user_id, "long_term_owner")
                    
        except Exception as e:
            print(f"❌ 檢查寵物成就失敗: {e}")

    @app_commands.command(name="adopt", description="認養一隻虛擬寵物")
    @app_commands.describe(pet_name="你想給寵物取的名字")
    async def adopt_pet(self, interaction: discord.Interaction, pet_name: str):
        """認養寵物：/adopt 寵物名字"""
        user_id = str(interaction.user.id)
        
        # 檢查是否已經有寵物
        if user_id in self.pets:
            await interaction.response.send_message(f"❌ 你已經有一隻寵物了：**{self.pets[user_id]['name']}**！")
            return

        # 檢查名字長度
        if len(pet_name) > 20:
            await interaction.response.send_message("❌ 寵物名字太長了！請使用20個字元以內的名字。")
            return

        await interaction.response.send_message(f"🔍 正在為你尋找最適合的寵物 **{pet_name}**...")

        try:
            # 使用 AI 生成寵物個性
            print(f"🤖 正在為 {pet_name} 生成獨特個性...")
            description = await pet_ai_generator.generate_pet_personality(pet_name)

            # 創建專屬寵物 Thread
            thread_name = f"🐾 {pet_name} 的小窩"
            thread = await interaction.channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.public_thread,
                reason=f"{interaction.user.display_name} 認養了寵物 {pet_name}"
            )

            # 建立寵物資料
            pet_data = {
                "name": pet_name,
                "description": description,
                "channel_id": interaction.channel.id,
                "thread_id": thread.id,  # 記錄專屬 Thread ID
                "affection": 0,
                "adopted_date": datetime.datetime.now().isoformat(),
                "owner_name": interaction.user.display_name
            }

            # 保存寵物資料
            self.pets[user_id] = pet_data
            self.pet_timers[user_id] = self.generate_all_timers()
            self.save_pets_data()

            # 初始化用戶數據中的寵物欄位
            user_data = await user_data_manager.get_user(interaction.user)
            user_data["pet_name"] = pet_name
            user_data["pet_affection"] = 0
            await user_data_manager.update_user_data(interaction.user.id, user_data)

            # 生成寵物頭像
            avatar_bytes, avatar_emoji = await self.generate_pet_avatar(pet_name, description)
            
            # 更新寵物資料，包含頭像資訊
            self.pets[user_id]["avatar"] = avatar_bytes
            self.pets[user_id]["avatar_emoji"] = avatar_emoji
            self.save_pets_data()

            # 檢查並發放成就
            await self.check_pet_achievements(interaction.user.id, avatar_bytes)

            # 建立歡迎 Embed
            embed = discord.Embed(
                title="🎉 認養成功！",
                description=f"恭喜你成功認養了 **{pet_name}** {avatar_emoji}！",
                color=0x00ff90
            )
            embed.add_field(name="🐾 寵物資訊", value=description, inline=False)
            embed.add_field(name="💖 初始好感度", value="0", inline=True)
            embed.add_field(name="📅 認養日期", value=datetime.datetime.now().strftime("%Y-%m-%d"), inline=True)
            embed.add_field(
                name="🎮 互動指令", 
                value="• `/pet_status` - 查看寵物狀態\n• `/play_ball` - 跟寵物玩球\n• `/feed_pet` - 餵食寵物", 
                inline=False
            )
            embed.set_footer(text="你的寵物會定時與你互動，記得多關心它哦！")

            await interaction.followup.send(embed=embed)

            # 寵物在專屬 Thread 中打招呼
            context = "我剛被主人認養，很開心能遇到這麼好的主人！"
            greeting = await pet_ai_generator.generate_pet_response(pet_name, description, context)
            
            await asyncio.sleep(2)
            
            # 在 Thread 中使用 Webhook 讓寵物打招呼
            webhook = await self.create_pet_webhook(thread, pet_name, avatar_bytes)
            if webhook:
                try:
                    await webhook.send(greeting, username=pet_name)
                    await webhook.delete()  # 使用完畢後刪除 webhook
                except Exception as e:
                    print(f"❌ 寵物打招呼 Webhook 失敗: {e}")
                    await thread.send(f"{avatar_emoji} **{pet_name}**: {greeting}")
            else:
                # 如果無法創建 Webhook，使用普通訊息
                await thread.send(f"{avatar_emoji} **{pet_name}**: {greeting}")

            # 歡迎主人加入 Thread
            welcome_embed = discord.Embed(
                title=f"🏠 歡迎來到 {pet_name} 的小窩！",
                description=f"這裡是你和 **{pet_name}** {avatar_emoji} 的專屬互動空間！\n\n在這裡，{pet_name} 會：\n• 定時與你分享生活點滴\n• 回應你的關愛與互動\n• 展現各種可愛行為\n\n記得多來陪陪你的寵物哦！💕",
                color=0x87ceeb
            )
            welcome_embed.set_footer(text="你仍然可以在任何頻道使用寵物指令")
            await thread.send(embed=welcome_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ 認養寵物時發生錯誤：{str(e)}")
            print(f"❌ 認養寵物錯誤: {e}")

    @app_commands.command(name="pet_status", description="查看你的寵物狀態和好感度")
    async def pet_status(self, interaction: discord.Interaction):
        """查看寵物狀態：/pet_status"""
        user_id = str(interaction.user.id)
        
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！")
            return

        pet = self.pets[user_id]
        
        # 計算認養天數
        adopted_date = datetime.datetime.fromisoformat(pet["adopted_date"])
        days_together = (datetime.datetime.now() - adopted_date).days

        embed = discord.Embed(
            title=f"🐾 {pet['name']} 的狀態",
            color=0x87ceeb
        )
        embed.add_field(name="📝 個性描述", value=pet["description"], inline=False)
        embed.add_field(name="💖 好感度", value=str(pet.get("affection", 0)), inline=True)
        embed.add_field(name="📅 相處天數", value=f"{days_together} 天", inline=True)
        embed.add_field(name="👤 主人", value=pet.get("owner_name", interaction.user.display_name), inline=True)
        
        # 根據好感度顯示寵物狀態
        affection = pet.get("affection", 0)
        if affection >= 50:
            status = "💕 非常愛你"
        elif affection >= 30:
            status = "😊 很喜歡你"
        elif affection >= 15:
            status = "🙂 喜歡你"
        elif affection >= 5:
            status = "😐 普通"
        else:
            status = "😟 還不太熟"
            
        embed.add_field(name="💭 寵物狀態", value=status, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play_ball", description="跟你的寵物玩球遊戲")
    async def play_ball(self, interaction: discord.Interaction):
        """跟寵物玩球：/play_ball"""
        user_id = str(interaction.user.id)
        
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！")
            return

        pet = self.pets[user_id]
        pet_name = pet["name"]

        # 寵物邀請玩球
        embed = discord.Embed(
            title="🎾 玩球時間！",
            description=f"**{pet_name}** 想要跟你玩球！請選擇一種球：",
            color=0xffd700
        )
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # 加入球類選項
        ball_reactions = ["🏀", "⚽", "🏐", "🎾"]
        for ball in ball_reactions:
            await message.add_reaction(ball)

        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ball_reactions and reaction.message.id == message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
            
            # 隨機決定寵物的反應
            mood = random.randint(1, 3)
            affection_gain = 0
            
            # 使用 AI 生成玩球回應
            pet_name = pet["name"]
            pet_description = pet["description"]
            ball_emoji = str(reaction.emoji)
            
            if mood == 1:
                context = f"主人給我一個{ball_emoji}球，但我不是很感興趣"
                result_msg = f"**{pet_name}** 對這個球不太感興趣"
                color = 0xff6b6b
            elif mood == 2:
                context = f"主人給我一個{ball_emoji}球，我覺得還不錯！"
                result_msg = f"**{pet_name}** 覺得這個球還不錯！"
                affection_gain = 1
                color = 0xffd93d
            else:
                context = f"主人給我一個{ball_emoji}球，我超級喜歡！"
                result_msg = f"**{pet_name}** 超喜歡這個球！"
                affection_gain = 2
                color = 0x6bcf7f

            # 生成寵物的 AI 回應
            pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context)

            # 更新好感度
            if affection_gain > 0:
                self.increase_affection(user_id, affection_gain)
                result_msg += f" 💖 好感度 +{affection_gain}！"

            # 更新訊息
            new_embed = discord.Embed(
                title="🎾 玩球結果",
                description=result_msg,
                color=color
            )
            
            current_affection = pet.get("affection", 0) + affection_gain
            new_embed.add_field(name="💖 目前好感度", value=str(current_affection), inline=True)
            
            await message.edit(embed=new_embed)
            
            # 寵物使用 Webhook 回應
            await asyncio.sleep(1)
            webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}")
                    await webhook.delete()  # 使用完畢後刪除 webhook
                except Exception as e:
                    print(f"❌ 玩球回應 Webhook 失敗: {e}")
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await interaction.followup.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
            else:
                # 如果無法創建 Webhook，使用普通訊息
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.followup.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
            await message.clear_reactions()

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ 時間到了",
                description=f"**{pet_name}**: 主人都不理我... (´･ω･`)",
                color=0x95a5a6
            )
            await message.edit(embed=timeout_embed)
            await message.clear_reactions()

    @app_commands.command(name="feed_pet", description="餵食你的寵物")
    async def feed_pet(self, interaction: discord.Interaction):
        """餵食寵物：/feed_pet"""
        user_id = str(interaction.user.id)
        
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！")
            return

        pet = self.pets[user_id]
        pet_name = pet["name"]

        # 檢查餵食冷卻時間（每小時只能餵一次）
        last_fed = pet.get("last_fed")
        if last_fed:
            last_fed_time = datetime.datetime.fromisoformat(last_fed)
            time_diff = datetime.datetime.now() - last_fed_time
            if time_diff.total_seconds() < 3600:  # 1小時 = 3600秒
                remaining = 3600 - time_diff.total_seconds()
                minutes = int(remaining // 60)
                await interaction.response.send_message(f"⏰ **{pet_name}** 還不餓呢！請等待 {minutes} 分鐘後再餵食。")
                return

        # 餵食成功
        foods = ["🍖 美味肉塊", "🐟 新鮮魚肉", "🥕 營養胡蘿蔔", "🍎 甜脆蘋果", "🥛 溫暖牛奶"]
        selected_food = random.choice(foods)
        
        affection_gain = random.randint(2, 4)
        self.increase_affection(user_id, affection_gain)
        
        # 更新餵食時間
        self.pets[user_id]["last_fed"] = datetime.datetime.now().isoformat()
        self.save_pets_data()

        embed = discord.Embed(
            title="🍽️ 餵食成功！",
            description=f"你給 **{pet_name}** 餵了 {selected_food}",
            color=0x00ff90
        )
        embed.add_field(name="💖 好感度增加", value=f"+{affection_gain}", inline=True)
        embed.add_field(name="💖 目前好感度", value=str(pet.get("affection", 0)), inline=True)
        embed.add_field(name="⏰ 下次餵食", value="1 小時後", inline=True)

        await interaction.response.send_message(embed=embed)

        # 寵物使用 AI 生成回應
        pet_name = pet["name"]
        pet_description = pet["description"]
        context = f"主人剛剛餵了我{selected_food}，我很開心！"
        response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context)
        
        await asyncio.sleep(1)
        
        # 創建 Webhook 讓寵物以自己的身份回應
        webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
        if webhook:
            try:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await webhook.send(response, username=f"{emoji_prefix} {pet_name}")
                await webhook.delete()  # 使用完畢後刪除 webhook
            except Exception as e:
                print(f"❌ 餵食回應 Webhook 失敗: {e}")
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.followup.send(f"{emoji_prefix} **{pet_name}**: {response}")
        else:
            # 如果無法創建 Webhook，使用普通訊息
            emoji_prefix = pet.get("avatar_emoji", "🐾")
            await interaction.followup.send(f"{emoji_prefix} **{pet_name}**: {response}")

    @app_commands.command(name="pet_ranking", description="查看寵物好感度排行榜")
    async def pet_ranking(self, interaction: discord.Interaction):
        """查看寵物好感度排行榜：/pet_ranking"""
        if not self.pets:
            await interaction.response.send_message("❌ 目前還沒有人認養寵物！")
            return

        # 按好感度排序
        sorted_pets = sorted(
            self.pets.items(), 
            key=lambda x: x[1].get("affection", 0), 
            reverse=True
        )

        embed = discord.Embed(
            title="🏆 寵物好感度排行榜",
            description="看看誰的寵物最愛主人！",
            color=0xffd700
        )

        # 排行榜表情符號
        rank_emojis = ["🥇", "🥈", "🥉"] + ["🏅"] * 7

        for i, (user_id, pet) in enumerate(sorted_pets[:10]):  # 只顯示前10名
            try:
                user = self.bot.get_user(int(user_id))
                user_name = user.display_name if user else pet.get("owner_name", "未知用戶")
            except:
                user_name = pet.get("owner_name", "未知用戶")

            affection = pet.get("affection", 0)
            pet_name = pet["name"]
            
            # 根據好感度顯示愛心等級
            if affection >= 50:
                love_level = "💕💕💕"
            elif affection >= 30:
                love_level = "💕💕"
            elif affection >= 15:
                love_level = "💕"
            else:
                love_level = "💖"

            rank_emoji = rank_emojis[i] if i < len(rank_emojis) else "📍"
            
            embed.add_field(
                name=f"{rank_emoji} 第 {i+1} 名",
                value=f"**{pet_name}** {love_level}\n主人：{user_name}\n好感度：{affection}",
                inline=True
            )

        embed.set_footer(text="與寵物多互動可以增加好感度哦！")
        await interaction.response.send_message(embed=embed)

    @commands.command(name="abandon_pet", hidden=True)
    @commands.is_owner()
    async def abandon_pet(self, ctx, user_id: str = None):
        """放棄寵物（管理員指令）"""
        target_user_id = user_id or str(ctx.author.id)
        
        if target_user_id not in self.pets:
            await ctx.send("❌ 指定用戶沒有寵物！")
            return

        pet_name = self.pets[target_user_id]["name"]
        del self.pets[target_user_id]
        
        if target_user_id in self.pet_timers:
            del self.pet_timers[target_user_id]
            
        self.save_pets_data()
        
        await ctx.send(f"💔 已移除寵物 **{pet_name}**")

    @app_commands.command(name="show_off_pet", description="在公共頻道炫耀你的寵物")
    async def show_off_pet(self, interaction: discord.Interaction):
        """炫耀寵物：/show_off_pet"""
        user_id = str(interaction.user.id)
        
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！", ephemeral=True)
            return

        pet = self.pets[user_id]
        pet_name = pet["name"]
        pet_description = pet["description"]
        affection = pet.get("affection", 0)
        
        # 計算相處天數
        adopted_date = datetime.datetime.fromisoformat(pet["adopted_date"])
        days_together = (datetime.datetime.now() - adopted_date).days

        # 根據好感度決定炫耀內容
        if affection >= 50:
            love_status = "💕 非常愛你"
            show_off_color = 0xff69b4
        elif affection >= 30:
            love_status = "😊 很喜歡你"
            show_off_color = 0xffd700
        elif affection >= 15:
            love_status = "🙂 喜歡你"
            show_off_color = 0x87ceeb
        elif affection >= 5:
            love_status = "😐 普通"
            show_off_color = 0xffa500
        else:
            love_status = "😟 還不太熟"
            show_off_color = 0x808080

        # 生成炫耀內容
        avatar_emoji = pet.get("avatar_emoji", "🐾")
        
        embed = discord.Embed(
            title=f"🌟 {interaction.user.display_name} 的寵物 {pet_name} {avatar_emoji}",
            description=f"*{pet_description}*",
            color=show_off_color
        )
        
        embed.add_field(name="💖 好感度", value=f"{affection} 分", inline=True)
        embed.add_field(name="😊 關係狀態", value=love_status, inline=True)
        embed.add_field(name="📅 相處天數", value=f"{days_together} 天", inline=True)
        
        # 添加特殊成就
        achievements = []
        if affection >= 100:
            achievements.append("🏆 超級寵物")
        if affection >= 50:
            achievements.append("💝 摯愛夥伴")
        if days_together >= 30:
            achievements.append("🎊 老朋友")
        if days_together >= 7:
            achievements.append("🎉 一週好友")
            
        if achievements:
            embed.add_field(name="🏅 特殊成就", value=" ".join(achievements), inline=False)
        
        # 使用 AI 生成寵物的炫耀回應
        context = "主人正在向大家炫耀我們的感情，我很開心！"
        pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context)
        
        embed.set_footer(text=f"💬 {pet_name}: {pet_response}")
        
        await interaction.response.send_message(embed=embed)

        # 寵物也在公共頻道說話炫耀
        await asyncio.sleep(1)
        
        # 創建 Webhook 讓寵物自己說話
        webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
        if webhook:
            try:
                proud_responses = [
                    "我和主人的感情很好呢！大家看看我們的好感度！✨",
                    "主人對我很好，我很幸福！(´▽｀)",
                    "謝謝主人這麼疼愛我！我會繼續努力的～",
                    "能遇到這麼好的主人真是太幸運了！💕",
                    "主人，我也很愛你哦！ ♡(˃͈ દ ˂͈ ༶ )"
                ]
                proud_response = random.choice(proud_responses)
                await webhook.send(proud_response, username=f"{avatar_emoji} {pet_name}")
                await webhook.delete()
            except Exception as e:
                print(f"❌ 炫耀回應 Webhook 失敗: {e}")
                await interaction.followup.send(f"{avatar_emoji} **{pet_name}**: {proud_response}")
        else:
            # 如果無法創建 Webhook，使用普通訊息
            proud_response = random.choice([
                "我和主人的感情很好呢！大家看看我們的好感度！✨",
                "主人對我很好，我很幸福！(´▽｀)",
                "謝謝主人這麼疼愛我！我會繼續努力的～"
            ])
            await interaction.followup.send(f"{avatar_emoji} **{pet_name}**: {proud_response}")

    @app_commands.command(name="pet_thread", description="前往你的寵物專屬討論串")
    async def pet_thread(self, interaction: discord.Interaction):
        """前往寵物專屬討論串：/pet_thread"""
        user_id = str(interaction.user.id)
        
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！", ephemeral=True)
            return

        pet = self.pets[user_id]
        pet_name = pet["name"]
        thread_id = pet.get("thread_id")
        
        if not thread_id:
            await interaction.response.send_message("❌ 你的寵物還沒有專屬討論串！這可能是因為寵物是在更新前認養的。", ephemeral=True)
            return
        
        thread = self.bot.get_channel(thread_id)
        if not thread:
            await interaction.response.send_message("❌ 找不到寵物的專屬討論串，可能已被刪除。", ephemeral=True)
            return
        
        avatar_emoji = pet.get("avatar_emoji", "🐾")
        
        embed = discord.Embed(
            title=f"🏠 {pet_name} 的小窩",
            description=f"點擊下方連結前往你和 **{pet_name}** {avatar_emoji} 的專屬空間！",
            color=0x87ceeb
        )
        
        embed.add_field(
            name="📍 專屬討論串", 
            value=f"<#{thread_id}>", 
            inline=False
        )
        
        embed.set_footer(text="在專屬討論串中，你的寵物會更頻繁地與你互動！")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """設置 Cog"""
    await bot.add_cog(PetSystem(bot))
