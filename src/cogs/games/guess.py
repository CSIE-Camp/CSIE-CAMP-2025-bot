import random
import discord
from discord.ext import commands
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager


class GuessButtonView(discord.ui.View):
    def __init__(self, player: discord.Member, amount: int, channel, bot: commands.Bot):
        super().__init__(timeout=60)
        self.player = player
        self.amount = amount
        self.channel = channel
        self.bot = bot
        self.winning_button_id = str(random.randint(1, 5))
        self.is_done = False
        for i in range(1, 5):
            button = discord.ui.Button(
                label=f"按鈕 {i}",
                style=discord.ButtonStyle.secondary,
                custom_id=str(i),
            )
            button.callback = self.button_callback
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user == self.player

    async def button_callback(self, interaction: discord.Interaction):
        if self.is_done:
            await interaction.response.send_message("遊戲已經結束了！", ephemeral=True)
            return
        self.is_done = True
        self.stop()
        user = await user_data_manager.get_user(self.player.id, self.player)
        chosen_id = interaction.data["custom_id"]
        for child in self.children:
            child.disabled = True
        if chosen_id == self.winning_button_id:
            winnings = self.amount * 3
            user["money"] += winnings
            result_message = f"{self.player.mention} 猜對了！贏得了 {winnings} 元！"
            interaction.message.components[0].children[
                int(chosen_id) - 1
            ].style = discord.ButtonStyle.success
        else:
            winnings = -self.amount
            user["money"] += winnings
            result_message = (
                f"{self.player.mention} 猜錯了...輸掉了 {abs(winnings)} 元。"
            )
            interaction.message.components[0].children[
                int(chosen_id) - 1
            ].style = discord.ButtonStyle.danger
            interaction.message.components[0].children[
                int(self.winning_button_id) - 1
            ].style = discord.ButtonStyle.success
        await user_data_manager.update_user_data(self.player.id, user)
        await interaction.response.edit_message(view=self)
        await self.channel.send(result_message)
        await achievement_manager.check_money_achievements(
            self.player.id, user["money"], self.bot
        )
