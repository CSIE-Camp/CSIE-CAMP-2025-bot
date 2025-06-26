import discord
from discord.ext import commands, tasks
from src import config
from src.utils.user_data import user_data_manager
import asyncio


class Scoreboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = user_data_manager
        self.scoreboard_messages = {}  # {category: message}
        self.titles = {
            "money": "💰 **金幣排行榜** 💰",
            "exp": "🌟 **經驗值排行榜** 🌟",
            "achievements": "🏆 **成就排行榜** 🏆",
            "found_flags": "🥚 **彩蛋排行榜** 🥚",
        }
        self.update_scoreboard.start()

    def cog_unload(self):
        self.update_scoreboard.cancel()

    async def _create_leaderboard_text(self, top_users, formatter):
        """Helper to create formatted leaderboard text with medals."""
        if not top_users:
            return "尚無資料"

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, (user_id, data) in enumerate(top_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_mention = user.mention
            except discord.NotFound:
                user_mention = f"`ID:{user_id}`"

            medal = medals.get(i, f"**{i}.**")
            lines.append(f"{medal} {user_mention} - {formatter(data)}")
        return "\n".join(lines)

    async def create_scoreboard_texts(self):
        """Creates a dictionary of text messages for all leaderboards."""
        texts = {}

        # Money Leaderboard
        money_top = self.user_data.get_top_users("money", 3)
        money_list_text = await self._create_leaderboard_text(
            money_top, lambda d: f"**{d.get('money', 0):,}** 🪙"
        )
        money_list_text_indented = money_list_text.replace("\n", "\n> ")
        texts["money"] = f"{self.titles['money']}\n> {money_list_text_indented}"

        # EXP Leaderboard
        exp_top = self.user_data.get_top_users("exp", 3)
        exp_list_text = await self._create_leaderboard_text(
            exp_top, lambda d: f"LV.{d.get('lv', 1)} (**{d.get('exp', 0):,}** EXP)"
        )
        exp_list_text_indented = exp_list_text.replace("\n", "\n> ")
        texts["exp"] = f"{self.titles['exp']}\n> {exp_list_text_indented}"

        # Achievements Leaderboard
        achievements_top = self.user_data.get_top_users("achievements", 3)
        achievements_list_text = await self._create_leaderboard_text(
            achievements_top, lambda d: f"**{len(d.get('achievements', []))}** 個 🎖️"
        )
        achievements_list_text_indented = achievements_list_text.replace("\n", "\n> ")
        texts["achievements"] = (
            f"{self.titles['achievements']}\n> {achievements_list_text_indented}"
        )

        # Easter Eggs Leaderboard
        flags_top = self.user_data.get_top_users("found_flags", 3)
        flags_list_text = await self._create_leaderboard_text(
            flags_top, lambda d: f"**{len(d.get('found_flags', []))}** 個 🥚"
        )
        flags_list_text_indented = flags_list_text.replace("\n", "\n> ")
        texts["found_flags"] = (
            f"{self.titles['found_flags']}\n> {flags_list_text_indented}"
        )

        return texts

    @tasks.loop(minutes=5)
    async def update_scoreboard(self):
        channel = self.bot.get_channel(config.SCOREBOARD_CHANNEL_ID)
        if not channel:
            return

        texts = await self.create_scoreboard_texts()

        for category, text in texts.items():
            message = self.scoreboard_messages.get(category)
            try:
                if message:
                    await message.edit(content=text)
                else:
                    new_message = await channel.send(text)
                    self.scoreboard_messages[category] = new_message
            except discord.NotFound:
                new_message = await channel.send(text)
                self.scoreboard_messages[category] = new_message
            except Exception as e:
                print(f"Error updating scoreboard for {category}: {e}")

    @update_scoreboard.before_loop
    async def before_update_scoreboard(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(config.SCOREBOARD_CHANNEL_ID)
        if not channel:
            return

        self.scoreboard_messages.clear()
        temp_messages = {}

        async for message in channel.history(limit=20):
            if message.author.id == self.bot.user.id:
                for category, title in self.titles.items():
                    if message.content.startswith(title):
                        if category not in temp_messages:
                            temp_messages[category] = message
                        break

        if len(temp_messages) != len(self.titles):
            for msg in temp_messages.values():
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass
            self.scoreboard_messages.clear()
        else:
            self.scoreboard_messages = temp_messages


async def setup(bot):
    await bot.add_cog(Scoreboard(bot))
