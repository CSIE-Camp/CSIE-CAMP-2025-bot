import discord
from discord import app_commands
from discord.ext import commands, tasks
import random

# 導入共享的 user_data_manager 以確保資料操作的同步與一致性
from src.utils.user_data import user_data_manager
from src import config


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.random_red_packet_loop.start()

    def cog_unload(self):
        self.random_red_packet_loop.cancel()

    @tasks.loop(hours=1)
    async def random_red_packet_loop(self):
        """每小時檢查一次，有機率觸發隨機紅包雨"""
        # 每小時有 20% 的機率觸發
        if random.random() < 0.2:
            channel = self.bot.get_channel(config.REWARD_CHANNEL_ID)
            if channel:
                # 隨機決定這次紅包可以被搶的人數
                limit = random.randint(10, 25)
                await self.run_check_in_event(channel, limit)

    @random_red_packet_loop.before_loop
    async def before_random_red_packet_loop(self):
        """在 loop 開始前，先等待 bot 上線"""
        await self.bot.wait_until_ready()

    @app_commands.command(name="redpacket", description="手動觸發一個紅包雨/搶錢活動。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(limit="可以搶紅包的人數上限")
    async def red_packet(self, interaction: discord.Interaction, limit: int = 20):
        """手動觸發一個紅包雨/搶錢活動。"""
        await self.run_check_in_event(interaction.channel, limit)
        await interaction.response.send_message(
            f"已在 {interaction.channel.mention} 發起一個 {limit} 人名額的紅包雨！",
            ephemeral=True,
        )

    async def run_check_in_event(self, channel: discord.TextChannel, limit_amount: int):
        """執行限時搶錢活動"""
        view = self.CheckInView(self, limit=limit_amount)
        message = await channel.send(
            f"點擊下方按鈕搶獎金！還剩 `{limit_amount}` 位名額", view=view
        )
        view.message = message

    class CheckInView(discord.ui.View):
        def __init__(self, cog_instance, limit: int):
            super().__init__(timeout=600)  # 10 分鐘後 view 失效
            self.cog = cog_instance
            self.limit = limit
            self.claimed_users = set()
            self.remain_amount = limit
            self.message = None

        @discord.ui.button(label="我要搶！", style=discord.ButtonStyle.success)
        async def claim_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            user = interaction.user

            if user.id in self.claimed_users:
                await interaction.response.send_message(
                    "你已經搶過了！", ephemeral=True
                )
                return

            if self.remain_amount <= 0:
                await interaction.response.send_message(
                    "獎金已經被搶完了！", ephemeral=True
                )
                return

            self.remain_amount -= 1
            self.claimed_users.add(user.id)

            # 發放獎金，並傳入 user 物件以更新使用者名稱
            user_account = await user_data_manager.get_user(user)
            reward = random.randint(100, 200)
            user_account["money"] += reward
            await user_data_manager.update_user_data(user.id, user_account)

            await interaction.response.send_message(
                f"恭喜你搶到 {reward} 元獎金！", ephemeral=True
            )

            if self.remain_amount > 0:
                await self.message.edit(
                    content=f"點擊下方按鈕搶獎金！還剩 `{self.remain_amount}` 位名額"
                )
            else:
                button.disabled = True
                await self.message.edit(content="獎金被搶完了！", view=self)
                self.stop()

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(content="獎金時間結束！", view=self)


async def setup(bot):
    await bot.add_cog(Tasks(bot))
