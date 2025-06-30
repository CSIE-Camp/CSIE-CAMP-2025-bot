"""
NTNU CSIE Camp 2025 Discord Bot

主機器人程式，負責：
- 初始化機器人和必要組件
- 載入所有功能模組 (cogs)
- 管理機器人生命週期

執行方式：
請從專案根目錄執行：python start.py
"""

import os
import asyncio
import discord
from discord.ext import commands

from src import config
from src.utils.user_data import user_data_manager


class CampBot:
    """營隊機器人主類別"""

    def __init__(self):
        # 設定機器人所需的 Discord Intents
        intents = discord.Intents.default()
        intents.message_content = True  # 用於監聽訊息內容
        intents.members = True  # 用於獲取成員資訊（經驗值系統）

        # 建立機器人實例
        self.bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

        # 綁定事件處理器
        self.bot.event(self.on_ready)

        # 新增同步指令
        @self.bot.command()
        @commands.is_owner()
        async def sync(ctx: commands.Context):
            """手動同步斜線指令"""
            await ctx.send("🔄 正在同步斜線指令...")
            try:
                synced = await self.bot.tree.sync()
                await ctx.send(f"✅ 成功全域同步 {len(synced)} 個斜線指令！")
            except Exception as e:
                await ctx.send(f"❌ 同步失敗：{e}")

    async def on_ready(self):
        """機器人啟動完成事件"""
        print(f"✅ 機器人已成功登入：{self.bot.user}")
        print(f"📱 機器人 ID：{self.bot.user.id}")

        # 設定機器人狀態
        activity = discord.Game(name="參加師大資工營中！")
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        print("🎮 機器人狀態已設定完成")

        # 自動同步斜線指令
        try:

            global_synced = await self.bot.tree.sync()
            print(f"🌍 已全域同步 {len(global_synced)} 個斜線指令")
        except Exception as e:
            print(f"⚠️ 斜線指令同步失敗：{e}")

        print("=" * 50)

    async def load_cogs(self):
        """載入所有功能模組"""
        print("🔧 開始載入功能模組...")

        if not os.path.isdir(config.COGS_DIR):
            print(f"❌ 錯誤：模組目錄 '{config.COGS_DIR}' 不存在")
            return

        success_count = 0
        total_count = 0

        for filename in os.listdir(config.COGS_DIR):
            if not (filename.endswith(".py") and not filename.startswith("__")):
                continue

            total_count += 1
            extension_name = f"src.cogs.{filename[:-3]}"

            try:
                await self.bot.load_extension(extension_name)
                print(f"  ✅ {filename}")
                success_count += 1
            except commands.ExtensionNotFound:
                print(f"  ❌ {filename} - 找不到模組")
            except commands.ExtensionAlreadyLoaded:
                print(f"  ⚠️  {filename} - 已載入")
                success_count += 1
            except commands.NoEntryPointError:
                print(f"  ❌ {filename} - 缺少 setup 函數")
            except commands.ExtensionFailed as e:
                print(f"  ❌ {filename} - 載入失敗：{e}")

        print(f"📊 模組載入完成：{success_count}/{total_count}")
        print("=" * 50)

    async def start(self):
        """啟動機器人"""
        if not config.DISCORD_TOKEN:
            print("❌ 錯誤：DISCORD_TOKEN 未設定！")
            print("請檢查 .env 檔案中的 DISCORD_TOKEN 設定")
            return

        async with self.bot:
            # 載入用戶資料
            await user_data_manager.load_data()

            # 載入功能模組
            await self.load_cogs()

            # 啟動機器人
            print("🚀 機器人即將啟動...")
            await self.bot.start(config.DISCORD_TOKEN)


async def main():
    """主程式進入點"""
    camp_bot = CampBot()
    await camp_bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 收到關閉指令，正在關閉機器人...")
    except Exception as e:
        print(f"❌ 機器人運行時發生錯誤：{e}")
