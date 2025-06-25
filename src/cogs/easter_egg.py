import discord
from discord.ext import commands
import json
import datetime
from src import config
from src.utils.user_data import user_data_manager


class EasterEgg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flags_data = self.load_flags_data()
        self.user_data = user_data_manager

    def load_flags_data(self):
        with open("data/flags.json", "r", encoding="utf-8") as f:
            return json.load(f)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.content in self.flags_data:
            flag_info = self.flags_data[message.content]
            flag_id = flag_info["id"]
            user_id = message.author.id

            user = await self.user_data.get_user(user_id)

            if "found_flags" not in user:
                user["found_flags"] = []

            if flag_id in user.get("found_flags", []):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} 你已經找過這個彩蛋囉！", delete_after=5
                )
                return  # User has already found this flag

            # 從所有使用者資料中計算這個彩蛋被找到的次數
            all_users = self.user_data.users.values()
            found_count = sum(
                1 for u in all_users if flag_id in u.get("found_flags", [])
            )

            if found_count < 3:
                await message.delete()

                user.setdefault("found_flags", []).append(flag_id)
                await self.user_data.update_user_data(user_id, user)

                announcement_channel = self.bot.get_channel(
                    config.EASTER_EGG_CHANNEL_ID
                )
                if announcement_channel:
                    # 將當前找到的人數 +1 作為名次
                    found_order = found_count + 1
                    order_text = {1: "第一位", 2: "第二位", 3: "第三位"}.get(
                        found_order, f"第 {found_order} 位"
                    )

                    embed = discord.Embed(
                        title="🎉 彩蛋尋獲！ 🎉",
                        description=f"**{message.author.mention}** 成功找到了彩蛋！",
                        color=discord.Color.gold(),
                        timestamp=datetime.datetime.now(),
                    )
                    embed.set_thumbnail(url=message.author.display_avatar.url)
                    embed.add_field(
                        name="彩蛋名稱", value=f"`{flag_info['name']}`", inline=False
                    )
                    embed.add_field(
                        name="尋獲成就",
                        value=f"你是**{order_text}**找到此彩蛋的勇者！",
                        inline=False,
                    )
                    embed.set_footer(
                        text=f"由 {self.bot.user.name} 記錄",
                        icon_url=self.bot.user.display_avatar.url,
                    )

                    await announcement_channel.send(embed=embed)

            else:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} 這個彩蛋已經被找到了，下次請早！",
                    delete_after=5,
                )

    @commands.command(name="egg", aliases=["彩蛋"], help="查詢自己找到的彩蛋。")
    async def my_egg(self, ctx):
        """讓使用者查詢自己找到的彩蛋列表"""
        user = await self.user_data.get_user(ctx.author.id)
        found_flags_ids = user.get("found_flags", [])

        if not found_flags_ids:
            return await ctx.send(f"{ctx.author.mention} 你還沒有找到任何彩蛋喔！")

        # 為了方便查找，建立一個從 flag ID 到 flag 名稱的對應字典
        id_to_name = {info["id"]: info["name"] for info in self.flags_data.values()}

        found_flags_names = [
            id_to_name.get(flag_id, f"未知彩蛋 (ID: {flag_id})")
            for flag_id in found_flags_ids
        ]

        embed = discord.Embed(
            title=f"**{ctx.author.display_name}** 找到的彩蛋",
            color=discord.Color.gold(),
        )
        embed.description = "\n".join(f"✅ {name}" for name in found_flags_names)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EasterEgg(bot))
