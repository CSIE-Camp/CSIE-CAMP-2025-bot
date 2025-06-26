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
import discord

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
                    all_users = json.load(f)

                # 清理無效的鍵（非數字 ID）
                cleaned_users = {k: v for k, v in all_users.items() if k.isdigit()}

                if len(cleaned_users) < len(all_users):
                    print(
                        f"已清理無效的使用者資料。從 {len(all_users)} 筆資料中保留了 {len(cleaned_users)} 筆。"
                    )
                    self.users = cleaned_users
                    await self._save_data()  # 儲存清理後的版本
                else:
                    self.users = all_users

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

    async def get_user(
        self,
        user_id_or_obj: int | discord.User | discord.Member,
        user_obj_optional: Optional[discord.User | discord.Member] = None,
    ) -> UserRecord:
        """
        從記憶體中獲取使用者資料。
        可以傳入使用者 ID (int) 或 discord.User/discord.Member 物件。
        如果使用者是第一次出現，會為其建立一個預設的資料結構並儲存。
        同時會檢查並更新使用者名稱。
        """
        user_obj: Optional[discord.User | discord.Member] = None
        user_id: int

        if isinstance(user_id_or_obj, (discord.User, discord.Member)):
            user_obj = user_id_or_obj
            user_id = user_obj.id
        else:
            user_id = user_id_or_obj
            user_obj = user_obj_optional

        user_id_str = str(user_id)

        # 如果是新使用者，先建立基本資料
        if user_id_str not in self.users:
            async with self._lock:
                # 再次檢查，防止競爭條件
                if user_id_str not in self.users:
                    print(f"新使用者: {user_id_str}，正在建立預設資料...")
                    user_name = user_obj.name if user_obj else "Unknown"
                    default_data = {
                        "name": user_name,
                        "lv": 1,
                        "exp": 0,
                        "money": 100,
                        "last_sign_in": None,
                        "sign_in_streak": 0,
                        "achievements": [],
                        "found_flags": [],
                    }
                    self.users[user_id_str] = default_data
                    await self._save_data()

        # 現在，使用者資料必定存在
        user_data = self.users[user_id_str]

        # --- 向後相容性與名稱更新檢查 ---
        needs_update = False

        # 如果提供了使用者物件，就檢查並更新名稱
        # 這也會處理使用者改名，或補上舊資料中缺少的名字
        if user_obj and user_data.get("name") != user_obj.name:
            user_data["name"] = user_obj.name
            needs_update = True

        # 確保舊用戶也有成就和旗標欄位
        if "achievements" not in user_data:
            user_data["achievements"] = []
            needs_update = True

        if "found_flags" not in user_data:
            user_data["found_flags"] = []
            needs_update = True

        # 如果有任何更新，則儲存回檔案
        if needs_update:
            await self.update_user_data(user_id, user_data)

        return user_data

    async def update_user_data(self, user_id: int, data: UserRecord):
        """
        更新指定使用者 ID 的資料，並將變更儲存到檔案中。
        """
        user_id_str = str(user_id)
        async with self._lock:
            self.users[user_id_str] = data
            await self._save_data()

    def get_top_users(self, sort_by: str, limit: int = 10):
        """
        獲取排序後的使用者列表。

        Args:
            sort_by (str): 用於排序的鍵（例如 "money", "exp", "achievements", "found_flags"）。
            limit (int): 要返回的使用者數量。

        Returns:
            list: 排序後的使用者元組列表 (user_id, data)。
        """
        if sort_by == "exp":
            # 對於經驗值，主要按等級排序，次要按經驗值排序
            key_func = lambda item: (item[1].get("lv", 1), item[1].get("exp", 0))
        elif sort_by in ["achievements", "found_flags"]:
            # 對於列表類型，我們按其長度排序
            key_func = lambda item: len(item[1].get(sort_by, []))
        else:
            # 對於數值類型，直接按其值排序
            key_func = lambda item: item[1].get(sort_by, 0)

        sorted_users = sorted(self.users.items(), key=key_func, reverse=True)
        return sorted_users[:limit]


# 建立一個全域唯一的 UserData 實例
user_data_manager = UserData()
