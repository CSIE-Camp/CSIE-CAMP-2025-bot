# 🤖 NTNU CSIE Camp 2025 Discord Bot

> 師大資工營 2025 官方 Discord 機器人  
> 專為資工營打造，提供豐富的互動功能，讓你的營隊生活更加精彩！

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🆘 幫助說明（Help）

### 指令與功能總覽

#### 🎯 一般功能

-   `/profile`：查詢你或指定用戶的等級、經驗值、金錢。
-   `/links`：顯示營隊重要連結（GitHub、Instagram）。
-   `/schedule`：查詢今日營隊課表。
-   `/help`：顯示本說明。

#### 💰 遊戲與經濟

-   `/checkin`：每日簽到抽運勢，獲得金錢、隨機引言與圖片。
-   `/scoreboard`：查看經驗值排行榜。
-   `/game slot <金額>`：拉霸遊戲，下注金額有機會翻倍。
-   `/game dice <金額>`：與機器人比骰子大小，贏家獲得全部金額。
-   `/game rps <金額> <選項>`：剪刀石頭布，贏家獲得全部金額。
-   `/game guess <金額>`：猜數字遊戲，使用互動按鈕進行，猜中可獲得獎勵。

> **遊戲頻道限制**：請在指定的「[遊戲頻道](https://discord.com/channels/YOUR_GUILD_ID/1388171224361734205)」進行遊戲指令，否則無法使用。

#### 🏆 成就與彩蛋

-   `/achievements`：查看你或指定用戶已解鎖的成就。
-   `/egg`：查詢你發現的彩蛋。

> **彩蛋提示**：
> 找到彩蛋後，直接在任何群組頻道輸入彩蛋內容即可觸發。
> 彩蛋格式為 `flag{||XXXX||}`，請將 `XXXX` 替換為你發現的彩蛋內容。

#### 🎵 MyGo 專屬

-   `/mygo <關鍵字>`：搜尋 MyGO!!!!! 圖片。
-   `/mygo_quote`：隨機取得一句 MyGO!!!!! 名言。

#### 🤖 AI 互動

-   `@機器人`：在任何頻道提及機器人即可與 AI (Gemini) 聊天。
-   `/image <提示詞>`：生成 AI 圖片（如有開啟）。
-   在特定「風格轉換頻道」發言，訊息會自動轉換成指定角色風格（如文言文、貓娘、中二、傲嬌、祥子等）。

#### 🐾 虛擬寵物養成系統

> **🌟 特色功能**：
> - **🎨 AI 頭像生成**: 每隻寵物都有 AI 生成的專屬真實頭像！
> - **🤖 智能對話**: 所有寵物回應都由 AI 實時生成，符合個性！
> - **📱 Webhook 互動**: 寵物以自己的名稱和頭像發送訊息，彷彿真實存在！

-   `/adopt <寵物名字>`：認養一隻專屬的虛擬寵物，AI 生成個性和頭像，**自動創建專屬討論串**。
-   `/pet_status`：查看你的寵物狀態、好感度和相處天數。
-   `/play_ball`：與寵物玩球互動遊戲，增加好感度。
-   `/feed_pet`：餵食寵物（每小時限一次），大幅增加好感度。
-   `/pet_ranking`：查看好感度排行榜，看誰最疼愛寵物！
-   `/show_off_pet`：在公共頻道炫耀你的寵物，展示感情深度和 AI 頭像。
-   `/pet_thread`：快速前往你的寵物專屬討論串。

> **🏠 專屬小窩**：每隻寵物都有自己的討論串，所有 AI 生成的自主行為都在裡面進行：
> - 🎁 帶禮物回家 (3-8分鐘) - AI 生成獨特探險故事
> - 😔 心情不好時找安慰 (5-12分鐘) - AI 生成個性化委屈表達
> - 💎 出去尋找寶物 (4-10分鐘) - AI 生成刺激尋寶過程
> - 😴 午睡並分享夢境 (6-15分鐘) - AI 生成有趣夢境內容
> - 💃 開心時跳舞表演 (8-18分鐘) - AI 生成活潑舞蹈描述

> **🏆 成就系統**: 解鎖寵物相關成就 - 寵物愛好者 🐾、AI 寵物大師 🎨、寵物語者 💕、資深飼主 🏆

> **⚠️ 重要**：機器人需要以下權限：
> - 「管理 Webhook」- 讓寵物以自己的身份說話
> - 「管理討論串」- 創建專屬小窩
> - 有效的 Hugging Face Token - 生成 AI 頭像
> 請參考 [權限設置指南](WEBHOOK_PERMISSIONS_GUIDE.md)。

#### 🛠️ 管理功能（限管理員）

-   `/reload <模組>`：重載指定功能模組。
-   `/status`：顯示機器人運行狀態。
-   `/cogs`：列出所有已載入功能模組。
-   `/reset_flags`：重置所有用戶彩蛋觸發狀態。
-   `/set_schedule`：上傳並設定新課表。
-   `/redpacket <人數>`：手動觸發紅包雨活動（限管理員）。

---

### ✨ 自動功能（無須指令）

-   **經驗與金錢系統**：在任何頻道發言（指令除外）自動獲得經驗值和金錢，經驗值滿自動升級，頻道會通知。
-   **隨機紅包雨**：每小時有機率自動在公告頻道發起紅包雨活動，限額搶獎金。
-   **AI 智慧聊天**：提及機器人即可自由聊天。
-   **角色風格轉換**：在指定頻道自動轉換訊息風格。
-   **彩蛋系統**：輸入隱藏關鍵字可觸發彩蛋。
-   **🐾 寵物自主行為**：已認養的寵物會定時主動與主人互動，使用 Webhook 以自己的身份說話！

---

### 📢 頻道與遊戲規則

-   **遊戲指令**：請在指定「[遊戲頻道](https://discord.com/channels/YOUR_GUILD_ID/1388171224361734205)」使用，否則無法參與。
-   **紅包雨活動**：會在公告頻道自動或由管理員手動發起，點擊按鈕搶獎金，每人限搶一次，名額有限。
-   **AI 互動**：全頻道皆可提及機器人聊天，風格轉換僅限指定頻道。
-   **經驗/金錢/成就**：發言、遊戲、簽到、搶紅包等皆可獲得經驗與金錢，達成條件自動解鎖成就。

---

## ⚙️ 快速開始（開發者）

### 環境需求

-   Python 3.8+
-   Discord Bot Token
-   Google Gemini API Key

### 安裝與啟動

1.  **複製專案**

    ```bash
    git clone https://github.com/your-username/camp-public-bot.git
    cd camp-public-bot
    ```

2.  **安裝依賴**

    ```bash
    pip install -r requirement.txt
    ```

3.  **環境配置**

    -   複製 `.env.example` 為 `.env`
    -   填寫必要的 API Keys 和頻道 ID。

4.  **健康檢查與啟動**

    ```bash
    python start.py
    ```

    > 啟動腳本會自動進行健康檢查，確保設定無誤。

## 🏗️ 專案結構

```
camp-public-bot/
├── src/                    # 主要程式碼
│   ├── cogs/               # 功能模組 (e.g., general, games, ...)
│   ├── utils/              # 共用工具 (e.g., user_data, llm)
│   ├── camp_bot.py         # 機器人主程式
│   ├── config.py           # 設定檔管理
│   └── constants.py        # 常數定義
├── data/                   # 資料檔案 (e.g., quotes, achievements)
├── .env.example            # 環境變數範例
├── requirement.txt         # Python 依賴
├── start.py                # 啟動腳本
├── health_check.py         # 健康檢查腳本
└── README.md               # 就是這個檔案
```

## 🗝️ .env 主要設定說明

-   `DISCORD_TOKEN`：Discord Bot Token（必要）
-   `GEMINI_API_KEY`：Google Gemini API Key（必要）
-   其他如 Hugging Face Token、頻道 ID、Webhook URL 請參考 `.env.example`

## 🤝 貢獻

歡迎各種形式的貢獻！無論是回報問題、建議新功能，或是直接提交 Pull Request。

1.  Fork 本專案
2.  建立你的功能分支 (`git checkout -b feature/AmazingFeature`)
3.  提交你的變更 (`git commit -m 'Add some AmazingFeature'`)
4.  將分支推送到遠端 (`git push origin feature/AmazingFeature`)
5.  開啟一個 Pull Request

## 📞 聯絡我們

若有任何問題，歡迎透過 [GitHub Issues](https://github.com/your-username/camp-public-bot/issues) 與我們聯繫。
