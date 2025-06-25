# Discord Bot - 師大資工營 2025

這是一個為師大資工營設計的多功能 Discord 機器人專案。它採用了模組化的架構，將不同的功能分離到各自的 Cog 中，並透過統一的設定檔進行管理，以提高程式碼的可讀性、可維護性和擴充性。

## ✨ 功能亮點

-   **🎲 遊戲與經濟系統**

    -   **每日簽到**：使用者可以透過 `?sign_in` 或 `?簽到` 進行每日簽到，獲得金錢獎勵，連續簽到有額外獎勵。
    -   **經驗值系統**：在頻道中發言可以獲得經驗值並升級。
    -   **個人資料**：使用 `?profile`、`?p` 或 `?資料` 查詢自己或他人的等級、經驗與金錢。
    -   **拉霸機**：使用 `?slot <金額>` 或 `?拉霸 <金額>` 指令，體驗刺激的拉霸遊戲，根據相同圖案的數量決定輸贏與倍率。
    -   **限時搶錢**：定時在特定頻道出現的搶錢活動，增加伺服器活躍度。

-   **🤖 AI 智慧互動**

    -   **LLM 聊天**：當有人在頻道中提及 (mention) 機器人時，它會使用 Google Gemini 模型進行智慧回應。
    -   **MyGo 圖片搜尋**：在指定頻道中，輸入關鍵字即可搜尋《It's MyGO!!!!!》的相關梗圖。

-   **🔧 通用與管理工具**
    -   **抽籤運勢**：使用 `?抽籤` 指令，獲得今日運勢和一句動漫名言，並由 AI 生成專屬配圖。
    -   **動態重載**：管理員可以使用 `?reload <cog_name>` 指令，在不重啟機器人的情況下，即時更新功能模組。

## 📂 專案結構

```
.env                # 儲存所有機密資訊與環境變數
README.md           # 就是你現在正在看的這個檔案
requirement.txt     # 專案所需的 Python 套件
data/
  ├── acg_quotes.json # 抽籤系統所使用的名言資料
  └── user_data.json  # 儲存所有使用者的等級、金錢等資料
src/
  ├── __init__.py
  ├── camp_bot.py     # 機器人的主程式進入點
  ├── config.py       # 讀取 .env 並提供全域設定
  ├── cogs/           # 存放所有功能模組 (Cogs)
  │   ├── __init__.py
  │   ├── admin.py      # 管理員指令
  │   ├── ai.py         # AI 相關功能 (LLM, MyGo)
  │   ├── game_events.py# 遊戲事件處理 (如：發言加經驗)
  │   ├── general.py    # 通用指令 (抽籤, 連結)
  │   ├── schedule.py   # 課表查詢
  │   ├── sign_in.py    # 簽到系統
  │   ├── slot.py       # 拉霸機遊戲
  │   └── tasks.py      # 背景排程任務 (限時搶錢)
  └── utils/          # 存放共用的工具函式
      ├── __init__.py
      ├── image_gen.py  # AI 圖片生成工具
      └── user_data.py  # 使用者資料管理
```

## 🚀 安裝與設定

1.  **複製專案**

    ```bash
    git clone https://github.com/CSIE-Camp/camp-public-bot.git
    cd camp-public-bot
    ```

2.  **安裝依賴套件**
    建議在虛擬環境中進行安裝。

    ```bash
    pip install -r requirement.txt
    ```

3.  **設定環境變數**
    複製 `.env.example` (如果有的話) 或手動建立一個名為 `.env` 的新檔案，並填入以下內容：

    ```properties
    # --- 機器人金鑰 ---
    DISCORD_TOKEN="你的 Discord Bot Token"

    # --- API 金鑰 ---
    GEMINI_API_KEY="你的 Google Gemini API Key"
    NGROK_URL="你的圖片生成服務 Ngrok URL"

    # --- 檔案路徑 (通常不需要修改) ---
    USER_DATA_FILE="data/user_data.json"

    # --- 頻道 ID ---
    # 將 ID 換成你伺服器中對應的頻道 ID
    MYGO_CHANNEL_ID="123456789012345678"
    REWARD_CHANNEL_ID="123456789012345678"
    ```

    > **如何取得 Discord 頻道 ID？**
    > 進入 Discord -> 使用者設定 -> 進階 -> 開啟「開發者模式」。然後在頻道上按右鍵，選擇「複製頻道 ID」。

## ▶️ 如何執行

**請務必**從專案的根目錄 (`camp-public-bot`) 執行以下指令來啟動機器人。這能確保 Python 正確地將 `src` 視為一個可匯入的套件。

```bash
python -m src.camp_bot
```

當您在終端機看到 `已成功登入為: YourBotName` 的訊息時，表示機器人已成功啟動並上線。
