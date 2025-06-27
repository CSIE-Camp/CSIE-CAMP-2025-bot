# 🤖 NTNU CSIE Camp 2025 Discord Bot

> 師大資工營 2025 官方 Discord 機器人  
> 專為資工營打造，提供豐富的互動功能，讓你的營隊生活更加精彩！

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 主要功能

-   **📊 個人檔案**: 追蹤你的等級、經驗值和金錢。
-   **🏆 成就系統**: 解鎖特殊成就，獲得獨家獎勵。
-   **🎰 趣味遊戲**: 每日簽到、拉霸、抽籤，還有更多驚喜！
-   **🥚 彩蛋收集**: 在營隊中尋找隱藏的彩蛋，成為彩蛋大師！
-   **🤖 AI 智慧互動**:
    -   與機器人自由聊天。
    -   體驗多種角色風格的訊息轉換。
    -   MyGo 專屬圖文生成。
-   **📅 營隊資訊**: 快速查詢課表與重要連結。

## 🚀 如何使用

大部分指令都支援**斜線指令 (`/`)** 和**傳統前綴 (`?`)** 兩種方式。

-   **查看所有指令**: 輸入 `/help` 或 `?help`
-   **查看特定指令說明**: 輸入 `/help <指令名稱>`

### 指令列表

#### 🎯 一般功能

-   `/profile`: 查詢你或指定用戶的個人資料 (等級、金錢、經驗值)。
-   `/links`: 顯示營隊的相關重要連結 (GitHub, Instagram)。
-   `/schedule`: 查詢當日的營隊課表。
-   `/help`: 顯示這個幫助訊息。

#### 💰 遊戲與經濟

-   `/checkin`: 🌟 **每日簽到抽籤**！簽到後自動抽取今日運勢，依運勢獲得金錢獎勵，並有隨機引言和圖片生成。
-   `/scoreboard`: 查看營隊成員的經驗值排行榜。
-   `/game slot <金額>`: 玩一把刺激的拉霸遊戲。
-   `/game dice <金額>`: 與機器人比骰子大小。
-   `/game rps <金額> <選項>`: 玩一場剪刀石頭布。
-   `/game guess <金額> <數字>`: 猜一個 1 到 100 的數字。

#### 🏆 成就與彩蛋

-   `/achievements`: 顯示你或指定用戶已解鎖的成就。
-   `/all_achievements`: 查看所有可以解鎖的成就列表。
-   `/egg`: 查詢你已經發現了哪些彩蛋。

#### 🎵 MyGo 專屬

-   `/mygo <關鍵字>`: 從 MyGO!!!!! 圖庫中搜尋一張符合關鍵字的圖片。
-   `/mygo_quote`: 隨機取得一句 MyGO!!!!! 的經典名言。

#### 🛠️ 管理功能 (限管理員)

-   `/reload <模組>`: 重載指定的機器人功能模組。
-   `/status`: 顯示機器人的運行狀態。
-   `/cogs`: 列出所有已載入的功能模組。
-   `/reset_flags`: 重置所有用戶的彩蛋觸發狀態。
-   `/set_schedule`: 上傳並設定新的課表。

### ✨ 自動功能 (無須指令)

這些是本機器人的核心特色，它們會在背景自動運作，無須輸入任何指令！

-   **💬 經驗與金錢系統**:

    -   在任何頻道發言（指令除外），都會自動獲得經驗值和金錢。
    -   經驗值累積到一定程度後會自動升級，並在當前頻道發送升級通知。
    -   發言時有 5% 的機率觸發隨機事件，可能會撿到錢或掉錢！

-   **🤖 AI 智慧聊天**:

    -   在任何頻道中**提及 (mention)** 機器人 (`@NTNU CSIE Camp Bot`)，就可以和它自由聊天。

-   **🎭 角色風格轉換**:

    -   在特定的「風格轉換頻道」中發言，你的訊息會被自動轉換成該頻道的角色風格，並由該角色（Webhook）發送出來。

-   **🥚 彩蛋系統**:
    -   在任何地方輸入隱藏的「彩蛋關鍵字」，如果你是前三位發現者，就會在彩蛋頻道廣播你的成就！如果已經被找完了，機器人也會提示你。

## ⚙️ 快速開始 (開發者)

### 環境需求

-   Python 3.8+
-   Discord Bot Token
-   Google Gemini API Key

### 安裝與啟動

1.  **克隆專案**

    ```bash
    git clone https://github.com/your-username/camp-public-bot.git
    cd camp-public-bot
    ```

2.  **安裝依賴**

    ```bash
    pip install -r requirements.txt
    ```

3.  **環境配置**

    -   複製 `.env.example` 為 `.env`
    -   填寫必要的 API Keys 和頻道 ID。

4.  **啟動機器人**
    ```bash
    python start.py
    ```
    > 腳本會自動進行健康檢查，確保設定無誤。

## 🏗️ 專案結構

```
camp-public-bot/
├── src/                    # 主要程式碼
│   ├── cogs/               # 功能模組 (e.g., general, games)
│   ├── utils/              # 共用工具 (e.g., user_data, llm)
│   ├── camp_bot.py         # 機器人主程式
│   ├── config.py           # 設定檔管理
│   └── constants.py        # 常數定義
├── data/                   # 資料檔案 (e.g., quotes, achievements)
├── .env.example            # 環境變數範例
├── requirement.txt         # Python 依賴
├── start.py                # 啟動腳本
└── README.md               # 就是這個檔案
```

## 🤝 貢獻

歡迎各種形式的貢獻！無論是回報問題、建議新功能，或是直接提交 Pull Request。

1.  Fork 本專案
2.  建立你的功能分支 (`git checkout -b feature/AmazingFeature`)
3.  提交你的變更 (`git commit -m 'Add some AmazingFeature'`)
4.  將分支推送到遠端 (`git push origin feature/AmazingFeature`)
5.  開啟一個 Pull Request

## 📞 聯絡我們

若有任何問題，歡迎透過 [GitHub Issues](https://github.com/your-username/camp-public-bot/issues) 與我們聯繫。
