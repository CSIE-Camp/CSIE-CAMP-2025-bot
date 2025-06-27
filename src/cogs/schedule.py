import discord
from discord import app_commands
from discord.ext import commands
import json
import datetime
import random

from src.constants import SCHEDULE_FILE


class Schedule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lessons = self.load_schedule()

    def load_schedule(self):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        lessons = []
        for item in data["lessons"]:
            lessons.append(
                {
                    "name": item["name"],
                    "time": datetime.datetime.fromisoformat(item["time"]),
                }
            )
        return lessons

    def _get_fancy_reply(self, lesson_name, remaining_minutes, now):
        """根據目前課程、剩餘時間和當前時間生成一個有趣的額外回覆。"""
        additional_messages = []

        if now.hour < 3 or now.hour >= 22:
            additional_messages = [
                "現在是凌晨耶:O，快去睡覺",
                "~~這麼爆肝，很有成為工程師的潛力喔~~",
                "你...怎麼那麼晚還在想我(/////)",
            ]

        if lesson_name == "報到":
            additional_messages = [
                "歡迎來到資工營！",
                "居然有人已經發現這個功能了",
                "我以為這裡是主控台ㄟ，你怎麼闖進來的",
            ]
        elif lesson_name == "開幕":
            additional_messages = [
                "愉快的資工營終於開始了~",
                "開戲明明很精采鴨，我的魅力那麼高嗎(////)",
            ]
        elif lesson_name == "午餐時間":
            additional_messages = ["吃飯時間>v<", "有沒有順便帶我的午餐來0.0"]
        elif lesson_name == "晚餐時間":
            additional_messages = [
                "晚餐吃得飽，隔天精神好0v0",
                "不...不要偷看我吃晚餐(>////<)",
            ]
        elif lesson_name == "晚上活動":
            additional_messages = [
                "現在正在活動，別跟我聊天了啦> <",
                "我也正在享受活動~猜猜我在哪~",
            ]
        elif lesson_name == "黑客松 & 吃午餐":
            if remaining_minutes < 10:
                additional_messages = [
                    "等等...為什麼你還有閒情逸致跟我聊天=v=",
                    "幫我撐 10 分鐘",
                ]
            elif remaining_minutes < 30:
                additional_messages = [
                    "最後衝刺！加油加油！",
                    "你們可以的！",
                    "時間快不夠了，我來偷偷幫你吧~\n...阿...我忘記我沒有手了> <",
                ]
            elif remaining_minutes < 60:
                additional_messages = [
                    "最後衝刺！加油加油！",
                    "你想問我要怎麼做嗎，我才不會告訴你> <",
                ]
            else:
                additional_messages = [
                    "我的想法一定超有創意，可惜我不能講話( •̀ ω •́ )✧",
                    "黑客松加油~",
                ]

        if additional_messages:
            return random.choice(additional_messages)
        return None

    @app_commands.command(
        name="schedule", description="查詢目前課程、剩餘時間、下個課程。"
    )
    @app_commands.describe(custom_time="要查詢的自訂時間(格式: mmddHHMM)")
    async def query_schedule(
        self, interaction: discord.Interaction, custom_time: str = None
    ):
        """查詢目前課程、剩餘時間、下個課程。可選填 mmddHHMM 格式的自訂時間。"""
        now = datetime.datetime.now()
        if custom_time:
            try:
                now = datetime.datetime.strptime(custom_time, "%m%d%H%M")
                now = now.replace(year=datetime.datetime.now().year)  # Use current year
            except ValueError:
                await interaction.response.send_message(
                    "請輸入正確的時間格式：`mmddHHMM`", ephemeral=True
                )
                return

        current_lesson = None
        next_lesson = None

        for i, lesson in enumerate(self.lessons):
            if lesson["time"] > now:
                if i > 0:
                    current_lesson = self.lessons[i - 1]
                next_lesson = lesson
                break
        else:
            current_lesson = self.lessons[-1]

        embed = None
        fancy_reply = None
        remaining_minutes = 0

        if current_lesson:
            embed = discord.Embed(title="課表查詢", color=0x00FF00)
            embed.add_field(name="目前課程", value=current_lesson["name"], inline=False)
            embed.set_footer(text="NTNU CSIE Camp 2025")

            if next_lesson:
                remaining_time = next_lesson["time"] - now
                remaining_minutes = remaining_time.total_seconds() / 60
                remaining_str = str(
                    datetime.timedelta(seconds=int(remaining_time.total_seconds()))
                )

                embed.add_field(
                    name="距離下個課程還有", value=remaining_str, inline=False
                )
                embed.add_field(
                    name="下個課程", value=next_lesson["name"], inline=False
                )
            else:
                embed.description = "所有課程都結束囉！"

            fancy_reply = self._get_fancy_reply(
                current_lesson["name"], remaining_minutes, now
            )

        else:
            embed = discord.Embed(
                title="課表查詢", description="營隊還沒開始喔！", color=0xFF0000
            )

        await interaction.response.send_message(embed=embed)
        if fancy_reply:
            await interaction.followup.send(fancy_reply)


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot))
