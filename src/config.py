import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- API Keys ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NGROK_URL = os.getenv("NGROK_URL")

# --- Paths ---
COGS_DIR = "src/cogs"
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")

# --- Channel IDs ---
MYGO_CHANNEL_ID = int(os.getenv("MYGO_CHANNEL_ID", "0"))
REWARD_CHANNEL_ID = int(os.getenv("REWARD_CHANNEL_ID", "0"))
