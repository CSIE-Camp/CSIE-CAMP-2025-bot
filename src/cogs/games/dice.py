import random
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager


def dice_game_vs_bot(user, amount):
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
    return result_text, winnings
