"""
使用者資料管理模組。

此模組提供 UserData 類別，用於處理使用者資料的載入、儲存和存取。
為了防止在異步環境中同時讀寫檔案導致資料損毀，
所有檔案操作都透過一個 asyncio.Lock 來進行同步。

它會在啟動時將資料載入記憶體，所有操作都針對記憶體中的資料進行，
並在每次修改後將資料寫回檔案，確保資料的一致性。
"""

import json
import asyncio
from typing import Dict, Any, Optional

from src import config

UserRecord = Dict[str, Any]


class UserData:
    """
    一個線程安全的類別，用於管理使用者資料的 JSON 檔案。
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or config.USER_DATA_FILE
        self._lock = asyncio.Lock()
        self.users: Dict[str, UserRecord] = {}
        self._loaded = False

    async def load_data(self):
        """
        從 JSON 檔案載入使用者資料到記憶體中。
        此方法應在機器人啟動時被呼叫一次。
        """
        if self._loaded:
            return

        async with self._lock:
            if self._loaded:
                return

            print("正在初始化使用者資料...")
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
                print(
                    f"已成功從 '{self.file_path}' 載入 {len(self.users)} 位使用者的資料。"
                )
            except FileNotFoundError:
                print(f"資料檔案 '{self.file_path}' 不存在，將以空資料開始。")
                self.users = {}
            except json.JSONDecodeError:
                print(f"警告：無法解析資料檔案 '{self.file_path}'。將使用空資料。")
                self.users = {}
            self._loaded = True

    async def _save_data(self):
        """
        將目前記憶體中的使用者資料非同步寫入 JSON 檔案。
        此方法假設呼叫者已經取得了 lock。
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"儲存資料到 '{self.file_path}' 時發生錯誤: {e}")

    async def get_user(self, user_id: int) -> UserRecord:
        """
        從記憶體中獲取使用者資料。
        如果使用者是第一次出現，會為其建立一個預設的資料結構並儲存。
        """
        user_id_str = str(user_id)

        if user_id_str in self.users:
            user_data = self.users[user_id_str]
            # 確保舊用戶也有成就欄位（向後相容性）
            if "achievements" not in user_data:
                user_data["achievements"] = []
                await self.update_user_data(user_id, user_data)
            return user_data

        async with self._lock:
            if user_id_str in self.users:
                user_data = self.users[user_id_str]
                if "achievements" not in user_data:
                    user_data["achievements"] = []
                    await self._save_data()
                return user_data

            print(f"新使用者: {user_id_str}，正在建立預設資料...")
            default_data = {
                "lv": 1,
                "exp": 0,
                "money": 100,
                "last_sign_in": None,
                "sign_in_streak": 0,
                "achievements": []
            }
            self.users[user_id_str] = default_data
            await self._save_data()
            return default_data

    async def update_user_data(self, user_id: int, data: UserRecord):
        """
        以原子操作更新指定使用者的資料，並將其儲存回檔案。
        """
        user_id_str = str(user_id)
        async with self._lock:
            self.users[user_id_str] = data
            await self._save_data()


# 建立一個全域唯一的 UserData 實例
user_data_manager = UserData()
