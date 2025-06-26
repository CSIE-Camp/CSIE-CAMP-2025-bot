"""
應用程式常數定義

集中管理所有硬編碼的常數值，提高代碼的可維護性
"""

from typing import Dict, List, Tuple

# ===== 經驗值系統 =====
DEFAULT_LEVEL = 1
DEFAULT_EXP = 0
DEFAULT_MONEY = 100
EXP_PER_LEVEL = 10

# ===== 進度條設定 =====
PROGRESS_BAR_LENGTH = 10
PROGRESS_BAR_FILLED = "🟩"
PROGRESS_BAR_EMPTY = "⬛"

# ===== 運勢等級配置 =====
FORTUNE_LEVELS: List[Tuple[int, str]] = [
    (1, "🌟 不可思議的傳說大吉！"),
    (3, "🚀 超級無敵大吉！"),
    (5, "🎊 無敵大吉！"),
    (10, "😄 大吉！"),
    (30, "😊 中吉！"),
    (50, "🙂 普通吉！"),
    (70, "🤔 小吉！"),
    (100, "🤏 迷你吉！"),
]

# ===== 名言替換關鍵字 =====
QUOTE_REPLACEMENTS: Dict[str, str] = {
    "oooo": "寫黑客松",
    "ooo": "寫程式",
    "oo": "程式",
    "o": "卷",
    "xx": "Python",
}

# ===== 預設使用者資料結構 =====
DEFAULT_USER_FIELDS: Dict[str, any] = {
    "achievements": [],
    "found_flags": [],
    "sign_in_streak": 0,
    "last_sign_in": None,
}

# ===== 檔案路徑 =====
DATA_DIR = "data"
ACG_QUOTES_FILE = f"{DATA_DIR}/acg_quotes.json"
USER_DATA_FILE = f"{DATA_DIR}/user_data.json"
ACHIEVEMENTS_FILE = f"{DATA_DIR}/achievement.json"
FLAGS_FILE = f"{DATA_DIR}/flags.json"
MYGO_FILE = f"{DATA_DIR}/mygo.json"
SCHEDULE_FILE = f"{DATA_DIR}/schedule.json"


# ===== Discord 嵌入顏色 =====
class Colors:
    """Discord 嵌入訊息顏色常數"""

    PRIMARY = 0x5865F2  # Discord Blurple
    SUCCESS = 0x57F287  # Green
    WARNING = 0xFEE75C  # Yellow
    ERROR = 0xED4245  # Red
    INFO = 0x00D4FF  # Cyan


# ===== 表情符號 =====
class Emojis:
    """常用表情符號"""

    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    MONEY = "💰"
    EXP = "⭐"
    LEVEL = "🏆"


# ===== 訊息模板 =====
class Messages:
    """常用訊息模板"""

    DATA_LOADING = "📁 正在載入資料..."
    DATA_LOADED = "✅ 資料載入完成"
    DATA_SAVE_ERROR = "❌ 資料保存失敗"
    USER_NOT_FOUND = "❌ 找不到指定用戶"
    INSUFFICIENT_PERMISSION = "❌ 權限不足"
    COMMAND_COOLDOWN = "⏰ 指令冷卻中，請稍後再試"
