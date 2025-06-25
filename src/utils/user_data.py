# -*- coding: utf-8 -*-
"""
使用者資料管理模組。

此模組提供 UserData 類別，用於處理使用者資料的載入、儲存和存取。
為了防止在異步環境中同時讀寫檔案導致資料損毀，
所有檔案操作都透過一個 asyncio.Lock 來進行同步。
"""
import json
import asyncio
from typing import Dict, Any, Optional

from src import config

# --- 資料模型 ---
# 使用 TypedDict 或 Pydantic 可以讓資料結構更清晰，但為保持簡單，這裡先用 Dict
UserRecord = Dict[str, Any]


class UserData:
    """
    一個線程安全的類別，用於管理使用者資料的 JSON 檔案。
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        初始化 UserData。

        Args:
            file_path: JSON 檔案的路徑。如果為 None，則從 config.py 讀取預設路徑。
        """
        self.file_path = file_path or config.USER_DATA_FILE
        self._lock = asyncio.Lock()
        # 資料不再於初始化時載入，避免阻塞。會在首次存取時異步載入。
        self.users: Dict[str, UserRecord] = {}

    async def _load_data(self) -> Dict[str, UserRecord]:
        """
        從 JSON 檔案非同步載入使用者資料。
        處理檔案不存在或內容損毀的情況。
        """
        async with self._lock:
            try:
                # 使用 aiofiles 可以在未來進一步優化為完全非阻塞的 IO
                # 但為了減少依賴，暫時使用標準 open
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                print(f"資料檔案 '{self.file_path}' 不存在，將建立一個新的。")
                return {}
            except json.JSONDecodeError:
                print(
                    f"警告：無法解析資料檔案 '{self.file_path}'。可能檔案已損毀。將使用空資料。"
                )
                return {}

    async def _save_data(self):
        """
        將目前的使用者資料非同步寫入 JSON 檔案。
        """
        async with self._lock:
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(self.users, f, indent=4, ensure_ascii=False)
            except IOError as e:
                print(f"儲存資料到 '{self.file_path}' 時發生錯誤: {e}")

    async def get_user(self, user_id: int) -> UserRecord:
        """
        根據 user_id 獲取使用者資料。

        如果使用者是第一次出現，會為其建立一個預設的資料結構。
        為了確保資料是最新的，此方法會從檔案重新載入資料。

        Args:
            user_id: 使用者的 Discord ID。

        Returns:
            一個包含使用者資料的字典。
        """
        user_id_str = str(user_id)
        self.users = await self._load_data()

        if user_id_str not in self.users:
            print(f"新使用者: {user_id_str}，正在建立預設資料...")
            self.users[user_id_str] = {
                "lv": 1,
                "exp": 0,
                "money": 100,  # 新使用者初始資金
                "last_sign_in": None,
                "sign_in_streak": 0,
            }
            await self._save_data()
        return self.users[user_id_str]

    async def update_user_data(self, user_id: int, data: UserRecord):
        """
        更新指定使用者的資料，並將其儲存回檔案。

        Args:
            user_id: 使用者的 Discord ID。
            data: 要更新的資料字典。
        """
        user_id_str = str(user_id)
        # 為了安全起見，再次載入資料以獲取最新版本
        self.users = await self._load_data()

        # 使用 .get 避免 KeyError，並用 data 更新
        user_record = self.users.get(user_id_str, {})
        user_record.update(data)
        self.users[user_id_str] = user_record

        await self._save_data()


# 建立一個全域唯一的 UserData 實例，讓所有 cogs 共享。
# 這樣可以確保所有操作都使用同一個 lock。
user_data_manager = UserData()
