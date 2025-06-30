import discord
from discord.ext import commands, tasks
from src import config, constants
from src.utils.user_data import user_data_manager
import asyncio
import json
from pathlib import Path

BOT_STATE_FILE = Path(constants.BOT_STATE_FILE)


class Scoreboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = user_data_manager
        self.scoreboard_message_ids = {}  # {category: message_id}
        self.titles = {
            "money": "💰 **金幣排行榜** 💰",
            "exp": "🌟 **經驗值排行榜** 🌟",
            "achievements": "🏆 **成就排行榜** 🏆",
            "found_flags": "🥚 **彩蛋排行榜** 🥚",
            "pet_affection": "💖 **寵物好感度排行榜** 💖",
        }
        self._load_message_ids()
        self.update_scoreboard.start()

    def _load_message_ids(self):
        """從狀態檔案載入訊息 ID"""
        if not BOT_STATE_FILE.exists():
            return
        try:
            with open(BOT_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.scoreboard_message_ids = {
                    k: int(v) for k, v in data.get("scoreboard_message_ids", {}).items()
                }
                print("✅ Scoreboard message IDs loaded.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error decoding bot state file: {e}. Starting fresh.")
            self.scoreboard_message_ids = {}
        except IOError as e:
            print(f"❌ Error reading bot state file: {e}")
            self.scoreboard_message_ids = {}

    async def _save_message_ids(self):
        """將訊息 ID 儲存到狀態檔案"""
        try:
            data = {}
            if BOT_STATE_FILE.exists():
                try:
                    with open(BOT_STATE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    pass  # Corrupt file, will be overwritten

            data["scoreboard_message_ids"] = self.scoreboard_message_ids
            with open(BOT_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"❌ Failed to save scoreboard message IDs: {e}")

    def cog_unload(self):
        self.update_scoreboard.cancel()

    async def _create_leaderboard_text(self, top_users, formatter):
        """Helper to create formatted leaderboard text with medals."""
        if not top_users:
            return "尚無資料"

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        # Although fetching users one-by-one in a loop can be inefficient,
        # the impact is minimal here since we're only processing the top N (e.g., 3) users.
        for i, (user_id, data) in enumerate(top_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_mention = user.mention
            except discord.NotFound:
                user_mention = f"`ID:{user_id}`"

            medal = medals.get(i, f"**{i}.**")
            lines.append(f"{medal} {user_mention} - {formatter(data)}")
        return "\n".join(lines)

    async def _generate_leaderboard_embed(
        self, category: str, top_n: int, color: discord.Color, formatter
    ):
        """Helper to generate a single leaderboard embed."""
        top_users = self.user_data.get_top_users(category, top_n)
        description = await self._create_leaderboard_text(top_users, formatter)
        return discord.Embed(
            title=self.titles[category], description=description, color=color
        )

    async def create_scoreboard_embeds(self):
        """為所有排行榜建立嵌入式訊息"""
        embeds = {
            "money": await self._generate_leaderboard_embed(
                "money",
                top_n=3,
                color=discord.Color.gold(),
                formatter=lambda d: f"**{d.get('money', 0):,}** 🪙",
            ),
            "exp": await self._generate_leaderboard_embed(
                "exp",
                top_n=3,
                color=discord.Color.green(),
                formatter=lambda d: f"LV.{d.get('lv', 1)} (**{d.get('exp', 0):,}** EXP)",
            ),
            "achievements": await self._generate_leaderboard_embed(
                "achievements",
                top_n=3,
                color=discord.Color.purple(),
                formatter=lambda d: f"**{len(d.get('achievements', []))}** 個成就",
            ),
            "found_flags": await self._generate_leaderboard_embed(
                "found_flags",
                top_n=3,
                color=discord.Color.blue(),
                formatter=lambda d: f"**{len(d.get('found_flags', []))}** 個彩蛋",
            ),
        }
        
        # 添加寵物好感度排行榜
        pet_affection_embed = await self._generate_pet_affection_leaderboard()
        if pet_affection_embed:
            embeds["pet_affection"] = pet_affection_embed
            
        return embeds

    async def _generate_pet_affection_leaderboard(self):
        """生成寵物好感度排行榜"""
        try:
            # 嘗試獲取寵物系統的 cog
            pet_cog = self.bot.get_cog('PetSystem')
            if not pet_cog or not hasattr(pet_cog, 'pets'):
                return None
            
            pets_data = pet_cog.pets
            if not pets_data:
                return discord.Embed(
                    title=self.titles["pet_affection"],
                    description="目前還沒有人認養寵物呢！",
                    color=discord.Color.pink()
                )
            
            # 按好感度排序，取前3名
            sorted_pets = sorted(
                pets_data.items(),
                key=lambda x: x[1].get("affection", 0),
                reverse=True
            )[:3]
            
            if not sorted_pets:
                return discord.Embed(
                    title=self.titles["pet_affection"],
                    description="尚無資料",
                    color=discord.Color.pink()
                )
            
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            lines = []
            
            for i, (user_id, pet_data) in enumerate(sorted_pets, 1):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_mention = user.mention
                except discord.NotFound:
                    user_mention = f"`ID:{user_id}`"
                
                pet_name = pet_data.get("name", "未知寵物")
                affection = pet_data.get("affection", 0)
                
                # 根據好感度顯示愛心等級
                if affection >= 50:
                    love_level = "💕💕💕"
                elif affection >= 30:
                    love_level = "💕💕"
                elif affection >= 15:
                    love_level = "💕"
                else:
                    love_level = "💖"
                
                medal = medals.get(i, f"**{i}.**")
                lines.append(f"{medal} {user_mention} 的 **{pet_name}** {love_level}\n好感度：**{affection}**")
            
            description = "\n\n".join(lines) if lines else "尚無資料"
            
            return discord.Embed(
                title=self.titles["pet_affection"],
                description=description,
                color=discord.Color.pink()
            )
            
        except Exception as e:
            print(f"❌ 生成寵物好感度排行榜時發生錯誤: {e}")
            return None

    @tasks.loop(minutes=constants.SCOREBOARD_UPDATE_INTERVAL)
    async def update_scoreboard(self):
        channel = self.bot.get_channel(config.SCOREBOARD_CHANNEL_ID)
        if not channel:
            print("❌ Scoreboard channel not found.")
            return

        embeds = await self.create_scoreboard_embeds()

        for category, embed in embeds.items():
            message_id = self.scoreboard_message_ids.get(category)
            message = None

            if message_id:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed)
                except discord.NotFound:
                    message = None  # Message was deleted, create a new one
                except discord.Forbidden:
                    print(f"❌ Lacking permissions to edit message {message_id}")
                    continue  # Skip this category
                except discord.HTTPException as e:
                    print(f"❌ Failed to edit message {message_id}: {e}")
                    continue

            if not message:
                try:
                    new_message = await channel.send(embed=embed)
                    self.scoreboard_message_ids[category] = new_message.id
                except discord.Forbidden:
                    print(f"❌ Lacking permissions to send messages in {channel.name}")
                    return  # Stop the update if we can't send messages
                except discord.HTTPException as e:
                    print(f"❌ Failed to send message for {category}: {e}")

        await self._save_message_ids()

    @update_scoreboard.before_loop
    async def before_update_scoreboard(self):
        await self.bot.wait_until_ready()
        # Delay the first run slightly to ensure user data is fully loaded
        await asyncio.sleep(10)


async def setup(bot: commands.Bot):
    await bot.add_cog(Scoreboard(bot))
