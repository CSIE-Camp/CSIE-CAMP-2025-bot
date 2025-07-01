import random
import discord
from discord.ext import commands
from src.utils.user_data import user_data_manager
from src.utils.achievements import AchievementManager


class RPSView(discord.ui.View):
    def __init__(
        self, challenger: discord.Member, opponent: discord.Member, amount: int, bot: commands.Bot
    ):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.amount = amount
        self.bot = bot
        self.challenger_choice = None
        self.opponent_choice = None

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user not in (self.challenger, self.opponent):
            await interaction.response.send_message(
                "這不是你的遊戲！只有參與對戰的玩家才能選擇。", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="剪刀 ✂️", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "剪刀")

    @discord.ui.button(label="石頭 🗿", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "石頭")

    @discord.ui.button(label="布 📄", style=discord.ButtonStyle.primary)
    async def scissors(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.handle_choice(interaction, "布")

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user == self.challenger:
            self.challenger_choice = choice
        else:
            self.opponent_choice = choice

        await interaction.response.send_message(f"你選擇了 {choice}！", ephemeral=True)

        if self.opponent.bot and self.challenger_choice and not self.opponent_choice:
            bot_choices = ["剪刀", "石頭", "布"]
            self.opponent_choice = random.choice(bot_choices)

        if self.challenger_choice and self.opponent_choice:
            self.stop()
            await self.determine_winner(interaction.channel)

    async def determine_winner(self, channel: discord.TextChannel):
        winner = None
        loser = None
        if self.challenger_choice == self.opponent_choice:
            result_msg = "平手！"
        elif (
            (self.challenger_choice == "石頭" and self.opponent_choice == "剪刀")
            or (self.challenger_choice == "剪刀" and self.opponent_choice == "布")
            or (self.challenger_choice == "布" and self.opponent_choice == "石頭")
        ):
            winner = self.challenger
            loser = self.opponent
            result_msg = f"{self.challenger.mention} 獲勝！"
        else:
            winner = self.opponent
            loser = self.challenger
            result_msg = f"{self.opponent.mention} 獲勝！"

        full_result = f"{self.challenger.mention} 出了 {self.challenger_choice}！\n{self.opponent.mention} 出了 {self.opponent_choice}！\n\n{result_msg}"

        if winner and loser and self.amount > 0:
            winner_data = await user_data_manager.get_user(winner.id, winner)
            loser_data = await user_data_manager.get_user(loser.id, loser)
            winner_data["money"] += self.amount
            loser_data["money"] -= self.amount
            await user_data_manager.update_user_data(winner.id, winner_data)
            await user_data_manager.update_user_data(loser.id, loser_data)
            if not winner.bot:
                full_result += f"\n{winner.mention} 贏得了 {self.amount} 元！"
            else:
                full_result += f"\n{loser.mention} 輸掉了 {self.amount} 元！"
        embed = discord.Embed(
            title = "猜拳結果",
            description = full_result
        )
        await channel.send(embed = embed, silent = True)
        
        # 檢查金錢成就
        for user, data in ((winner, winner_data), (loser, loser_data)):
            if not user.bot:
                await AchievementManager.check_money_achievements(user.id, data["money"], self.bot)

        # 追蹤功能使用（為兩個參與者都追蹤）
        await AchievementManager.track_feature_usage(self.challenger.id, "game_rps", self.bot)
        if not self.opponent.bot:
            await AchievementManager.track_feature_usage(self.opponent.id, "game_rps", self.bot)

