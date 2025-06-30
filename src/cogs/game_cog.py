import random
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.utils.user_data import user_data_manager
from src.utils.achievements import AchievementManager
from src import config
from .games.rps import RPSView
from .games.guess import GuessButtonView
from .games.slot import slot_game
from .games.dice import dice_game_vs_bot
from .games.utils import check_channel


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.number_games = {}

    async def _check_channel(self, interaction):
        return await check_channel(interaction)

    game = app_commands.Group(name="game", description="玩各種小遊戲")

    @game.command(name="slot", description="拉霸遊戲")
    @app_commands.describe(amount="要下的籌碼數量")
    async def slot(self, interaction: discord.Interaction, amount: int):
        if not await self._check_channel(interaction):
            return
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        current_money = user["money"]
        if amount > current_money:
            await interaction.response.send_message(
                f"你現在只有 {current_money} 元，你卻想花 {amount} 元，我們不支援賒帳系統啦>.<",
                ephemeral=True,
            )
            user["debt"] += 1
            await AchievementManager.check_debt_achievements(
                interaction.user.id, user["debt"], interaction
            )
            await user_data_manager.update_user_data(interaction.user.id, user)
            return
        if amount <= 0:
            await interaction.response.send_message(
                "請輸入大於 0 的金額！", ephemeral=True
            )
            return
        await interaction.response.defer()
        symbols = [
            "<:discord:1385577039838449704>",
            "<:python:1385577058184466502>",
            "<:block:1385577076865630300>",
            "<:mushroom:1385577154775089182>",
            "<:dino:1385577110965321840>",
            "<:money:1385577138727686286>",
            "<:monitor:1385577094393757768>",
        ]
        result_str, winnings, msg, max_count = slot_game(user, amount, symbols)
        user["money"] += winnings
        await user_data_manager.update_user_data(interaction.user.id, user)
        user_name = interaction.user.display_name
        if max_count > 3:
            user_name = interaction.user.mention
        await interaction.followup.send(
            f"# {result_str}\n{user_name} {msg}", ephemeral=True
        )
        await AchievementManager.check_slot_achievements(
            interaction.user.id, max_count, interaction
        )
        await AchievementManager.check_money_achievements(
            interaction.user.id, user["money"], interaction
        )
        
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(interaction.user.id, "game_slot", interaction)

    @game.command(name="dice", description="骰子比大小")
    @app_commands.describe(amount="要下的賭注金額", opponent="挑戰的對手")
    async def dice(
        self,
        interaction: discord.Interaction,
        amount: int,
        opponent: Optional[discord.Member] = None,
    ):
        if not await self._check_channel(interaction):
            return
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        current_money = user["money"]
        if amount <= 0:
            await interaction.response.send_message(
                "請輸入大於 0 的金額！", ephemeral=True
            )
            return
        if opponent and not opponent.bot:
            if opponent == interaction.user:
                await interaction.response.send_message(
                    "你不能挑戰自己啦！", ephemeral=True
                )
                return
            opponent_data = await user_data_manager.get_user(opponent.id, opponent)
            if current_money < amount:
                await interaction.response.send_message(
                    f"你的錢不夠下注 {amount} 元！", ephemeral=True
                )
                return
            if opponent_data["money"] < amount:
                await interaction.response.send_message(
                    f"{opponent.display_name} 的錢不夠接受 {amount} 元的賭注！",
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
            player_roll = random.randint(1, 6)
            opponent_roll = random.randint(1, 6)
            dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
            if player_roll > opponent_roll:
                winnings = amount
                user["money"] += winnings
                opponent_data["money"] -= winnings
                result_msg = f"{interaction.user.mention} 擲出 {dice_emojis[player_roll-1]}，{opponent.mention} 擲出 {dice_emojis[opponent_roll-1]}\n\n{interaction.user.mention} 贏得 {winnings} 元！"
            elif player_roll < opponent_roll:
                winnings = amount
                user["money"] -= winnings
                opponent_data["money"] += winnings
                result_msg = f"{interaction.user.mention} 擲出 {dice_emojis[player_roll-1]}，{opponent.mention} 擲出 {dice_emojis[opponent_roll-1]}\n\n{opponent.mention} 贏得 {winnings} 元！"
            else:
                winnings = 0
                result_msg = f"{interaction.user.mention} 和 {opponent.mention} 都擲出 {dice_emojis[player_roll-1]}，平手！"
            await user_data_manager.update_user_data(interaction.user.id, user)
            await user_data_manager.update_user_data(opponent.id, opponent_data)
            await interaction.followup.send(result_msg)
            await AchievementManager.check_money_achievements(
                interaction.user.id, user["money"], interaction
            )
            await AchievementManager.check_money_achievements(
                opponent.id, opponent_data["money"], interaction
            )
            
            # 追蹤功能使用
            await AchievementManager.track_feature_usage(interaction.user.id, "game_dice", interaction)
        else:
            if current_money < amount:
                await interaction.response.send_message(
                    f"你只有 {current_money} 元，想賭 {amount} 元？去賺點錢再來吧！",
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
            result_text, winnings = dice_game_vs_bot(user, amount)
            if winnings != 0:
                await user_data_manager.update_user_data(interaction.user.id, user)
            await interaction.followup.send(result_text)
            await AchievementManager.check_money_achievements(
                interaction.user.id, user["money"], interaction
            )
            
            # 追蹤功能使用
            await AchievementManager.track_feature_usage(interaction.user.id, "game_dice", interaction)

    @game.command(name="rps", description="剪刀石頭布")
    @app_commands.describe(amount="賭注金額", opponent="挑戰的對手")
    async def rps(
        self,
        interaction: discord.Interaction,
        amount: int,
        opponent: Optional[discord.Member] = None,
    ):
        if not await self._check_channel(interaction):
            return
        if opponent == interaction.user:
            await interaction.response.send_message(
                "你不能挑戰自己啦！", ephemeral=True
            )
            return
        if amount <= 0:
            await interaction.response.send_message(
                "剪刀石頭布必須下注，請輸入大於 0 的金額！", ephemeral=True
            )
            return
        challenger_data = await user_data_manager.get_user(
            interaction.user.id, interaction.user
        )
        if challenger_data["money"] < amount:
            await interaction.response.send_message(
                f"你的錢不夠下注 {amount} 元！", ephemeral=True
            )
            return
        if opponent and not opponent.bot:
            opponent_data = await user_data_manager.get_user(opponent.id, opponent)
            if opponent_data["money"] < amount:
                await interaction.response.send_message(
                    f"{opponent.display_name} 的錢不夠接受 {amount} 元的賭注！",
                    ephemeral=True,
                )
                return
            view = RPSView(interaction.user, opponent, amount)
            await interaction.response.send_message(
                f"{opponent.mention}，{interaction.user.mention} 邀請你來一場剪刀石頭布！賭注為 {amount} 元。請選擇你的出拳：\n"
                f"⚠️ 只有 {interaction.user.mention} 和 {opponent.mention} 可以點擊按鈕！",
                view=view,
            )
        else:
            view = RPSView(interaction.user, self.bot.user, amount)
            await interaction.response.send_message(
                f"來跟我一決勝負吧！賭注 {amount} 元。請出拳：",
                view=view,
                ephemeral=True,
            )

    @game.command(name="guess", description="猜按鈕遊戲")
    @app_commands.describe(amount="要下的賭注金額")
    async def guess(self, interaction: discord.Interaction, amount: int):
        if not await self._check_channel(interaction):
            return
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        current_money = user["money"]
        if amount <= 0:
            await interaction.response.send_message(
                "請輸入大於 0 的金額！", ephemeral=True
            )
            return
        if amount > current_money:
            await interaction.response.send_message(
                f"你只有 {current_money} 元，想賭 {amount} 元？去賺點錢再來吧！",
                ephemeral=True,
            )
            return
        view = GuessButtonView(interaction.user, amount, interaction.channel)
        await interaction.response.send_message(
            "選擇一個按鈕！", view=view, ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
