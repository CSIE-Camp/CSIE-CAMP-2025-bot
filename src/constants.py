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
# 格式：(運勢文字, 顏色, 權重)
FORTUNE_LEVELS: List[Tuple[str, int, int]] = [
    ("🌟 不可思議的傳說大吉！", 0xFFD700, 1),  # 金色
    ("🚀 超級無敵大吉！", 0xFF69B4, 3),  # 熱粉色
    ("🎊 無敵大吉！", 0xFF4500, 5),  # 橙紅色
    ("😄 大吉！", 0x32CD32, 10),  # 酸橙綠
    ("😊 中吉！", 0x1E90FF, 30),  # 道奇藍
    ("🙂 普通吉！", 0x9370DB, 50),  # 中紫色
    ("🤔 小吉！", 0xFFA500, 70),  # 橙色
    ("🤏 迷你吉！", 0x808080, 100),  # 灰色
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
    "pet_name": None,
    "pet_affection": 0,
}

# ===== 檔案路徑 =====
DATA_DIR = "data"
BOT_STATE_FILE = f"{DATA_DIR}/bot_state.json"
ACG_QUOTES_FILE = f"{DATA_DIR}/acg_quotes.json"
USER_DATA_FILE = f"{DATA_DIR}/user_data.json"
ACHIEVEMENTS_FILE = f"{DATA_DIR}/achievement.json"
FLAGS_FILE = f"{DATA_DIR}/flags.json"
FLAGS_URL="https://docs.google.com/spreadsheets/d/1crf23wVyL0NPJH6DWcoAw_5qHgNEHUXPl4aaN6xCeHc/export?format=csv"
MYGO_FILE = f"{DATA_DIR}/mygo.json"
SCHEDULE_FILE = f"{DATA_DIR}/schedule.json"
LINKS_FILE = f"{DATA_DIR}/links.json"
NOTES_FILE = f"{DATA_DIR}/notes.json"


# ===== 排行榜設定 =====
SCOREBOARD_UPDATE_INTERVAL = 5  # minutes


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
