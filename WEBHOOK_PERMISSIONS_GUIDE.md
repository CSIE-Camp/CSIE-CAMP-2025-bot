# 🤖 寵物系統 Discord 機器人權限設置指南

## 🔑 必要權限

為了讓寵物系統的 Webhook 功能正常運作，您的 Discord 機器人需要以下權限：

### 基礎權限
- ✅ **Send Messages** (發送訊息)
- ✅ **Use Slash Commands** (使用斜線指令)
- ✅ **Embed Links** (嵌入連結)
- ✅ **Add Reactions** (添加反應)

### 🌟 Webhook 相關權限 (重要！)
- ✅ **Manage Webhooks** (管理 Webhook) - **這是關鍵權限！**
- ✅ **Manage Threads** (管理討論串) - **用於創建寵物專屬小窩！**
- ✅ **Create Public Threads** (創建公開討論串) - **用於寵物專屬討論串！**

## 🛠️ 權限設置步驟

### 方法 1: Discord 開發者面板設置

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇您的機器人應用程式
3. 進入「OAuth2」→「URL Generator」
4. 勾選以下 Scopes:
   - `bot`
   - `applications.commands`
5. 勾選以下 Bot Permissions:
   ```
   General Permissions:
   ☑️ Manage Webhooks
   ☑️ Manage Threads
   ☑️ Create Public Threads
   
   Text Permissions:
   ☑️ Send Messages
   ☑️ Use Slash Commands
   ☑️ Embed Links
   ☑️ Add Reactions
   ☑️ Read Message History
   ```
6. 複製生成的邀請連結重新邀請機器人

### 方法 2: 伺服器內設置

1. 右鍵點擊機器人 → 「角色」
2. 確保機器人的角色具有以下權限：
   - ✅ 管理 Webhook (Manage Webhooks)
   - ✅ 發送訊息 (Send Messages)
   - ✅ 使用斜線指令 (Use Slash Commands)

## ⚠️ 權限不足時的表現

如果機器人缺少 `Manage Webhooks` 權限，會出現以下情況：

### 寵物認養 (`/adopt`)
```
❌ 機器人在頻道 #general 缺少 Manage Webhooks 權限
🐾 小貓貓: 主人你好！我是你的新寵物！  # 回退為普通訊息
```

### 寵物餵食 (`/feed_pet`)
```
❌ 創建 Webhook 被拒絕：機器人可能缺少權限
🐾 小貓貓: 好香的味道！謝謝主人~  # 回退為普通訊息
```

### 寵物自主行為
```
❌ Webhook 發送失敗: 403 Forbidden
🐾 小貓貓: 我找到了一個漂亮的小石頭給主人！  # 回退為普通訊息
```

## ✅ 權限檢查方法

### 管理員檢查
在您的 Discord 伺服器中執行以下步驟：
1. 前往「伺服器設置」→「角色」
2. 找到機器人的角色
3. 確認「管理 Webhook」權限已開啟

### 頻道層級權限
如果特定頻道無法使用 Webhook：
1. 右鍵點擊頻道 → 「編輯頻道」
2. 進入「權限」頁籤
3. 找到機器人角色，確保「管理 Webhook」未被拒絕

## 🎯 最佳實踐

### 建議的機器人角色設置
建議為機器人創建專屬角色並賦予以下權限：
```
角色名稱: 營隊機器人
顏色: 任意（建議鮮明顏色便於識別）

權限設置:
✅ 管理 Webhook
✅ 管理討論串
✅ 創建公開討論串
✅ 發送訊息
✅ 嵌入連結
✅ 添加反應
✅ 使用斜線指令
✅ 讀取訊息紀錄
```

### 安全考量
- Webhook 權限僅用於寵物系統功能
- 每次使用後會自動清理 Webhook，不會留下垃圾
- 不會影響其他機器人或使用者的 Webhook

## 🔧 故障排除

### 問題：寵物不使用 Webhook 說話
**解決方案：**
1. 檢查機器人是否有「管理 Webhook」權限
2. 確認頻道沒有限制機器人權限
3. 查看控制台是否有權限錯誤訊息

### 問題：部分頻道 Webhook 無效
**解決方案：**
1. 檢查該頻道的專屬權限設置
2. 確保機器人角色在該頻道有「管理 Webhook」權限

### 問題：機器人完全無法使用斜線指令
**解決方案：**
1. 重新邀請機器人並確保包含正確權限
2. 執行 `?sync` 指令同步斜線指令（需要擁有者權限）

## 📞 聯絡支援

如果仍有權限相關問題，請聯絡技術支援並提供：
- 錯誤訊息截圖
- 機器人角色權限截圖
- 受影響的頻道名稱

正確設置權限後，您的寵物就能以自己的身份愉快地與主人聊天了！🐾💕
