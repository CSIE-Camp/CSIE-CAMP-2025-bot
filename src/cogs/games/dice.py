import discord
from discord.ext import commands
import random
from src.utils.achievements import AchievementManager
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager

class DiceView(discord.ui.View):
    def __init__(self,
        player: discord.Member,
        opponent: discord.Member,
        amount: int,
        channel: discord.TextChannel,
        bot: commands.Bot
    ):
        super().__init__(timeout=60)
        self.player = player
        self.opponent = opponent
        self.amount = amount
        self.channel = channel
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user != self.opponent:
            await interaction.response.send_message(
                "這不是對你發起的挑戰！請不要插手他們之間的決鬥！",
                ephemeral = True
            )
            return False
        return True
    
    @discord.ui.button(label="🚩接受挑戰！", style=discord.ButtonStyle.primary)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        msg, result = dice_roll(self.player, self.opponent, self.amount)
        user_data = await user_data_manager.get_user(self.player.id, self.player)
        opponent_data = await user_data_manager.get_user(self.opponent.id, self.opponent)
        if result > 0:
            user_data["money"] += self.amount
            opponent_data["money"] -= self.amount
        elif result < 0:
            user_data["money"] -= self.amount
            opponent_data["money"] += self.amount
        await user_data_manager.update_user_data(self.player.id, user_data)
        await user_data_manager.update_user_data(self.opponent.id, opponent_data)
        embed = discord.Embed(title = "骰子比大小結果", description = msg)
        await interaction.followup.send(embed = embed)
        await AchievementManager.check_money_achievements(
            self.player.id, user_data["money"], self.bot
        )
        await AchievementManager.check_money_achievements(
            self.opponent.id, opponent_data["money"], self.bot
        )
        

# This funciton is no longer used
def dice_game_vs_bot(user, amount):
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    if player_roll > bot_roll:
        winnings = amount
        result_msg = "你贏了！"
        result_emoji = "🎉"
        user["money"] += winnings
    elif player_roll < bot_roll:
        winnings = -amount
        result_msg = "我贏了！"
        result_emoji = "😅"
        user["money"] += winnings
    else:
        winnings = 0
        result_msg = "平手！"
        result_emoji = "🤝"
    result_text = (
        f"{result_emoji} **骰子比大小結果**\n\n"
        f"你擲出了：{dice_emojis[player_roll-1]} **{player_roll} 點**\n"
        f"我擲出了：{dice_emojis[bot_roll-1]} **{bot_roll} 點**\n\n"
        f"**{result_msg}**"
    )
    if winnings > 0:
        result_text += f"\n💰 你贏得了 **{winnings}** 元！"
    elif winnings < 0:
        result_text += f"\n💸 你輸掉了 **{abs(winnings)}** 元..."
    return result_text, winnings

def dice_roll(a: discord.User, b: discord.User, amount: int):
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    rand_a = random.randint(0, 5)
    rand_b = random.randint(0, 5)
    msg = f'{a.mention} 擲出了 {dice_emojis[rand_a]} = **{rand_a + 1}** 點\n\
{b.mention} 擲出了 {dice_emojis[rand_b]} = **{rand_b + 1}** 點\n\n'
    if rand_a > rand_b:
        msg += f'{a.mention} 贏得了 {amount} 元！'
    elif rand_b > rand_a:
        msg += f'{b.mention} 贏得了 {amount} 元！'
    else:
        msg += '平手！'
    return msg, rand_a - rand_b