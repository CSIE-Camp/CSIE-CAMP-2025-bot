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
• /comfort_pet       - 安慰你的寵物（當它心情不好時）
• /pet_ranking       - 查看好感度排行榜
• /show_off_pet      - 在公共頻道炫耀你的寵物
• /pet_thread        - 快速前往寵物專屬討論串

特色功能：
• 🏠 專屬討論串：每隻寵物都有自己的小窩
• 🌟 公共炫耀：向大家展示你和寵物的感情
• 🤖 Webhook 互動：寵物以自己的身份說話

寵物行為：
• 每 3-8 分鐘會帶禮物給主人（在專屬討論串中）
• 每 5-12 分鐘會表達心情不好，需要主人安慰（根據回覆品質：優秀+5、良好+3、一般+2、敷衍+1、不當-1好感，超時-2好感）
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
from io import BytesIO

from src import config
from src.utils.user_data import user_data_manager
from src.utils.llm import generate_text
from src.utils.pet_ai import pet_ai_generator
from src.utils.achievements import AchievementManager, track_feature_usage
from src.utils.image_gen import generate_image
from discord import ui

class BallSelectionView(ui.View):
    def __init__(self, original_interaction: discord.Interaction, pet_system_cog):
        super().__init__(timeout=15.0)
        self.original_interaction = original_interaction
        self.cog = pet_system_cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("這不是你的寵物，不能幫牠決定喔！", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            user_id = str(self.original_interaction.user.id)
            pet_name = self.cog.pets[user_id]['name']
            await self.original_interaction.edit_original_response(content=f"**{pet_name}** 等不到你的選擇，自己跑去玩了。", embed=None, view=self)
        except (discord.NotFound, KeyError):
            pass # 訊息可能已被刪除或寵物資料已變更

    async def _handle_ball_selection(self, interaction: discord.Interaction, ball_emoji: str):
        # 停用所有按鈕
        for item in self.children:
            item.disabled = True

        user_id = str(interaction.user.id)
        pet = self.cog.pets[user_id]
        pet_name = pet["name"]
        pet_description = pet["description"]

        # 隨機決定寵物的反應
        mood = random.randint(1, 3)
        affection_gain = 0
        
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

        # 顯示 "正在輸入..."
        async with interaction.channel.typing():
            # 生成寵物的 AI 回應
            pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context)

            # 更新好感度
            if affection_gain > 0:
                self.cog.increase_affection(user_id, affection_gain)

            # 更新訊息
            new_embed = discord.Embed(
                title="🎾 玩球結果",
                description=result_msg,
                color=color
            )
            current_affection = self.cog.pets[user_id].get("affection", 0)
            new_embed.add_field(name="💖 目前好感度", value=f"{current_affection} (+{affection_gain})" if affection_gain > 0 else str(current_affection), inline=True)
            
            await self.original_interaction.edit_original_response(embed=new_embed, view=self)
            
            # 寵物使用 Webhook 回應
            webhook = await self.cog.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=interaction.channel)
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 玩球回應 Webhook 失敗: {e}")
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}", allowed_mentions=discord.AllowedMentions.none())
            else:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}", allowed_mentions=discord.AllowedMentions.none())

        # 追蹤功能使用
        await track_feature_usage(interaction.user.id, "pet")
        self.stop()

    @ui.button(label="🏀", style=discord.ButtonStyle.secondary)
    async def basketball(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self._handle_ball_selection(interaction, "🏀")

    @ui.button(label="⚽", style=discord.ButtonStyle.secondary)
    async def soccer(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self._handle_ball_selection(interaction, "⚽")

    @ui.button(label="🏐", style=discord.ButtonStyle.secondary)
    async def volleyball(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self._handle_ball_selection(interaction, "🏐")

    @ui.button(label="🎾", style=discord.ButtonStyle.secondary)
    async def tennis(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self._handle_ball_selection(interaction, "🎾")

class PetSystem(commands.Cog):
    """虛擬寵物養成系統"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pets_data_file = os.path.join(config.DATA_DIR, "pets_data.json")
        self.pets: Dict[str, Dict[str, Any]] = {}
        self.pet_timers: Dict[str, Dict[str, datetime.datetime]] = {}
        self.comfort_locks: Dict[str, asyncio.Lock] = {}
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
            # 創建可序列化的寵物資料副本
            serializable_pets = {}
            for user_id, pet_data in self.pets.items():
                pet_copy = pet_data.copy()
                # 移除無法序列化的 bytes 資料（頭像）
                if "avatar" in pet_copy and isinstance(pet_copy["avatar"], bytes):
                    pet_copy.pop("avatar")
                serializable_pets[user_id] = pet_copy
            
            data = {
                "pets": serializable_pets,
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
            "bad_mood": now + datetime.timedelta(seconds=random.randint(60, 90)),
            "treasure_hunt": now + datetime.timedelta(minutes=random.randint(1400, 1500)),
        }

    def reset_timer(self, user_id: str, timer_type: str):
        """重置指定類型的定時器"""
        if user_id not in self.pet_timers:
            self.pet_timers[user_id] = {}
        
        timer_ranges = {
            "bad_mood": (60, 90),
            "treasure_hunt": (1400, 1500),
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
            # 如果是 Thread，使用父頻道來創建 Webhook
            target_channel = channel
            if isinstance(channel, discord.Thread):
                target_channel = channel.parent
                if not target_channel:
                    print(f"❌ Thread {channel.name} 沒有父頻道")
                    return None
            
            # 檢查機器人是否有管理 Webhook 的權限
            if not target_channel.permissions_for(target_channel.guild.me).manage_webhooks:
                print(f"❌ 機器人在頻道 {target_channel.name} 缺少 Manage Webhooks 權限")
                return None
                
            # 如果有頭像資料且是 bytes 類型，使用它作為頭像
            if pet_avatar_data and isinstance(pet_avatar_data, bytes):
                try:
                    webhook = await target_channel.create_webhook(name=f"Pet_{pet_name}", avatar=pet_avatar_data)
                except:
                    # 如果使用頭像失敗，創建無頭像的 webhook
                    webhook = await target_channel.create_webhook(name=f"Pet_{pet_name}")
            else:
                webhook = await target_channel.create_webhook(name=f"Pet_{pet_name}")
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
                
                # 檢查等待安慰的寵物是否超時
                await self.check_comfort_timeouts(current_time)
                
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
    
    async def check_comfort_timeouts(self, current_time: datetime.datetime):
        """檢查等待安慰的寵物是否超時"""
        try:
            timeout_pets = []
            
            for user_id, pet in self.pets.items():
                waiting_comfort = pet.get("waiting_for_comfort")
                if waiting_comfort:
                    comfort_time = datetime.datetime.fromisoformat(waiting_comfort["timestamp"])
                    time_diff = (current_time - comfort_time).total_seconds()
                    
                    # 超過安慰時間限制
                    if time_diff > waiting_comfort["comfort_timeout"]:
                        timeout_pets.append(user_id)
            
            # 處理超時的寵物
            for user_id in timeout_pets:
                await self.handle_comfort_timeout(user_id)
                
        except Exception as e:
            print(f"❌ 檢查安慰超時失敗: {e}")
    
    async def handle_comfort_timeout(self, user_id: str):
        """處理安慰超時的寵物"""
        try:
            pet = self.pets[user_id]
            pet_name = pet["name"]
            
            # 好感度-5
            old_affection = pet.get("affection", 0)
            new_affection = max(0, old_affection - 5)  # 確保不會變成負數
            self.pets[user_id]["affection"] = new_affection
            
            # 清除等待安慰狀態
            del self.pets[user_id]["waiting_for_comfort"]
            self.save_pets_data()
            
            # 同步更新用戶資料
            await self._sync_user_affection(user_id, new_affection)
            
            # 找到對應的頻道
            channel_id = pet.get("thread_id") or pet.get("channel_id")
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # 生成失望的回應
                    context = "主人沒有來安慰我，我感到很失望和難過..."
                    response_msg = await pet_ai_generator.generate_pet_response(pet_name, pet["description"], context)
                    
                    # 發送超時訊息
                    timeout_embed = discord.Embed(
                        title="😢 寵物感到被忽視",
                        description=f"**{pet_name}** 等了很久都沒有等到主人的安慰...\n💔 好感度 -5",
                        color=0xff6b6b
                    )
                    await channel.send(embed=timeout_embed)
                    
                    # 寵物使用 Webhook 表達失望
                    await asyncio.sleep(1)
                    webhook = await self.create_pet_webhook(channel, pet_name, pet.get("avatar"))
                    if webhook:
                        try:
                            emoji_prefix = pet.get("avatar_emoji", "🐾")
                            if isinstance(channel, discord.Thread):
                                await webhook.send(response_msg, username=f"{emoji_prefix} {pet_name}", thread=channel)
                            else:
                                await webhook.send(response_msg, username=f"{emoji_prefix} {pet_name}")
                            await webhook.delete()
                        except Exception as e:
                            print(f"❌ 超時回應 Webhook 失敗: {e}")
                            emoji_prefix = pet.get("avatar_emoji", "🐾")
                            await channel.send(f"{emoji_prefix} **{pet_name}**: {response_msg}")
                    else:
                        emoji_prefix = pet.get("avatar_emoji", "🐾")
                        await channel.send(f"{emoji_prefix} **{pet_name}**: {response_msg}")
                        
        except Exception as e:
            print(f"❌ 處理安慰超時失敗: {e}")

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

            # 生成行為描述
            response = await pet_ai_generator.generate_pet_behavior_description(pet_name, pet_description, event_type)

            # --- Treasure Hunt Special Logic ---
            if event_type == "treasure_hunt":
                treasure_description = response
                image_file = None
                image_prompt = None
                
                try:
                    # 1. 生成圖片提示詞
                    image_prompt = await pet_ai_generator.generate_treasure_image_prompt(treasure_description)

                    # 2. 生成圖片
                    if image_prompt:
                        print(f"💎 正在為「{treasure_description}」生成寶物圖片...")
                        print(f"📝 圖片提示詞: {image_prompt}")
                        image_data = await generate_image(image_prompt)
                        if image_data:
                            print("✅ 寶物圖片生成成功！")
                            image_file = discord.File(fp=image_data, filename="treasure.png")
                        else:
                            print("❌ 寶物圖片生成失敗。")
                except Exception as e:
                    print(f"❌ 寶物圖片生成過程中發生錯誤: {e}")
                    image_file = None

                # 3. 發送含有文字和圖片的訊息
                webhook = await self.create_pet_webhook(channel, pet_name, pet.get("avatar"))
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                
                # 準備訊息內容
                message_content = treasure_description
                
                if webhook:
                    try:
                        # Webhook 可以同時發送文字和檔案
                        if isinstance(channel, discord.Thread):
                            await webhook.send(message_content, username=f"{emoji_prefix} {pet_name}", thread=channel, file=image_file if image_file else discord.utils.MISSING)
                        else:
                            await webhook.send(message_content, username=f"{emoji_prefix} {pet_name}", file=image_file if image_file else discord.utils.MISSING)
                        await webhook.delete()
                        
                        # 如果圖片生成失敗，發送備用訊息
                        if not image_file:
                            await channel.send("✨ (想像一下這裡有張閃閃發光的寶物圖片)")
                            
                    except Exception as e:
                        print(f"❌ Webhook 發送失敗: {e}")
                        # Webhook 失敗，回退到普通訊息
                        await channel.send(f"{emoji_prefix} **{pet_name}**: {message_content}", file=image_file if image_file else discord.utils.MISSING)
                        if not image_file:
                            await channel.send("✨ (想像一下這裡有張閃閃發光的寶物圖片)")
                else:
                    # 無法創建 Webhook，使用普通訊息
                    await channel.send(f"{emoji_prefix} **{pet_name}**: {message_content}", file=image_file if image_file else discord.utils.MISSING)
                    if not image_file:
                        await channel.send("✨ (想像一下這裡有張閃閃發光的寶物圖片)")

                # 增加好感度
                self.increase_affection(user_id, 2) # 找到寶物獎勵多一點
                return # 結束事件處理

            # --- Logic for other events ---
            # 使用 Webhook 讓寵物以自己的身份說話
            webhook = await self.create_pet_webhook(channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    # 添加表情符號前綴讓訊息更生動
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    formatted_response = f"{response}"
                    
                    # 如果是在 Thread 中，指定 thread 參數
                    if isinstance(channel, discord.Thread):
                        await webhook.send(formatted_response, username=f"{emoji_prefix} {pet_name}", thread=channel)
                    else:
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

            # 不同事件的好感度影響
            if event_type in ["gift", "dance"]: # treasure_hunt 已在上面處理
                self.increase_affection(user_id, 1)
            elif event_type == "bad_mood":
                # 心情不好時，設置等待回應狀態
                self.pets[user_id]["waiting_for_comfort"] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "channel_id": channel.id,
                    "comfort_timeout": 300  # 5分鐘內需要回應
                }
                self.save_pets_data()
                
                # 添加回應提示
                comfort_embed = discord.Embed(
                    title="💔 寵物需要關愛",
                    description="你的寵物心情不好，需要你的安慰！\n\n🤗 **在此頻道說些溫暖的話來安慰你的寵物吧**\n",
                    color=0xffb6c1
                )
                await channel.send(embed=comfort_embed, delete_after=300)  # 5分鐘後自動刪除提示
                
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
                await self.bot.achievement_manager.check_and_award_achievement(user_id, "pet_adopter", self.bot)
            
            # AI 寵物大師成就 - 成功生成 AI 頭像
            if has_ai_avatar:
                await self.bot.achievement_manager.check_and_award_achievement(user_id, "ai_pet_master", self.bot)
            
            # 寵物語者成就 - 好感度達到50
            if user_str in self.pets:
                affection = self.pets[user_str].get("affection", 0)
                if affection >= 50:
                    await self.bot.achievement_manager.check_and_award_achievement(user_id, "pet_whisperer", self.bot)
            
            # 資深飼主成就 - 相處超過7天
            if user_str in self.pets:
                adopted_date = datetime.datetime.fromisoformat(self.pets[user_str]["adopted_date"])
                days_together = (datetime.datetime.now() - adopted_date).days
                if days_together >= 7:
                    await self.bot.achievement_manager.check_and_award_achievement(user_id, "long_term_owner", self.bot)
                    
        except Exception as e:
            print(f"❌ 檢查寵物成就失敗: {e}")

    async def _check_pet_thread(self, interaction: discord.Interaction) -> bool:
        """檢查互動是否在寵物的專屬 Thread 中"""
        user_id = str(interaction.user.id)
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！使用 `/adopt 寵物名字` 來認養一隻吧！", ephemeral=True)
            return False

        pet = self.pets[user_id]
        thread_id = pet.get("thread_id")

        if not thread_id:
            # 這種情況應該很少見，但作為保險
            await interaction.response.send_message("❌ 你的寵物沒有專屬小窩，請聯繫管理員。", ephemeral=True)
            return False

        if interaction.channel.id != thread_id:
            try:
                thread_mention = f"<#{thread_id}>"
                await interaction.response.send_message(f"❌ 請在你的寵物專屬小窩 {thread_mention} 中與牠互動！", ephemeral=True)
            except discord.errors.NotFound:
                await interaction.response.send_message(f"❌ 你的寵物專屬小窩似乎已被刪除，請聯繫管理員。", ephemeral=True)
            return False
            
        return True

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
                "owner_name": interaction.user.display_name,
                "daily_chat_count": 0,
                "last_chat_date": datetime.datetime.now().strftime("%Y-%m-%d")
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
            
            # 追蹤功能使用
            await track_feature_usage(interaction.user.id, "pet")

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
                value="• `/pet_status` - 查看寵物狀態\n• `/play_ball` - 跟寵物玩球\n• `/feed_pet` - 餵食寵物\n另外，每天可以跟你的寵物聊天互動喔！", 
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
                    await webhook.send(greeting, username=pet_name, thread=thread)
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
            welcome_embed.set_footer(text="所有寵物互動指令都只能在這個小窩裡使用哦！")
            await thread.send(embed=welcome_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ 認養寵物時發生錯誤：{str(e)}")
            print(f"❌ 認養寵物錯誤: {e}")

    @app_commands.command(name="pet_status", description="查看你的寵物狀態和好感度")
    async def pet_status(self, interaction: discord.Interaction):
        """查看寵物狀態：/pet_status"""
        if not await self._check_pet_thread(interaction):
            return

        user_id = str(interaction.user.id)
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
        
        # 追蹤功能使用
        await track_feature_usage(interaction.user.id, "pet")

    @app_commands.command(name="play_ball", description="跟你的寵物玩球遊戲")
    async def play_ball(self, interaction: discord.Interaction):
        """跟寵物玩球：/play_ball"""
        if not await self._check_pet_thread(interaction):
            return

        user_id = str(interaction.user.id)
        pet = self.pets[user_id]
        pet_name = pet["name"]

        # 寵物邀請玩球
        embed = discord.Embed(
            title="🎾 玩球時間！",
            description=f"**{pet_name}** 想要跟你玩球！請選擇一種球：",
            color=0xffd700
        )
        
        view = BallSelectionView(interaction, self)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="feed_pet", description="餵食你的寵物")
    async def feed_pet(self, interaction: discord.Interaction):
        """餵食寵物：/feed_pet"""
        if not await self._check_pet_thread(interaction):
            return
            
        user_id = str(interaction.user.id)
        pet = self.pets[user_id]
        pet_name = pet["name"]

        # 檢查餵食冷卻時間（每小時只能餵一次）
        last_fed = pet.get("last_fed")
        if last_fed:
            time_since_fed = datetime.datetime.now() - datetime.datetime.fromisoformat(last_fed)
            if time_since_fed < datetime.timedelta(hours=1):
                await interaction.response.send_message(f"❌ **{pet_name}** 剛吃飽，請一小時後再餵食哦！")
                return

        # 餵食成功
        foods = ["🍖 美味肉塊", "🐟 新鮮魚肉", "🥕 營養胡蘿蔔", "🍎 甜脆蘋果", "🥛 溫暖牛奶"]
        selected_food = random.choice(foods)
        
        affection_gain = random.randint(2, 4)
        self.increase_affection(user_id, affection_gain)
        
        # 更新餵食時間
        self.pets[user_id]["last_fed"] = datetime.datetime.now().isoformat()
        self.save_pets_data()

        # 使用 AI 生成回應
        context = f"主人餵我吃了 {selected_food.split(' ')[1]}，真好吃！"
        pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet["description"], context)

        embed = discord.Embed(
            title="🍖 餵食成功！",
            description=f"你餵食了 **{pet_name}** {selected_food}！",
            color=0x90ee90
        )
        current_affection = self.pets[user_id].get("affection", 0)
        embed.add_field(name="💖 好感度", value=f"{current_affection} (+{affection_gain})", inline=True)
        
        await interaction.response.send_message(embed=embed)

        # 寵物使用 Webhook 回應
        await asyncio.sleep(1)
        webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
        if webhook:
            try:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                if isinstance(interaction.channel, discord.Thread):
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=interaction.channel)
                else:
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}")
                await webhook.delete()
            except Exception as e:
                print(f"❌ 餵食回應 Webhook 失敗: {e}")
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
        else:
            emoji_prefix = pet.get("avatar_emoji", "🐾")
            await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")

        # 追蹤功能使用
        await track_feature_usage(interaction.user.id, "pet")

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

        embed.set_footer(text="排行榜每 15 分鐘更新一次")
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽訊息以處理寵物安慰互動"""
        # 忽略機器人自己或 Webhook 的訊息
        if message.author.bot:
            return

        user_id = str(message.author.id)

        # 檢查用戶是否有寵物，以及寵物是否在等待安慰
        if user_id not in self.pets or "waiting_for_comfort" not in self.pets[user_id]:

            pet = self.pets[user_id]
            comfort_info = pet.get("waiting_for_comfort")

            # 檢查是否在正確的頻道
            if message.channel.id != comfort_info["channel_id"]:
                return

            # --- Comfort Interaction Logic ---
            # 取得或創建該用戶的鎖
            lock = self.comfort_locks.get(user_id)
            if not lock:
                lock = asyncio.Lock()
                self.comfort_locks[user_id] = lock
            
            # 嘗試獲取鎖，避免競爭條件
            async with lock:
                # 再次檢查狀態，可能在等待鎖的時候狀態已經改變
                # 這次要用 self.pets.get(user_id, {}) 是因為 pet 可能在上鎖前被其他協程改變
                current_pet_data = self.pets.get(user_id, {})
                if "waiting_for_comfort" not in current_pet_data:
                    return

                try:
                    pet_name = current_pet_data["name"]
                    pet_description = current_pet_data["description"]
                    comfort_message = message.content

                    # 移除等待狀態，防止重複觸發
                    comfort_info_backup = current_pet_data.pop("waiting_for_comfort")
                    
                    print(f"💬 正在分析 {message.author.display_name} 對 {pet_name} 的安慰訊息...")

                    # 1. 分析安慰訊息品質
                    quality, analysis = await pet_ai_generator.analyze_comfort_message(pet_name, comfort_message)
                    
                    affection_gains = {"good": 3, "normal": 1, "bad": 0}
                    affection_gain = affection_gains.get(quality, 1)

                    # 2. 更新好感度
                    self.increase_affection(user_id, affection_gain)
                    
                    # 3. 生成寵物回應
                    context = f"主人對我說了「{comfort_message}」，我覺得..."
                    pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context, mood=quality)

                    # 4. 發送結果
                    result_embed = discord.Embed(
                        title="💖 安慰成功！",
                        description=f"你溫暖的話語傳達給了 **{pet_name}**！",
                        color=0x90ee90
                    )
                    result_embed.add_field(name="好感度變化", value=fr"+{affection_gain}", inline=True)
                    await message.channel.send(embed=result_embed)

                    # 5. 寵物使用 Webhook 回應
                    await asyncio.sleep(1)
                    webhook = await self.create_pet_webhook(message.channel, pet_name, current_pet_data.get("avatar"))
                    if webhook:
                        try:
                            emoji_prefix = current_pet_data.get("avatar_emoji", "🐾")
                            if isinstance(message.channel, discord.Thread):
                                await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=message.channel)
                            else:
                                await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}")
                            await webhook.delete()
                        except Exception as e:
                            print(f"❌ 安慰回應 Webhook 失敗: {e}")
                            emoji_prefix = current_pet_data.get("avatar_emoji", "🐾")
                            await message.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
                    else:
                        emoji_prefix = current_pet_data.get("avatar_emoji", "🐾")
                        await message.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")

                    # 保存資料
                    self.save_pets_data()

                except Exception as e:
                    print(f"❌ 處理安慰訊息失敗: {e}")
                    # 如果出錯，恢復等待狀態，避免鎖死
                    if user_id in self.pets:
                        self.pets[user_id]["waiting_for_comfort"] = comfort_info_backup
                        self.save_pets_data()
                        return
                
        """監聽寵物 Thread 中的訊息"""
        # 忽略機器人自己或 Webhook 的訊息
        print(f"🔍 處理訊息：{message.id} 來自 {message.author.display_name} 在 {message.channel.name}")
        if message.author.bot:
            return

        # 檢查訊息是否在一個由 PetSystem 管理的 Thread 中
        user_id = None
        pet_data = None
        for uid, p_data in self.pets.items():
            if p_data.get("thread_id") == message.channel.id:
                user_id = uid
                pet_data = p_data
                break
        
        # 如果不是寵物 Thread，或者找不到對應的寵物資料，則忽略
        if not user_id or not pet_data:
            print(f"🔍 忽略訊息：{message.id}，因為它不在寵物 Thread 中")
            return

        # 檢查發送者是否為寵物主人
        if message.author.id != int(user_id):
            print(f"🔍 忽略訊息：{message.id}，因為它不是寵物主人的訊息")
            return

        # --- 聊天邏輯 ---
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            last_chat_date = pet_data.get("last_chat_date")
            daily_chat_count = pet_data.get("daily_chat_count", 0)

            # 如果是新的一天，重置計數器
            if last_chat_date != today:
                daily_chat_count = 0
                self.pets[user_id]["last_chat_date"] = today

            # 檢查每日聊天次數是否已達上限
            if daily_chat_count >= 3:
                # 可以選擇不回應，或者發送一個寵物累了的訊息（一天一次）
                if pet_data.get("sent_tired_message_today") != today:
                    tired_response = await pet_ai_generator.generate_pet_response(
                        pet_data["name"], 
                        pet_data["description"], 
                        "我今天聊累了，想休息一下",
                        mood="tired"
                    )
                    webhook = await self.create_pet_webhook(message.channel, pet_data["name"], pet_data.get("avatar"))
                    if webhook:
                        try:
                            emoji_prefix = pet_data.get("avatar_emoji", "🐾")
                            await webhook.send(tired_response, username=f"{emoji_prefix} {pet_data['name']}", thread=message.channel)
                            await webhook.delete()
                            self.pets[user_id]["sent_tired_message_today"] = today
                            self.save_pets_data()
                        except Exception as e:
                            print(f"❌ 發送寵物疲勞訊息 Webhook 失敗: {e}")
                return

            # --- 生成並發送 AI 回應 ---
            async with message.channel.typing():
                # 增加好感度
                self.increase_affection(user_id, 1)

                # 生成回應
                pet_response = await pet_ai_generator.generate_chat_response(
                    pet_data["name"],
                    pet_data["description"],
                    message.content,
                    pet_data.get("affection", 0)
                )

                # 使用 Webhook 發送
                webhook = await self.create_pet_webhook(message.channel, pet_data["name"], pet_data.get("avatar"))
                if webhook:
                    try:
                        emoji_prefix = pet_data.get("avatar_emoji", "🐾")
                        await webhook.send(pet_response, username=f"{emoji_prefix} {pet_data['name']}", thread=message.channel)
                        await webhook.delete()
                    except Exception as e:
                        print(f"❌ 聊天回應 Webhook 失敗: {e}")
                        # Fallback
                        emoji_prefix = pet_data.get("avatar_emoji", "🐾")
                        await message.channel.send(f"{emoji_prefix} **{pet_data['name']}**: {pet_response}")
                else:
                    emoji_prefix = pet_data.get("avatar_emoji", "🐾")
                    await message.channel.send(f"{emoji_prefix} **{pet_data['name']}**: {pet_response}")

                # 更新聊天計數
                self.pets[user_id]["daily_chat_count"] = daily_chat_count + 1
                self.save_pets_data()
                
                # 追蹤成就
                await self.bot.achievement_manager.track_feature_usage(int(user_id), "pet_chat")


        except Exception as e:
            print(f"❌ 處理寵物聊天失敗: {e}")


async def setup(bot: commands.Bot):
    """設置並註冊 PetSystem Cog"""
    # 確保 AchievementManager 已經被初始化
    if not hasattr(bot, 'achievement_manager'):
        bot.achievement_manager = AchievementManager()
        print("🔧 初始化 AchievementManager for PetSystem")
        
    await bot.add_cog(PetSystem(bot))
