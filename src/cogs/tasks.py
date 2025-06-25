# -*- coding: utf-8 -*-
import discord
from discord.ext import commands, tasks
import datetime
import random
import json
from src.utils.user_data import UserData
from src import config


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = UserData(config.USER_DATA_FILE)
        self.check_in_times = []
        self.schedule_check_in.start()

    def cog_unload(self):
        self.schedule_check_in.cancel()

    @tasks.loop(seconds=1)
    async def schedule_check_in(self):
        """每秒檢查一次是否有排定的限時搶錢活動需要開始"""
        now_timestamp = int(datetime.datetime.now().timestamp())
        # 使用複製的列表進行迭代，避免在迴圈中修改列表
        for event_time in self.check_in_times[:]:
            if now_timestamp == event_time:
                channel = self.bot.get_channel(config.REWARD_CHANNEL_ID)
                if channel:
                    # 使用 create_task 以免阻塞 loop
                    self.bot.loop.create_task(self.run_check_in_event(channel))
                self.check_in_times.remove(event_time)

    @schedule_check_in.before_loop
    async def before_schedule_check_in(self):
        """在 loop 開始前，先等待 bot 上線，並排定所有搶錢活動時間"""
        await self.bot.wait_until_ready()
        self._schedule_all_check_in_events()

    def _schedule_all_check_in_events(self):
        """讀取課程時間並排定所有限時搶錢活動"""
        try:
            with open("data/schedule.json", "r", encoding="utf-8") as f:
                schedule_data = json.load(f)
            lesson_times = [
                datetime.datetime.fromisoformat(item["time"])
                for item in schedule_data["lessons"]
            ]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"無法讀取或解析 schedule.json: {e}")
            return

        # Day 1
        if len(lesson_times) > 5:
            self._schedule_random_time_for_day(
                [lesson_times[2], lesson_times[3]], [lesson_times[4], lesson_times[5]]
            )

        # Day 2
        if len(lesson_times) > 12:
            self._schedule_random_time_for_day(
                [lesson_times[8], lesson_times[9]], [lesson_times[11], lesson_times[12]]
            )

        # Day 3
        if len(lesson_times) > 19:
            self._schedule_random_time_for_day(
                [lesson_times[15], lesson_times[16]],
                [lesson_times[18], lesson_times[19]],
            )

        # Day 4
        if len(lesson_times) > 21:
            self._schedule_random_time_for_day([lesson_times[20], lesson_times[21]])

        print(f"已排定 {len(self.check_in_times)} 個限時搶錢活動。")
        print(f"活動時間戳: {self.check_in_times}")

    def _schedule_random_time_for_day(self, interval1, interval2=None):
        """在給定的1個或2個時間區間中，隨機選擇1個來排程活動"""
        chosen_interval = interval1
        if interval2 and random.choice([True, False]):
            chosen_interval = interval2

        start_time, end_time = chosen_interval
        random_timestamp = random.randint(
            int(start_time.timestamp()), int(end_time.timestamp()) - 1
        )
        self.check_in_times.append(random_timestamp)

    async def run_check_in_event(self, channel: discord.TextChannel):
        """執行限時搶錢活動"""
        limit_amount = 20
        message = await channel.send("限時獎金開搶！")

        thread = await message.create_thread(
            name="限時獎金討論串", auto_archive_duration=60
        )
        info_msg = await thread.send(
            f"點擊下方按鈕搶獎金！還剩 `{limit_amount}` 位名額"
        )

        view = self.CheckInView(self, limit=limit_amount)
        view.message = info_msg
        await info_msg.edit(view=view)
        await view.wait()

        # 活動結束後刪除討論串
        await thread.delete()

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

            if self.remain_amount > 0:
                self.remain_amount -= 1
                self.claimed_users.add(user.id)

                # 發放獎金
                user_account = self.cog.user_data.get_user(user.id)
                reward = random.randint(100, 200)
                user_account["money"] += reward
                self.cog.user_data.save_data()

                await interaction.message.edit(
                    content=f"點擊下方按鈕搶獎金！還剩 `{self.remain_amount}` 位名額"
                )
                await interaction.response.send_message(
                    f"恭喜你搶到 {reward} 元獎金！", ephemeral=True
                )

            if self.remain_amount <= 0:
                button.disabled = True
                await interaction.message.edit(view=self)
                await interaction.followup.send("獎金被搶完了！", ephemeral=False)
                self.stop()

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            await self.message.edit(content="獎金時間結束！", view=self)


async def setup(bot):
    await bot.add_cog(Tasks(bot))
