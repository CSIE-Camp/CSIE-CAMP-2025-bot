#!/usr/bin/env python3
"""
測試 RPS 遊戲功能的腳本
"""

import asyncio
import discord
from discord.ext import commands
from src.cogs.games import Games, RPSView
from src.utils.user_data import user_data_manager


class MockMember:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.display_name = name
        self.mention = f"@{name}"


class MockInteraction:
    def __init__(self, user, channel):
        self.user = user
        self.channel = channel
        self.response = self.MockResponse()

    class MockResponse:
        async def send_message(self, content, **kwargs):
            print(f"Bot would send: {content}")


class MockChannel:
    async def send(self, content):
        print(f"Channel message: {content}")


async def test_rps_logic():
    """測試 RPS 遊戲邏輯"""
    print("🧪 測試 RPS 遊戲邏輯...")

    # 創建模擬用戶
    user1 = MockMember(123, "Player1")
    user2 = MockMember(456, "Player2")

    # 測試 RPSView
    view = RPSView(user1, user2, 100)

    # 模擬選擇
    view.challenger_choice = "石頭"
    view.opponent_choice = "剪刀"

    # 測試勝負判定
    channel = MockChannel()
    await view.determine_winner(channel)

    print("✅ RPS 邏輯測試完成")


async def test_rps_command():
    """測試 RPS 命令"""
    print("🧪 測試 RPS 命令...")

    # 初始化用戶資料管理器
    await user_data_manager.load_data()

    # 創建模擬機器人和 Games cog
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    games_cog = Games(bot)

    # 創建模擬交互
    user = MockMember(789, "TestUser")
    channel = MockChannel()
    interaction = MockInteraction(user, channel)

    try:
        # 測試對機器人的 RPS 遊戲（不需要金錢）
        await games_cog.rps(interaction, None, 0)
        print("✅ RPS 命令測試完成")
    except Exception as e:
        print(f"❌ RPS 命令測試失敗: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主測試函數"""
    print("🎮 開始測試 RPS 遊戲功能...\n")

    await test_rps_logic()
    print()
    await test_rps_command()

    print("\n🎯 測試完成！")


if __name__ == "__main__":
    asyncio.run(main())
