"""
主機器人程式檔案。

請注意：為了確保所有模組都能正確被找到，
請從專案的根目錄（camp-public-bot）使用以下指令執行此檔案：
python -m src.camp_bot
"""

import os
import asyncio
import discord
from discord.ext import commands

# 由於我們使用 `python -m src.camp_bot` 執行，
# Python 會自動將專案根目錄加入 sys.path，
# 因此我們可以直接從 src 開始 import，無需手動修改 sys.path。
from src import config
from src.utils.user_data import user_data_manager

# --- Bot 初始化 ---

# 設定所需的 Intents
# Intents 允許機器人訂閱特定的伺服器事件。
intents = discord.Intents.default()
intents.message_content = True  # 監聽訊息內容所需 (例如 on_message 事件)
intents.members = True  # 獲取伺服器成員列表所需 (例如用於經驗值系統)

# 建立 Bot 實例
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    """當機器人成功連線並準備好時觸發的事件"""
    print(f"已成功登入為: {bot.user}")
    print(f"機器人 ID: {bot.user.id}")
    # 設定機器人狀態
    activity = discord.Game(name="參加師大資工營中！")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print("機器人狀態已設定完成")
    print("=" * 20)


async def load_cogs():
    """自動載入所有位於 cogs 資料夾中的 cog 模組"""
    print("開始載入 Cogs...")
    if not os.path.isdir(config.COGS_DIR):
        print(f"錯誤：Cogs 目錄 '{config.COGS_DIR}' 不存在。")
        return

    for filename in os.listdir(config.COGS_DIR):
        # 只載入 .py 檔案，並排除 __init__.py 這類特殊檔案
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                # 組合 extension 的完整路徑 (e.g., src.cogs.general)
                extension_name = f"src.cogs.{filename[:-3]}"
                await bot.load_extension(extension_name)
                print(f"  [v] 已成功載入 Cog: {filename}")
            except commands.ExtensionNotFound as e:
                print(f"  [x] 找不到 Cog {filename}: {e}")
            except commands.ExtensionAlreadyLoaded:
                print(f"  [!] Cog {filename} 已經被載入。")
            except commands.NoEntryPointError:
                print(f"  [x] Cog {filename} 缺少必要的 `setup` 函數。")
            except commands.ExtensionFailed as e:
                print(f"  [x] 載入 Cog {filename} 失敗: {e.__class__.__name__} - {e}")
    print("Cogs 載入完畢。")
    print("=" * 20)


async def main():
    """主程式進入點"""
    # 檢查 DISCORD_TOKEN 是否已在 .env 檔案中設定
    if not config.DISCORD_TOKEN:
        print("錯誤：DISCORD_TOKEN 未設定！")
        print("請檢查您的 .env 檔案，並在其中加入 DISCORD_TOKEN='您的機器人TOKEN'。")
        return

    # 使用 async with 來管理 bot 的生命週期，確保連線被妥善關閉
    async with bot:
        await user_data_manager.load_data()  # <-- 在載入 Cogs 前，先載入使用者資料
        await load_cogs()
        print("機器人即將啟動...")
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    # 使用 asyncio.run() 來啟動異步主函數
    # 並加入 graceful shutdown 處理，當使用者按下 Ctrl+C 時可以優雅地關閉
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n收到關閉指令，正在關閉機器人...")
