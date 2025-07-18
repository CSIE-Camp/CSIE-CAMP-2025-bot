"""
Discord 機器人的設定檔案
載入並定義所有環境變數和應用程式設定
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()


def get_int_env(key: str) -> Optional[int]:
    """安全地取得整數型環境變數"""
    value = os.getenv(key)
    return int(value) if value else None


# ===== 基本設定 =====
ADMIN_ROLE_ID = get_int_env("ADMIN_ROLE_ID")
PLAYER_ROLE_IDS = [
    int(role_id)
    for role_id in os.getenv("PLAYER_ROLE_IDS", "").split(",")
    if role_id.strip().isdigit()
]

# ===== API Keys =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HUGGINGFACE_IMAGE_GEN_MODEL = os.getenv("HUGGINGFACE_IMAGE_GEN_MODEL")

# ===== 檔案路徑 =====
COGS_DIR = "src/cogs"
DATA_DIR = "data"
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "data/user_data.json")


# ===== 主要頻道 ID =====
SCOREBOARD_CHANNEL_ID = get_int_env("SCOREBOARD_CHANNEL_ID")
ANNOUNCEMENT_CHANNEL_ID = get_int_env("ANNOUNCEMENT_CHANNEL_ID")
MAIN_ANNOUNCEMENT_CHANNEL_ID = get_int_env("MAIN_ANNOUNCEMENT_CHANNEL_ID")

# ===== 風格轉換頻道 ID =====
STYLE_TRANSFER_WENYAN_CHANNEL_ID = get_int_env("STYLE_TRANSFER_WENYAN_CHANNEL_ID")
STYLE_TRANSFER_CATGIRL_CHANNEL_ID = get_int_env("STYLE_TRANSFER_CATGIRL_CHANNEL_ID")
STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID = get_int_env(
    "STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID"
)
STYLE_TRANSFER_TSUNDERE_CHANNEL_ID = get_int_env("STYLE_TRANSFER_TSUNDERE_CHANNEL_ID")
STYLE_TRANSFER_SAKIKO_CHANNEL_ID = get_int_env("STYLE_TRANSFER_SAKIKO_CHANNEL_ID")

# ===== 演戲頻道 ID =====
DRAMA_CHANNEL_ID = get_int_env("DRAMA_CHANNEL_ID")

# ===== 風格轉換 Webhook URLs =====
STYLE_TRANSFER_WENYAN_WEBHOOK_URL = os.getenv("STYLE_TRANSFER_WENYAN_WEBHOOK_URL")
STYLE_TRANSFER_CATGIRL_WEBHOOK_URL = os.getenv("STYLE_TRANSFER_CATGIRL_WEBHOOK_URL")
STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL = os.getenv(
    "STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL"
)
STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL = os.getenv("STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL")
STYLE_TRANSFER_SAKIKO_WEBHOOK_URL = os.getenv("STYLE_TRANSFER_SAKIKO_WEBHOOK_URL")

# ===== 風格轉換設定映射 =====
STYLE_TRANSFER_CONFIG = {
    "wenyan": {
        "channel_id": STYLE_TRANSFER_WENYAN_CHANNEL_ID,
        "webhook_url": STYLE_TRANSFER_WENYAN_WEBHOOK_URL,
        "character": "東漢書院諸葛亮",
        "description": "文言文風格",
    },
    "catgirl": {
        "channel_id": STYLE_TRANSFER_CATGIRL_CHANNEL_ID,
        "webhook_url": STYLE_TRANSFER_CATGIRL_WEBHOOK_URL,
        "character": "你的專屬貓娘",
        "description": "貓娘風格",
    },
    "chuunibyou": {
        "channel_id": STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID,
        "webhook_url": STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL,
        "character": "漆黑的墮天使",
        "description": "中二風格",
    },
    "tsundere": {
        "channel_id": STYLE_TRANSFER_TSUNDERE_CHANNEL_ID,
        "webhook_url": STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL,
        "character": "傲嬌大小姐",
        "description": "傲嬌風格",
    },
    "sakiko": {
        "channel_id": STYLE_TRANSFER_SAKIKO_CHANNEL_ID,
        "webhook_url": STYLE_TRANSFER_SAKIKO_WEBHOOK_URL,
        "character": "豐川祥子",
        "description": "祥子風格",
    },
}

# ===== 遊戲允許頻道設定 =====
# 以逗號分隔多個頻道 ID，例如：123,456,789
ALLOWED_GAME_CHANNEL_IDS = os.getenv("ALLOWED_GAME_CHANNEL_IDS", "").split(",")
ALLOWED_GAME_CHANNEL_IDS = [
    int(cid) for cid in ALLOWED_GAME_CHANNEL_IDS if cid.strip().isdigit()
]  # 轉為 int 並過濾空值

# ===== 除錯設定 =====
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
