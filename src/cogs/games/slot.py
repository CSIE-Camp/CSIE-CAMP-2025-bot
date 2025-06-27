import random
from src.utils.user_data import user_data_manager
from src.utils.achievements import achievement_manager


def slot_game(user, amount, symbols):
    result = [random.choice(symbols) for _ in range(5)]
    result_str = "".join(result)
    max_count = max(result.count(symbol) for symbol in set(symbols))
    winnings = 0
    if max_count == 5:
        winnings = 100 * amount
        add_msgs = [
            "原...原來，你的幸運值已經突破系統上限了>.<",
            "是百年難得一見的拉霸奇才！",
            "你該不會駭入系統了吧！？",
        ]
        msg = f"恭喜你中了五個！！！賺了 {winnings} 元！{random.choice(add_msgs)}"
    elif max_count == 4:
        winnings = 10 * amount
        add_msgs = [
            "搞不好能遇到好事喔~",
            "下一代拉霸幫幫主就是你:O",
            "去找別人單挑猜拳吧",
        ]
        msg = f"中了四個！！賺了 {winnings} 元！{random.choice(add_msgs)}"
    elif max_count == 3:
        winnings = amount
        msg = f"中了三個！賺了 {winnings} 元！運氣還不錯～"
    elif max_count == 2:
        winnings = -(amount // 2)
        msg = f"有兩個一樣，但還是損失了 {abs(winnings)} 元..."
    else:
        winnings = -amount
        add_msgs = [
            "只能說...菜就多練=v=",
            "也算變相的運氣好...啦T-T",
            "恭喜你把壞運用光了q-q",
        ]
        msg = f"沒有相同的...損失 {abs(winnings)} 元...{random.choice(add_msgs)}"
    return result_str, winnings, msg, max_count
