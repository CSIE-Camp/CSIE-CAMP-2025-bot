# NTNU CSIE Camp 2025 Public Bot

This is the official Discord bot for the NTNU CSIE Camp 2025. It's designed to enhance the camp experience with a variety of fun and interactive features, including multiple AI-powered functions.

## Features

### 般指令

-   **`?profile` / `?資料`**: 查詢自己或他人等級、經驗值、金錢等個人資料。
-   **`?links`**: 顯示營隊相關的實用連結。
-   **`?draw` / `?抽籤`**: 每日抽籤，獲得隨機運勢與動漫語錄，並生成運勢圖。
-   **`?schedule` / `?查詢課表`**: 查詢當前或指定時間的營隊課程表。

### 遊戲與經濟系統

-   **經驗值與等級**: 在伺服器中聊天即可獲得經驗值並升級。
-   **`?sign_in` / `?簽到`**: 每日簽到領取金錢，連續簽到天數越多，獎勵越豐厚！
-   **`?slot <amount>` / `?拉霸 <金額>`**: 試試手氣，玩拉霸機贏取（或輸掉）金錢。
-   **定時金錢活動**: 特定時間會出現特殊活動，把握機會賺取額外金錢！

### 彩蛋系統

-   **`?egg` / `?彩蛋`**: 在伺服器中輸入隱藏的關鍵字即可觸發彩蛋。使用此指令可查看已收集的彩蛋。

### AI 智慧功能

-   **AI 聊天**: 在任何頻道 **`@機器人`** 即可與 AI 進行自由對話。
-   **MyGo 專屬頻道**:
    -   在指定頻道輸入關鍵字，機器人會自動搜尋相關的 MyGo!!!!! 角色圖片。
    -   如果找不到對應圖片，AI 會化身為 MyGo 角色，並以該角色的口吻回覆你一句新的台詞。
-   **風格轉換頻道**:
    -   在特定頻道發言，機器人會自動將你的訊息轉換為指定風格，並以該風格的角色發言。
    -   此功能透過 Webhook 運作，會以自訂的名稱與頭像發送訊息，並刪除你的原始訊息。
    -   目前支援風格：
        -   **文言文**: 化身「東漢書院諸葛亮」。
        -   **貓娘**: 化身「你的專屬貓娘」。
        -   **中二**: 化身「漆黑的墮天使」。
        -   **傲嬌**: 化身「傲嬌大小姐」。

### 管理員指令 (僅限工作人員)

-   **`?reload <cog>`**: 重新載入指定的機器人功能模組 (僅限 Bot 擁有者)。
-   **`?reset_flags`**: 重設所有使用者的彩蛋尋獲狀態 (僅限管理員)。

## 安裝與設定

1.  **複製專案庫**:

    ```bash
    git clone https://github.com/your-username/camp-public-bot.git
    cd camp-public-bot
    ```

2.  **安裝依賴套件**:

    ```bash
    pip install -r requirement.txt
    ```

3.  **設定環境變數**:

    -   將 `.env.example` 檔案複製並重新命名為 `.env`。
    -   依照下方的說明填寫 `.env` 檔案中的所有變數。

4.  **啟動機器人**:
    ```bash
    python src/camp_bot.py
    ```

### 如何設定 `.env` 檔案

-   `DISCORD_TOKEN`: 你的 Discord 機器人 Token。前往 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式並取得 Token。
-   `GEMINI_API_KEY`: 你的 Google AI (Gemini) API 金鑰。前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 取得金鑰。

-   **頻道 ID (`*_CHANNEL_ID`)**:

    1.  在 Discord 中，前往「使用者設定」 -> 「進階」，並**開啟「開發者模式」**。
    2.  在任何你想要設定的頻道上按右鍵，選擇「**複製頻道 ID**」。
    3.  將複製的 ID 貼到對應的變數中。

-   **風格轉換 Webhook (`*_WEBHOOK_URL`)**:
    1.  前往你為特定風格（如「文言文」）設定的頻道。
    2.  點擊頻道旁的齒輪圖示，進入「整合」 -> 「Webhook」。
    3.  建立一個新的 Webhook，你可以自訂名稱與頭像（但程式會覆蓋它們）。
    4.  點擊「**複製 Webhook URL**」，並將其貼到 `.env` 中對應的變數（例如 `STYLE_TRANSFER_WENYAN_WEBHOOK_URL`）。
    5.  為所有四種風格重複此步驟。

## 設定檔範例 (`.env.example`)

請參考 `.env.example` 檔案來設定你的環境變數。

```bash
# --- API Keys ---
DISCORD_TOKEN=
GEMINI_API_KEY=

# --- File Paths ---
USER_DATA_FILE=data/user_data.json

# --- Channel IDs ---
# AI-powered channels
MYGO_CHANNEL_ID=
# Style transfer channels
STYLE_TRANSFER_WENYAN_CHANNEL_ID=
STYLE_TRANSFER_CATGIRL_CHANNEL_ID=
STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID=
STYLE_TRANSFER_TSUNDERE_CHANNEL_ID=
# Other feature channels
REWARD_CHANNEL_ID=
EASTER_EGG_CHANNEL_ID=

# --- Style Transfer Webhook URLs ---
STYLE_TRANSFER_WENYAN_WEBHOOK_URL=
STYLE_TRANSFER_CATGIRL_WEBHOOK_URL=
STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL=
STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL=
```

Have fun!
