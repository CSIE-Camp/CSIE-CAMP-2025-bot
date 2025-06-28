import asyncio
import discord
from discord.ext import commands
import random

from src import config

class Drama(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="startDrama")
    async def startDrama(self, ctx: commands.Context):
        # if ctx.author.id != 825730483601276929:  # 替換為你的 Discord ID
            # print(f"{ctx.author.display_name} 沒有權限使用這個指令")
            # return

        drama_channel = ctx.guild.get_channel(config.DRAMA_CHANNEL_ID)
        
        # drama_channel_name = "demo區"
        # drama_channel = discord.utils.get(ctx.guild.text_channels, name=f"{drama_channel_name}")

        starfish_webhook = await drama_channel.create_webhook(name="Starfish")
        starfish_avatar = ctx.guild.get_member(825730483601276929).avatar.url
        starfish_name = ctx.guild.get_member(825730483601276929).name

        names = ["一番賞", "二靈古堡", "動物三友會", "使出 Z 招四", "五敵鐵金剛", "六界玩家"]
        random.shuffle(names)

        embed = discord.Embed(title="抽籤結果", description="以下是報告的順序", color=0xff0000)
        for i, name in enumerate(names):
            embed.add_field(name=f"第 {i + 1} 組報告", value=name, inline=False)
        
        await starfish_webhook.send("呼，我到了", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(3)
        await starfish_webhook.send("等我一下喔，現在要抽籤對吧", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(3)
        await starfish_webhook.send("ㄟ！惠惠，幫我抽個籤", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(2)
        await drama_channel.send("你很煩耶，好啦，我在營隊裡也是幫你很多忙ㄟ")
        await asyncio.sleep(3)
        await drama_channel.send("說好的酬勞可別忘了喔...( $ _ $ )")
        await asyncio.sleep(2)
        await starfish_webhook.send("噓...不是，不是說好不能談...$ 了嗎", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(2)
        await drama_channel.send("可是你已經說要...")
        await asyncio.sleep(1)
        msg = await starfish_webhook.send("好啦好啦，會給會給啦，快做事啦", username=starfish_name, avatar_url=starfish_avatar, wait=True)
        await asyncio.sleep(1)
        await msg.add_reaction("😀")
        async with drama_channel.typing():
            await asyncio.sleep(5)
        await drama_channel.send(embed=embed)
        await asyncio.sleep(2)
        await drama_channel.send("抽好了~")
        await asyncio.sleep(3)
        await drama_channel.send("說好的...別忘了喔( •̀ ω •́ )✧")
        await asyncio.sleep(1)
        await starfish_webhook.send("好好好，沒你的戲份了，掰掰", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(3)
        await starfish_webhook.send("如各位所見，以上，就是報告順序！", username=starfish_name, avatar_url=starfish_avatar)
        await asyncio.sleep(2)
        await starfish_webhook.send("抽完籤我就回來啦，等我一下！", username=starfish_name, avatar_url=starfish_avatar)

        starfish_webhook.delete()


async def setup(bot):
    await bot.add_cog(Drama(bot))