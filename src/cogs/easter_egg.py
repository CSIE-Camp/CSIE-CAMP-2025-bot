import discord
from discord import app_commands
from discord.ext import commands
import json
import datetime
from src import config
from src.utils.user_data import user_data_manager
from src.constants import Colors, FLAGS_FILE


class EasterEgg(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.flags_data = self.load_flags_data()
		self.user_data = user_data_manager

	def load_flags_data(self) -> dict[str, dict[str,]]:
		with open(FLAGS_FILE, "r", encoding="utf-8") as f:
			return json.load(f)
	
	@app_commands.command(name="ls", description="???")
	async def ls(self, interaction: discord.Interaction):
		await interaction.response.defer(thinking = True, ephemeral = True)

		await interaction.followup.send("```sh\n$ ls\nTOTAL 1 FILE(S)```\n`kajsdlifjawoiefjsjcavlkasjdlfkjlk.txt`\n")

	@app_commands.command(name="cat", description="???")
	@app_commands.describe(file="FILE")
	async def cat(self, interaction: discord.Interaction, file: str):
		await interaction.response.defer(thinking = True, ephemeral = True)

		if file == "kajsdlifjawoiefjsjcavlkasjdlfkjlk.txt":
			await interaction.followup.send(f"(*NOT IMPLEMENTED*)\n```sh\n$ cat {file}```\n`flag{{||5c1291bf52f7784ebb250c70b67fa3||}}`\n")
		else:
			await interaction.followup.send(f"\n```\n$ cat {file}\n```\ncat: {file} No such file or directory")


	
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		if message.author.bot:
			return
		if message.content in self.flags_data:	
			if not any(role.name in ['新身分', '公測玩家'] for role in message.author.roles):
				await message.author.send(
					f'{message.author.mention} 只有「公測玩家」可以找彩蛋喔！',
					delete_after = 5
				)
				await message.delete()
				return
			flag_info = self.flags_data[message.content]
			flag_id = flag_info["id"]
			user_id = message.author.id

			user = await self.user_data.get_user(user_id)

			if "found_flags" not in user:
				user["found_flags"] = []

			if flag_id in user.get("found_flags", []):
				await message.delete()
				await message.author.send(
					f"{message.author.mention} 你已經找過這個彩蛋囉！", delete_after=5
				)
				return  # User has already found this flag

			# 從所有使用者資料中計算這個彩蛋被找到的次數
			all_users = self.user_data.users.values()
			found_count = sum(
				1 for u in all_users if flag_id in u.get("found_flags", [])
			)

			if found_count < flag_info["amount"]:
				await message.delete()

				user.setdefault("found_flags", []).append(flag_id)
				await self.user_data.update_user_data(user_id, user)

				announcement_channel = self.bot.get_channel(
					config.ANNOUNCEMENT_CHANNEL_ID
				)
				if announcement_channel:
					# 將當前找到的人數 +1 作為名次
					found_order = found_count + 1

					embed = discord.Embed(
						title="🎉 彩蛋尋獲！ 🎉",
						description=f"**{message.author.mention}** 成功找到了彩蛋！",
						color=Colors.WARNING,
						timestamp=datetime.datetime.now(),
					)
					embed.set_thumbnail(url=message.author.display_avatar.url)
					embed.add_field(
						name="彩蛋名稱", value=f"`{flag_info['name']}`", inline=False
					)
					embed.add_field(
						name="尋獲成就",
						value=f"你是**第 {found_order}/{int(flag_info['amount'])} 個**找到此彩蛋的勇者！",
						inline=False,
					)
					embed.set_footer(
						text=f"使用 /egg 查詢你的彩蛋收藏！",
						icon_url=self.bot.user.display_avatar.url,
					)

					await announcement_channel.send(embed=embed)

			else:
				await message.delete()
				await message.author.send(
					f"{message.author.mention} 這個彩蛋已經被找到了，下次請早！",
					delete_after=5,
				)

	@app_commands.command(name="egg", description="查詢自己找到的彩蛋。")
	async def my_egg(self, interaction: discord.Interaction):
		"""讓使用者查詢自己找到的彩蛋列表"""
		user = await self.user_data.get_user(interaction.user.id)
		found_flags_ids = user.get("found_flags", [])

		if not found_flags_ids:
			await interaction.response.send_message(
				f"{interaction.user.mention} 你還沒有找到任何彩蛋喔！",
				ephemeral = True
			)
			return

		embed = discord.Embed(
			title=f"🥚 {interaction.user.display_name} 的彩蛋收藏",
			color=Colors.INFO,
		)

		all_flags_map = {v["id"]: v for k, v in self.flags_data.items()}

		found_flags_info = [
			all_flags_map[flag_id]
			for flag_id in found_flags_ids
			if flag_id in all_flags_map
		]

		if found_flags_info:
			egg_list = ""
			for flag in found_flags_info:
				egg_list += f"- **{flag['name']}**\n"
			embed.description = egg_list
		else:
			embed.description = "你還沒有找到任何彩蛋喔！"

		embed.set_footer(
			text=f"已找到 {len(found_flags_ids)} / {len(self.flags_data)} 個彩蛋"
		)
		await interaction.response.send_message(
			embed = embed,
			ephemeral = True
		)


async def setup(bot: commands.Bot):
	await bot.add_cog(EasterEgg(bot))
