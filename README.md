# 🤖 NTNU CSIE Camp 2025 Discord Bot

> 師大資工營 2025 官方 Discord 機器人  
> 提供豐富的互動功能，讓營隊體驗更加有趣！

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 功能特色

### 🎯 核心功能

-   **📊 用戶系統**: 等級、經驗值、金錢管理
-   **🎰 遊戲娛樂**: 簽到、拉霸、抽籤等互動遊戲
-   **🏆 成就系統**: 多種成就等待解鎖，獲得豐厚獎勵
-   **🥚 彩蛋收集**: 隱藏關鍵字觸發，收集專屬彩蛋

### 🤖 AI 智能功能

-   **💬 智能對話**: `@機器人` 開啟 AI 聊天模式
-   **🎭 風格轉換**: 多種角色風格自動轉換
    -   📜 文言文（東漢書院諸葛亮）
    -   🐱 貓娘風格（你的專屬貓娘）
    -   🌟 中二風格（漆黑的墮天使）
    -   💕 傲嬌風格（傲嬌大小姐）
    -   🎸 角色扮演（豐川祥子）
-   **🎵 MyGo 專屬**: 角色圖片搜尋與台詞生成

## 🚀 快速開始

### 環境需求

-   Python 3.8+
-   Discord Bot Token
-   Google Gemini API Key

### 安裝步驟

1. **克隆專案**

    ```bash
    git clone https://github.com/your-username/camp-public-bot.git
    cd camp-public-bot
    ```

2. **安裝依賴**

    ```bash
    pip install -r requirement.txt
    ```

3. **環境配置**

    ```bash
    cp .env.example .env
    # 編輯 .env 檔案，填入必要的 API Keys 和頻道 ID
    ```

4. **啟動機器人**
    ```bash
    python -m src.camp_bot
    ```

## ⚙️ 環境變數配置

### 必要設定

```env
# API Keys
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key

# 檔案路徑
USER_DATA_FILE=data/user_data.json
```

### 頻道配置

```env
# 功能頻道 ID
MYGO_CHANNEL_ID=your_mygo_channel_id
REWARD_CHANNEL_ID=your_reward_channel_id
EASTER_EGG_CHANNEL_ID=your_easter_egg_channel_id
SCOREBOARD_CHANNEL_ID=your_scoreboard_channel_id

# 風格轉換頻道 ID
STYLE_TRANSFER_WENYAN_CHANNEL_ID=your_wenyan_channel_id
STYLE_TRANSFER_CATGIRL_CHANNEL_ID=your_catgirl_channel_id
STYLE_TRANSFER_CHUUNIBYOU_CHANNEL_ID=your_chuunibyou_channel_id
STYLE_TRANSFER_TSUNDERE_CHANNEL_ID=your_tsundere_channel_id
STYLE_TRANSFER_SAKIKO_CHANNEL_ID=your_sakiko_channel_id
```

### Webhook 設定

```env
# 風格轉換 Webhook URLs
STYLE_TRANSFER_WENYAN_WEBHOOK_URL=your_wenyan_webhook_url
STYLE_TRANSFER_CATGIRL_WEBHOOK_URL=your_catgirl_webhook_url
STYLE_TRANSFER_CHUUNIBYOU_WEBHOOK_URL=your_chuunibyou_webhook_url
STYLE_TRANSFER_TSUNDERE_WEBHOOK_URL=your_tsundere_webhook_url
STYLE_TRANSFER_SAKIKO_WEBHOOK_URL=your_sakiko_webhook_url
```

## 📝 指令列表

### 🎯 一般功能

| 指令              | 別名        | 描述         |
| ----------------- | ----------- | ------------ |
| `?profile [用戶]` | `?資料`     | 查詢個人資料 |
| `?links`          |             | 顯示營隊連結 |
| `?draw`           | `?抽籤`     | 每日運勢抽籤 |
| `?schedule`       | `?查詢課表` | 查詢課程表   |
| `?help`           | `?幫助`     | 顯示幫助資訊 |

### 💰 遊戲經濟

| 指令           | 別名    | 描述           |
| -------------- | ------- | -------------- |
| `?sign_in`     | `?簽到` | 每日簽到領金錢 |
| `?slot <金額>` | `?拉霸` | 拉霸遊戲       |
| 聊天           |         | 獲得經驗值升級 |

### 🏆 成就彩蛋

| 指令                   | 別名        | 描述           |
| ---------------------- | ----------- | -------------- |
| `?achievements [用戶]` | `?成就`     | 查看成就狀態   |
| `?all_achievements`    | `?成就列表` | 查看所有成就   |
| `?egg`                 | `?彩蛋`     | 查看收集的彩蛋 |

### 🛠️ 管理功能

| 指令             | 權限   | 描述           |
| ---------------- | ------ | -------------- |
| `?reload <模組>` | 擁有者 | 重載功能模組   |
| `?status`        | 擁有者 | 機器人狀態     |
| `?reset_flags`   | 管理員 | 重置彩蛋狀態   |
| `?scoreboard`    | 管理員 | 手動更新排行榜 |
| `?cogs`          | 擁有者 | 模組列表       |

## 🏗️ 專案結構

```
camp-public-bot/
├── src/                    # 主要程式碼
│   ├── cogs/              # 功能模組
│   │   ├── general.py     # 一般功能
│   │   ├── admin.py       # 管理功能
│   │   ├── style_transfer.py  # 風格轉換
│   │   ├── achievements.py    # 成就系統
│   │   └── ...
│   ├── utils/             # 工具模組
│   │   ├── user_data.py   # 用戶資料管理
│   │   ├── llm.py         # AI 模型整合
│   │   └── ...
│   ├── camp_bot.py        # 機器人主程式
│   ├── config.py          # 配置管理
│   └── constants.py       # 常數定義
├── data/                  # 資料檔案
├── .env.example          # 環境變數範例
├── requirement.txt       # 依賴套件
└── README.md            # 專案說明
```

## 🔧 開發指南

### 新增功能模組

1. 在 `src/cogs/` 建立新的 `.py` 檔案
2. 繼承 `commands.Cog` 類別
3. 實作 `setup()` 函數
4. 機器人會自動載入新模組

### 新增成就

在 `src/utils/achievements.py` 的 `ACHIEVEMENTS` 字典中添加：

```python
"achievement_id": Achievement(
    id="achievement_id",
    name="成就名稱",
    description="成就描述",
    icon="🏆",
    reward_money=100
)
```

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📞 支援與聯絡

-   🐛 [回報問題](https://github.com/your-username/camp-public-bot/issues)
-   💡 [功能建議](https://github.com/your-username/camp-public-bot/discussions)
-   🌐 [營隊官網](https://camp.ntnucsie.info/)

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

---

<div align="center">
  <p><strong>NTNU CSIE Camp 2025</strong></p>
</div>
