import random
import discord
import datetime
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.utils.user_data import user_data_manager
from src.utils.achievements import AchievementManager
from src.cogs.games.rps import RPSView
from src.cogs.games.dice import DiceView
from src.cogs.games.guess import GuessButtonView
from src.cogs.games.slot import slot_game
from src.cogs.games import dice
from src.cogs.games.utils import check_channel


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.number_games = {}

    async def _check_channel(self, interaction):
        return await check_channel(interaction)

    @staticmethod
    async def in_class_game_check(interaction: discord.Interaction, amount: int, user: dict):
        now = datetime.datetime.now()
        if  datetime.datetime(2025, 7, 1, 13, 30) < now < datetime.datetime(2025, 7, 1, 17, 30) or\
            datetime.datetime(2025, 7, 2,  9, 40) < now < datetime.datetime(2025, 7, 2, 12, 10) or\
            datetime.datetime(2025, 7, 2, 13, 30) < now < datetime.datetime(2025, 7, 2, 15,  0) or\
            datetime.datetime(2025, 7, 2, 15, 10) < now < datetime.datetime(2025, 7, 2, 17, 40) or\
            datetime.datetime(2025, 7, 3,  9, 40) < now < datetime.datetime(2025, 7, 3, 12, 10) or\
            datetime.datetime(2025, 7, 3, 13, 30) < now < datetime.datetime(2025, 7, 3, 15,  0):
            if random.randint(0, 99) != 0:
                embed = discord.Embed(
                    title = '被發現了…',
                    description = f"你在上課玩賭錢被老師發現，\n所以老師贏了。\n{interaction.user.mention} 輸掉了 {amount} 元！"
                )
                await interaction.response.send_message(embed=embed)
                user["money"] -= amount
                if user["money"] < 0:
                    user["money"] = 0
                return True
        return False

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
                interaction.user.id, user["debt"], self.bot
            )
            await user_data_manager.update_user_data(interaction.user.id, user)
            return
        if amount <= 0:
            await interaction.response.send_message(
                "請輸入大於 0 的金額！", ephemeral=True
            )
            return

        if await self.in_class_game_check(interaction, amount * 2, user):
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
            interaction.user.id, max_count, self.bot
        )
        await AchievementManager.check_money_achievements(
            interaction.user.id, user["money"], self.bot
        )

        # 追蹤功能使用
        await AchievementManager.track_feature_usage(
            interaction.user.id, "game_slot", self.bot
        )

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

        if await self.in_class_game_check(interaction, amount * 2, user):
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
            
            view = DiceView(interaction.user, opponent, amount, interaction.channel, self.bot)
            await interaction.response.send_message(
                f"{opponent.mention}，{interaction.user.mention} 邀請你來一場骰子比大小！賭注為 {amount} 元。請確認是否接受對決：\n"
                f"⚠️ 只有 {opponent.mention} 可以點擊按鈕！",
                view=view,
            )
        else:
            if current_money < amount:
                await interaction.response.send_message(
                    f"你只有 {current_money} 元，想賭 {amount} 元？去賺點錢再來吧！",
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
            msg, result = dice.dice_roll(interaction.user, self.bot.user, amount)
            if result > 0:
                user["money"] += amount
            elif result < 0:
                user["money"] -= amount
            if result != 0:
                await user_data_manager.update_user_data(interaction.user.id, user)
            embed = discord.Embed(title = "骰子比大小結果", description = msg)
            await interaction.followup.send(embed = embed)
            await AchievementManager.check_money_achievements(
                    interaction.user.id, user["money"], self.bot
            )
        # 追蹤功能使用
        await AchievementManager.track_feature_usage(
            interaction.user.id, "game_dice", self.bot
        )

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
        
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        if await self.in_class_game_check(interaction, amount * 2, user):
            return
        
        if opponent and not opponent.bot:
            opponent_data = await user_data_manager.get_user(opponent.id, opponent)
            if opponent_data["money"] < amount:
                await interaction.response.send_message(
                    f"{opponent.display_name} 的錢不夠接受 {amount} 元的賭注！",
                    ephemeral=True,
                )
                return
            view = RPSView(interaction.user, opponent, amount, self.bot)
            await interaction.response.send_message(
                f"{opponent.mention}，{interaction.user.mention} 邀請你來一場剪刀石頭布！賭注為 {amount} 元。請選擇你的出拳：\n"
                f"⚠️ 只有 {interaction.user.mention} 和 {opponent.mention} 可以點擊按鈕！",
                view=view,
            )
        else:
            view = RPSView(interaction.user, self.bot.user, amount, self.bot)
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

        if await self.in_class_game_check(interaction, amount * 2, user):
            return
        
        view = GuessButtonView(interaction.user, amount, interaction.channel, self.bot)
        await interaction.response.send_message(
            "選擇一個按鈕！", view=view, ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
