import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager


class RPSView(discord.ui.View):
    def __init__(
        self, challenger: discord.Member, opponent: discord.Member, amount: int
    ):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.amount = amount
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
    async def rock(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):  # pylint: disable=unused-argument
        await self.handle_choice(interaction, "剪刀")

    @discord.ui.button(label="石頭 🗿", style=discord.ButtonStyle.primary)
    async def paper(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):  # pylint: disable=unused-argument
        await self.handle_choice(interaction, "石頭")

    @discord.ui.button(label="布 📄", style=discord.ButtonStyle.primary)
    async def scissors(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # pylint: disable=unused-argument
    ):
        await self.handle_choice(interaction, "布")

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user == self.challenger:
            self.challenger_choice = choice
        else:
            self.opponent_choice = choice

        await interaction.response.send_message(f"你選擇了 {choice}！", ephemeral=True)

        # 如果對手是機器人，讓機器人自動選擇
        if self.opponent.bot and self.challenger_choice and not self.opponent_choice:
            bot_choices = ["剪刀", "石頭", "布"]
            self.opponent_choice = random.choice(bot_choices)

        if self.challenger_choice and self.opponent_choice:
            self.stop()
            await self.determine_winner(interaction.channel)

    async def determine_winner(self, channel):
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

            full_result += f"\n{winner.mention} 贏得了 {self.amount} 元！"

        await channel.send(full_result)


class GuessButtonView(discord.ui.View):
    def __init__(self, player: discord.Member, amount: int, channel):
        super().__init__(timeout=60)
        self.player = player
        self.amount = amount
        self.channel = channel
        self.winning_button_id = str(random.randint(1, 5))
        self.is_done = False

        for i in range(1, 6):
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
            winnings = self.amount * 4
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
            self.player.id, user["money"], interaction
        )


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.number_games = {}  # For the number guessing game

    game = app_commands.Group(name="game", description="玩各種小遊戲")

    @game.command(name="slot", description="拉霸遊戲")
    @app_commands.describe(amount="要下的籌碼數量")
    async def slot(self, interaction: discord.Interaction, amount: int):
        """拉霸遊戲"""
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        current_money = user["money"]

        if amount > current_money:
            await interaction.response.send_message(
                f"你現在只有 {current_money} 元，你卻想花 {amount} 元，我們不支援賒帳系統啦>.<",
                ephemeral=True,
            )
            user["debt"] += 1
            await achievement_manager.check_debt_achievements(
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

        result = [random.choice(symbols) for _ in range(5)]
        result_str = "".join(result)
        author_mention = interaction.user.mention
        author_name = interaction.user.name

        max_count = max(result.count(symbol) for symbol in set(symbols))
        winnings = 0

        if max_count == 5:
            winnings = 100 * amount
            add_msgs = [
                "原...原來，你的幸運值已經突破系統上限了>.<",
                "是百年難得一見的拉霸奇才！",
                "你該不會駭入系統了吧！？",
            ]
            msg = f"{author_mention} 恭喜你中了五個！！！賺了 {winnings} 元！{random.choice(add_msgs)}"
        elif max_count == 4:
            winnings = 10 * amount
            add_msgs = [
                "搞不好能遇到好事喔~",
                "下一代拉霸幫幫主就是你:O",
                "去找別人單挑猜拳吧",
            ]
            msg = f"{author_mention} 中了四個！！賺了 {winnings} 元！{random.choice(add_msgs)}"
        elif max_count == 3:
            winnings = amount
            msg = f"{author_name} 中了三個！賺了 {winnings} 元！運氣還不錯～"
        elif max_count == 2:
            winnings = -(amount // 2)
            msg = f"有兩個一樣，但還是損失了 {abs(winnings)} 元..."
        else:
            winnings = -amount
            add_msgs = [
                "只能說...菜就多練=v=",
                "也算變相的運氣好...啦T-T",
                "恭喜你把壞運用光了q-q",
            ]
            msg = f"沒有相同的...損失 {abs(winnings)} 元...{random.choice(add_msgs)}"

        user["money"] += winnings
        await user_data_manager.update_user_data(interaction.user.id, user)
        await interaction.followup.send(f"# {result_str}\n{msg}", ephemeral=True)

        await achievement_manager.check_slot_achievements(
            interaction.user.id, max_count, interaction
        )
        await achievement_manager.check_money_achievements(
            interaction.user.id, user["money"], interaction
        )

    @game.command(name="dice", description="骰子比大小")
    @app_commands.describe(amount="要下的賭注金額", opponent="挑戰的對手")
    async def dice(
        self,
        interaction: discord.Interaction,
        amount: int,
        opponent: Optional[discord.Member] = None,
    ):
        """骰子遊戲，支援玩家 vs 玩家 或 玩家 vs 機器人"""
        user = await user_data_manager.get_user(interaction.user.id, interaction.user)
        current_money = user["money"]

        if amount <= 0:
            await interaction.response.send_message(
                "請輸入大於 0 的金額！", ephemeral=True
            )
            return

        if opponent and not opponent.bot:
            # 玩家 vs 玩家
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
            # 雙方擲骰
            player_roll = random.randint(1, 6)
            opponent_roll = random.randint(1, 6)
            dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
            if player_roll > opponent_roll:
                winnings = amount
                user["money"] += winnings
                opponent_data["money"] -= winnings
                result_msg = f"{interaction.user.mention} 擲出 {dice_emojis[player_roll-1]}，{opponent.mention} 擲出 {dice_emojis[opponent_roll-1]}\n\n{interaction.user.mention} 贏得 {winnings} 元！"
            elif player_roll < opponent_roll:
                winner = opponent
                loser = interaction.user
                winnings = amount
                user["money"] -= winnings
                opponent_data["money"] += winnings
                result_msg = f"{interaction.user.mention} 擲出 {dice_emojis[player_roll-1]}，{opponent.mention} 擲出 {dice_emojis[opponent_roll-1]}\n\n{opponent.mention} 贏得 {winnings} 元！"
            else:
                winner = None
                loser = None
                winnings = 0
                result_msg = f"{interaction.user.mention} 和 {opponent.mention} 都擲出 {dice_emojis[player_roll-1]}，平手！"
            await user_data_manager.update_user_data(interaction.user.id, user)
            await user_data_manager.update_user_data(opponent.id, opponent_data)
            await interaction.followup.send(result_msg)
            await achievement_manager.check_money_achievements(
                interaction.user.id, user["money"], interaction
            )
            await achievement_manager.check_money_achievements(
                opponent.id, opponent_data["money"], interaction
            )
        else:
            # 玩家 vs 機器人
            if current_money < amount:
                await interaction.response.send_message(
                    f"你只有 {current_money} 元，想賭 {amount} 元？去賺點錢再來吧！",
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
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
            if winnings != 0:
                await user_data_manager.update_user_data(interaction.user.id, user)
            await interaction.followup.send(result_text)
            await achievement_manager.check_money_achievements(
                interaction.user.id, user["money"], interaction
            )

    @game.command(name="rps", description="剪刀石頭布")
    @app_commands.describe(amount="賭注金額", opponent="挑戰的對手")
    async def rps(
        self,
        interaction: discord.Interaction,
        amount: int,
        opponent: Optional[discord.Member] = None,
    ):
        """剪刀石頭布遊戲"""
        if opponent == interaction.user:
            await interaction.response.send_message(
                "你不能挑戰自己啦！", ephemeral=True
            )
            return

        if amount < 0:
            await interaction.response.send_message(
                "賭注金額不能是負數！", ephemeral=True
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
            # Play against the bot
            if amount > 0:
                # 有賭注時顯示按鈕選擇
                view = RPSView(interaction.user, self.bot.user, amount)
                await interaction.response.send_message(
                    f"來跟我一決勝負吧！賭注 {amount} 元。請出拳：",
                    view=view,
                    ephemeral=True,
                )
            else:
                # 沒有賭注時直接顯示結果
                await self._play_rps_instant(interaction)

    @game.command(name="guess", description="猜按鈕遊戲")
    @app_commands.describe(amount="要下的賭注金額")
    async def guess(self, interaction: discord.Interaction, amount: int):
        """猜按鈕遊戲"""
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

    async def _play_rps_instant(self, interaction: discord.Interaction):
        """即時剪刀石頭布遊戲（無賭注，直接顯示結果）"""
        choices = ["剪刀", "石頭", "布"]
        player_choice = random.choice(choices)
        bot_choice = random.choice(choices)

        # 判定勝負
        if player_choice == bot_choice:
            result_msg = "平手！"
            result_emoji = "🤝"
        elif (
            (player_choice == "石頭" and bot_choice == "剪刀")
            or (player_choice == "剪刀" and bot_choice == "布")
            or (player_choice == "布" and bot_choice == "石頭")
        ):
            result_msg = "你贏了！"
            result_emoji = "🎉"
        else:
            result_msg = "我贏了！"
            result_emoji = "🤖"

        # 選擇對應的 emoji
        choice_emojis = {"剪刀": "✂️", "石頭": "🗿", "布": "📄"}

        await interaction.response.send_message(
            f"{result_emoji} **剪刀石頭布結果**\n\n"
            f"你出了：{choice_emojis[player_choice]} {player_choice}\n"
            f"我出了：{choice_emojis[bot_choice]} {bot_choice}\n\n"
            f"**{result_msg}**",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Games(bot))
