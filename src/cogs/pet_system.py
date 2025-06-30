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

from discord import app_commands, ui
from discord.ext import commands
import discord

from src.utils.user_data import user_data_manager
from src import config
from src.utils.llm import generate_text
from src.utils.pet_ai import pet_ai_generator
from src.utils.achievements import AchievementManager, track_feature_usage
from src.utils.image_gen import generate_image
import random
import datetime
import asyncio
import json
import os
import base64
from typing import Dict, Any, Optional
from io import BytesIO

# --- Views ---

class BallSelectionView(ui.View):
    """選擇球的互動視圖"""
    def __init__(self, original_interaction: discord.Interaction, cog: 'PetSystem'):
        super().__init__(timeout=180) # 3 分鐘後超時
        self.original_interaction = original_interaction
        self.cog = cog
        self.owner_id = original_interaction.user.id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ 這不是你的寵物，不能幫牠決定要玩什麼球！", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        try:
            # 編輯原始訊息，移除按鈕並顯示超時訊息
            timeout_embed = discord.Embed(
                title="🤔 選擇時間太久了...",
                description=f"{self.cog.pets[str(self.owner_id)]['name']} 等得不耐煩，跑去玩別的了。",
                color=0xf39c12
            )
            await self.original_interaction.edit_original_response(embed=timeout_embed, view=None)
        except discord.errors.NotFound:
            # 原始互動可能已被刪除，忽略即可
            pass
        except Exception as e:
            print(f"❌ 處理玩球視圖超時失敗: {e}")

    @discord.ui.button(label="紅色橡膠球", style=discord.ButtonStyle.red, emoji="🔴")
    async def red_ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_ball_selection(interaction, "紅色橡膠球", 2)

    @discord.ui.button(label="藍色網球", style=discord.ButtonStyle.primary, emoji="🔵")
    async def blue_ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_ball_selection(interaction, "藍色網球", 3)

    @discord.ui.button(label="會吱吱叫的玩具", style=discord.ButtonStyle.green, emoji="🧸")
    async def squeaky_toy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_ball_selection(interaction, "會吱吱叫的玩具", 4)

    async def handle_ball_selection(self, interaction: discord.Interaction, ball_type: str, affection_gain: int):
        """處理球的選擇"""
        user_id = str(interaction.user.id)
        pet = self.cog.pets[user_id]
        pet_name = pet["name"]

        # 立即回應，避免逾時
        embed = discord.Embed(
            title=f"🎾 你丟出了 **{ball_type}**！",
            description=f"**{pet_name}** 看著球飛了出去...",
            color=0x3498db
        )
        await interaction.response.edit_message(embed=embed, view=None) # 編輯原訊息，移除按鈕

        # 背景處理 AI 回應和資料更新
        async with interaction.channel.typing():
            context = f"主人跟我玩一顆 {ball_type}"
            pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet["description"], context)
            
            self.cog.increase_affection(user_id, affection_gain)
            self.cog.pets[user_id]["last_played"] = datetime.datetime.now().isoformat()
            self.cog.save_pets_data()

            result_embed = discord.Embed(
                title=f"🎉 和 **{pet_name}** 玩得很開心！",
                description=f"💖 好感度 +{affection_gain}",
                color=0x2ecc71
            )
            current_affection = self.cog.pets[user_id].get("affection", 0)
            result_embed.add_field(name="💖 目前好感度", value=str(current_affection))
            
            # 使用 followup 發送結果
            await interaction.followup.send(embed=result_embed, ephemeral=True)

            # 使用 Webhook 發送寵物回應
            webhook = await self.cog.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=interaction.channel)
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 玩球回應 Webhook 失敗: {e}")
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
            else:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")

        await track_feature_usage(interaction.user.id, "pet")


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
                    loaded_pets = data.get("pets", {})
                    
                    # 將頭像 base64 字串轉換回 bytes
                    for user_id, pet_data in loaded_pets.items():
                        if "avatar" in pet_data and pet_data["avatar"] and isinstance(pet_data["avatar"], str):
                            try:
                                pet_data["avatar"] = base64.b64decode(pet_data["avatar"])
                            except (base64.binascii.Error, TypeError):
                                pet_data["avatar"] = None # 如果解碼失敗，設為 None
                        self.pets[user_id] = pet_data

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

    def save_pets_data(self):
        """保存寵物資料"""
        try:
            # 創建可序列化的寵物資料副本
            serializable_pets = {}
            for user_id, pet_data in self.pets.items():
                pet_copy = pet_data.copy()
                # 將頭像 bytes 轉換為 base64 字串以便序列化
                if "avatar" in pet_copy and isinstance(pet_copy["avatar"], bytes):
                    pet_copy["avatar"] = base64.b64encode(pet_copy["avatar"]).decode('utf-8')
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
            "bad_mood": (220, 260),
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
            
            # 好感度-2
            old_affection = pet.get("affection", 0)
            new_affection = max(0, old_affection - 2)  # 確保不會變成負數
            self.pets[user_id]["affection"] = new_affection
            
            # 清除等待安慰狀態
            if "waiting_for_comfort" in self.pets[user_id]:
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
                        description=f"**{pet_name}** 等了很久都沒有等到主人的安慰...\n💔 好感度 -2",
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
                await AchievementManager.check_and_award_achievement(user_id, "pet_adopter", self.bot)
            
            # AI 寵物大師成就 - 成功生成 AI 頭像
            if has_ai_avatar:
                await AchievementManager.check_and_award_achievement(user_id, "ai_pet_master", self.bot)

            # 寵物語者成就 - 好感度達到50
            if user_str in self.pets:
                affection = self.pets[user_str].get("affection", 0)
                if affection >= 50:
                    await AchievementManager.check_and_award_achievement(user_id, "pet_whisperer", self.bot)
            
            # 資深飼主成就 - 相處超過7天
            if user_str in self.pets:
                adopted_date = datetime.datetime.fromisoformat(self.pets[user_str]["adopted_date"])
                days_together = (datetime.datetime.now() - adopted_date).days
                if days_together >= 4:
                    await AchievementManager.check_and_award_achievement(user_id, "long_term_owner", self.bot)

        except Exception as e:
            print(f"❌ 檢查寵物成就失敗: {e}")

    def _format_cooldown(self, time_left: datetime.timedelta) -> str:
        """格式化剩餘冷卻時間"""
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours} 小時 {minutes} 分鐘"
        elif minutes > 0:
            return f"{minutes} 分鐘 {seconds} 秒"
        else:
            return f"{seconds} 秒"

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
        print(f"🤖 正在為 {pet_name} 生成獨特個性...")
        await interaction.response.defer(ephemeral=True) # 先延遲回應，避免逾時
        
        user_id = str(interaction.user.id)
        
        # 檢查是否已經有寵物
        if user_id in self.pets:
            await interaction.followup.send(f"❌ 你已經有一隻寵物了：**{self.pets[user_id]['name']}**！", ephemeral=True)
            return

        # 檢查名字長度
        if len(pet_name) > 20:
            await interaction.followup.send("❌ 寵物名字太長了！請使用20個字元以內的名字。", ephemeral=True)
            return

        try:
            await interaction.followup.send(f"🔍 正在為你尋找最適合的寵物 **{pet_name}**...", ephemeral=True)

            # 使用 AI 生成寵物個性
            print(f"🤖 正在為 {pet_name} 生成獨特個性...")
            description = await pet_ai_generator.generate_pet_personality(pet_name)
            print(f"💬 {pet_name} 的個性: {description}")

            # 生成寵物頭像
            avatar_data, avatar_emoji = await self.generate_pet_avatar(pet_name, description)

            # 創建專屬討論串
            if not isinstance(interaction.channel, (discord.TextChannel, discord.ForumChannel)):
                 await interaction.edit_original_response(content="❌ 無法在此頻道類型創建寵物小窩，請在一般的文字頻道使用此指令。")
                 return

            thread_name = f"{avatar_emoji} {pet_name} 的小窩"
            try:
                thread = await interaction.channel.create_thread(name=thread_name, type=discord.ChannelType.private_thread)
            except discord.Forbidden:
                 await interaction.followup.send("⚠️ 機器人權限不足以創建私密討論串，將改為創建公開討論串。", ephemeral=True)
                 thread = await interaction.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
            
            await thread.add_user(interaction.user)

            # 創建寵物資料
            self.pets[user_id] = {
                "name": pet_name,
                "description": description,
                "affection": 10,
                "adopted_date": datetime.datetime.now().isoformat(),
                "last_fed": None,
                "last_played": None,
                "channel_id": interaction.channel.id,
                "thread_id": thread.id,
                "avatar": avatar_data,
                "avatar_emoji": avatar_emoji,
                "waiting_for_comfort": None
            }
            
            self.pet_timers[user_id] = self.generate_all_timers()
            self.comfort_locks[user_id] = asyncio.Lock()
            
            self.save_pets_data()

            # 在新 Thread 中發送歡迎訊息
            welcome_embed = discord.Embed(
                title=f"🎉 歡迎來到 {pet_name} 的小窩！",
                description=f"從今天起，這裡就是 **{pet_name}** 和你的專屬空間了！\n\n> {description}\n\n記得常常回來看看牠，跟牠互動喔！",
                color=0x7289da
            )
            welcome_embed.set_footer(text="使用 /pet_status 查看寵物狀態")
            
            webhook = await self.create_pet_webhook(thread, pet_name, avatar_data)
            if webhook:
                try:
                    await webhook.send(embed=welcome_embed, username=f"{avatar_emoji} {pet_name}", thread=thread)
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 歡迎訊息 Webhook 失敗: {e}")
                    await thread.send(embed=welcome_embed)
            else:
                await thread.send(embed=welcome_embed)

            await interaction.edit_original_response(content=f"✅ 恭喜！你已成功認養 **{pet_name}**！快到牠的專屬小窩 {thread.mention} 看看吧！")

            await self.check_pet_achievements(interaction.user.id, has_ai_avatar=(avatar_data is not None))
            
            user_data = await user_data_manager.get_user(interaction.user)
            user_data["pet_name"] = pet_name
            user_data["pet_affection"] = self.pets[user_id]["affection"]
            await user_data_manager.update_user_data(interaction.user.id, user_data)

            await track_feature_usage(interaction.user.id, "pet_adoption")

        except discord.Forbidden:
            await interaction.edit_original_response(content="❌ 機器人權限不足，無法創建討論串或 Webhook。請檢查伺服器設定。")
        except Exception as e:
            print(f"❌ 認養寵物失敗: {e}")
            try:
                await interaction.edit_original_response(content=f"❌ 認養寵物時發生未知錯誤，請稍後再試。")
            except discord.errors.NotFound:
                await interaction.followup.send(content=f"❌ 認養寵物時發生未知錯誤，請稍後再試。", ephemeral=True)

    @app_commands.command(name="pet_status", description="查看你的寵物狀態和好感度")
    async def pet_status(self, interaction: discord.Interaction):
        """查看寵物狀態：/pet_status"""
        if not await self._check_pet_thread(interaction):
            return

        user_id = str(interaction.user.id)
        pet = self.pets[user_id]
        
        embed = discord.Embed(
            title=f"{pet['avatar_emoji']} {pet['name']} 的狀態",
            description=f"*“{pet['description']}”*",
            color=discord.Color.blue()
        )
        
        if pet.get('avatar'):
            # 如果頭像是 bytes，需要先存檔再附加
            file = discord.File(BytesIO(pet['avatar']), filename="avatar.png")
            embed.set_thumbnail(url="attachment://avatar.png")
        else:
            file = None

        embed.add_field(name="💖 好感度", value=str(pet.get("affection", 0)), inline=True)
        
        adopted_date = datetime.datetime.fromisoformat(pet["adopted_date"])
        days_together = (datetime.datetime.now() - adopted_date).days
        embed.add_field(name="📅 相處天數", value=f"{days_together} 天", inline=True)

        if pet.get("last_fed"):
            last_fed_time = datetime.datetime.fromisoformat(pet["last_fed"])
            embed.add_field(name="上次餵食", value=f"<t:{int(last_fed_time.timestamp())}:R>", inline=False)
        
        if pet.get("last_played"):
            last_played_time = datetime.datetime.fromisoformat(pet["last_played"])
            embed.add_field(name="上次玩球", value=f"<t:{int(last_played_time.timestamp())}:R>", inline=False)

        if pet.get("waiting_for_comfort"):
            embed.add_field(name="目前心情", value="💔 需要你的安慰...", inline=False)

        embed.set_footer(text=f"主人: {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
        await track_feature_usage(interaction.user.id, "pet")

    @app_commands.command(name="play_ball", description="跟你的寵物玩球遊戲(冷卻時間: 6小時)")
    async def play_ball(self, interaction: discord.Interaction):
        """跟寵物玩球：/play_ball"""
        if not await self._check_pet_thread(interaction):
            return

        user_id = str(interaction.user.id)
        pet = self.pets[user_id]
        
        # 檢查冷卻時間
        cooldown = datetime.timedelta(hours=6)
        if pet.get("last_played"):
            last_played_time = datetime.datetime.fromisoformat(pet["last_played"])
            time_since_played = datetime.datetime.now() - last_played_time
            if time_since_played < cooldown:
                time_left = cooldown - time_since_played
                await interaction.response.send_message(f"⏳ **{pet['name']}** 還在休息，請在 **{self._format_cooldown(time_left)}** 後再跟牠玩。", ephemeral=True)
                return

        embed = discord.Embed(
            title=f"🎾 要跟 **{pet['name']}** 玩哪種球呢？",
            description="選擇一顆球丟給牠吧！",
            color=0x3498db
        )
        view = BallSelectionView(interaction, self)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="feed_pet", description="餵食你的寵物(冷卻時間: 8小時)")
    async def feed_pet(self, interaction: discord.Interaction):
        """餵食寵物：/feed_pet"""
        if not await self._check_pet_thread(interaction):
            return

        user_id = str(interaction.user.id)
        pet = self.pets[user_id]
        pet_name = pet["name"]

        cooldown = datetime.timedelta(hours=8)
        if pet.get("last_fed"):
            last_fed_time = datetime.datetime.fromisoformat(pet["last_fed"])
            time_since_fed = datetime.datetime.now() - last_fed_time
            if time_since_fed < cooldown:
                time_left = cooldown - time_since_fed
                await interaction.response.send_message(f"⏳ **{pet_name}** 的肚子還很飽，請在 **{self._format_cooldown(time_left)}** 後再餵牠。", ephemeral=True)
                return

        await interaction.response.defer()
        
        async with interaction.channel.typing():
            context = "主人餵我吃了好吃的東西"
            pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet["description"], context)
            
            affection_gain = random.randint(2, 4)
            self.increase_affection(user_id, affection_gain)
            
            self.pets[user_id]["last_fed"] = datetime.datetime.now().isoformat()
            self.save_pets_data()

            embed = discord.Embed(
                title=f"🍖 **{pet_name}** 吃得津津有味！",
                description=f"💖 好感度 +{affection_gain}",
                color=0x2ecc71
            )
            current_affection = self.pets[user_id].get("affection", 0)
            embed.add_field(name="💖 目前好感度", value=str(current_affection))
            
            await interaction.followup.send(embed=embed)

            webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=interaction.channel)
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 餵食回應 Webhook 失敗: {e}")
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
            else:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await interaction.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")

        await track_feature_usage(interaction.user.id, "pet")

    @app_commands.command(name="pet_ranking", description="查看寵物好感度排行榜")
    async def pet_ranking(self, interaction: discord.Interaction):
        """查看寵物好感度排行榜：/pet_ranking"""
        if not self.pets:
            await interaction.response.send_message("現在還沒有任何寵物喔！", ephemeral=True)
            return

        sorted_pets = sorted(self.pets.items(), key=lambda item: item[1].get("affection", 0), reverse=True)
        
        embed = discord.Embed(title="💖 寵物好感度排行榜", color=0xffd700)
        
        description = ""
        for i, (user_id, pet) in enumerate(sorted_pets[:10]):
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_name = user.display_name
            except:
                user_name = "未知用戶"
            
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            emoji = rank_emoji[i] if i < len(rank_emoji) else f"**#{i+1}**"
            description += f"{emoji} **{pet['name']}** (主人: {user_name}) - {pet.get('affection', 0)} 好感度\n"

        if not description:
            description = "還沒有任何寵物可以排名。"
            
        embed.description = description
        await interaction.response.send_message(embed=embed)
        await track_feature_usage(interaction.user.id, "pet_ranking")

    @app_commands.command(name="show_off_pet", description="在公共頻道炫耀你的寵物")
    async def show_off_pet(self, interaction: discord.Interaction):
        """炫耀寵物：/show_off_pet"""
        user_id = str(interaction.user.id)
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！", ephemeral=True)
            return

        pet = self.pets[user_id]
        pet_name = pet["name"]
        
        await interaction.response.defer()

        async with interaction.channel.typing():
            context = "主人正在向大家炫耀我，我該說些什麼好呢？"
            pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet["description"], context)

            embed = discord.Embed(
                title=f"🌟 {interaction.user.display_name} 的愛寵登場！",
                description=f"來看看可愛的 **{pet_name}**！",
                color=discord.Color.gold()
            )
            
            if pet.get('avatar'):
                file = discord.File(BytesIO(pet['avatar']), filename="avatar.png")
                embed.set_thumbnail(url="attachment://avatar.png")
            else:
                file = None

            embed.add_field(name="💖 好感度", value=str(pet.get("affection", 0)))
            embed.set_footer(text=f"“{pet['description']}”")

            await interaction.followup.send(embed=embed, file=file)

            webhook = await self.create_pet_webhook(interaction.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}")
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 炫耀回應 Webhook 失敗: {e}")
            
        await track_feature_usage(interaction.user.id, "pet")

    @app_commands.command(name="pet_thread", description="快速前往你的寵物專屬小窩")
    async def pet_thread(self, interaction: discord.Interaction):
        """前往寵物討論串：/pet_thread"""
        user_id = str(interaction.user.id)
        if user_id not in self.pets:
            await interaction.response.send_message("❌ 你還沒有認養寵物！", ephemeral=True)
            return

        thread_id = self.pets[user_id].get("thread_id")
        if not thread_id:
            await interaction.response.send_message("❌ 找不到你的寵物小窩。", ephemeral=True)
            return
            
        thread = self.bot.get_channel(thread_id)
        if thread:
            await interaction.response.send_message(f"🏠 點擊這裡前往你的寵物小窩: {thread.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 你的寵物小窩好像不見了...", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        if user_id not in self.pets:
            return

        pet = self.pets.get(user_id)
        if not pet or not pet.get("waiting_for_comfort"):
            return

        waiting_info = pet["waiting_for_comfort"]
        if message.channel.id != waiting_info["channel_id"]:
            return

        # 使用鎖確保一次只處理一個安慰訊息
        lock = self.comfort_locks.get(user_id)
        if not lock or lock.locked():
            return

        async with lock:
            # 再次檢查狀態，防止競爭條件
            pet = self.pets.get(user_id)
            if not pet or not pet.get("waiting_for_comfort"):
                return

            # 清除等待狀態
            del self.pets[user_id]["waiting_for_comfort"]
            self.save_pets_data()

            pet_name = pet["name"]
            pet_description = pet["description"]
            
            async with message.channel.typing():
                # 分析安慰訊息品質
                analysis_result = await pet_ai_generator.analyze_comfort_message(pet_name, pet_description, message.content)
                score = analysis_result["score"]
                reasoning = analysis_result["reasoning"]
                
                # 根據分數調整好感度
                self.increase_affection(user_id, score)
                
                # 生成寵物回應
                context = f"主人對我說了「{message.content}」，我的心情因此有了轉變。({reasoning})"
                pet_response = await pet_ai_generator.generate_pet_response(pet_name, pet_description, context)

            # 發送結果
            result_embed = discord.Embed(
                title="💖 安慰成功",
                description=f"你溫暖的話語傳達給了 **{pet_name}**！",
                color=0x90ee90
            )
            result_embed.add_field(name="📈 好感度變化", value=f"+{score}", inline=True)
            result_embed.add_field(name="💭 AI 分析", value=reasoning, inline=True)
            await message.reply(embed=result_embed, mention_author=False)

            # 寵物使用 Webhook 回應
            webhook = await self.create_pet_webhook(message.channel, pet_name, pet.get("avatar"))
            if webhook:
                try:
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await webhook.send(pet_response, username=f"{emoji_prefix} {pet_name}", thread=message.channel)
                    await webhook.delete()
                except Exception as e:
                    print(f"❌ 安慰回應 Webhook 失敗: {e}")
                    emoji_prefix = pet.get("avatar_emoji", "🐾")
                    await message.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")
            else:
                emoji_prefix = pet.get("avatar_emoji", "🐾")
                await message.channel.send(f"{emoji_prefix} **{pet_name}**: {pet_response}")

            await track_feature_usage(message.author.id, "pet_comfort")

async def setup(bot: commands.Bot):
    await bot.add_cog(PetSystem(bot))
