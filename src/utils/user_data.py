"""
用戶資料管理模組

提供線程安全的用戶資料管理功能，包括：
- 用戶資料的載入、保存和存取
- 新用戶自動初始化
- 向後相容性處理
- 排行榜功能

所有檔案操作都通過 asyncio.Lock 進行同步，確保資料一致性。
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
import discord

from src import config
from src.constants import DEFAULT_LEVEL, DEFAULT_EXP, DEFAULT_MONEY, DEFAULT_USER_FIELDS

UserRecord = Dict[str, Any]
UserIdentifier = Union[int, discord.User, discord.Member]


class UserDataManager:
    """線程安全的用戶資料管理器"""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or config.USER_DATA_FILE
        self._lock = asyncio.Lock()
        self.users: Dict[str, UserRecord] = {}
        self._loaded = False

    async def load_data(self) -> None:
        """從 JSON 檔案載入用戶資料"""
        if self._loaded:
            return

        async with self._lock:
            if self._loaded:  # 雙重檢查
                return

            print("📁 正在載入用戶資料...")
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    all_users = json.load(f)

                # 清理無效資料（非數字 ID）
                valid_users = {k: v for k, v in all_users.items() if k.isdigit()}

                if len(valid_users) != len(all_users):
                    removed_count = len(all_users) - len(valid_users)
                    print(f"🧹 已清理 {removed_count} 筆無效資料")
                    self.users = valid_users
                    await self._save_data()
                else:
                    self.users = all_users

                print(f"✅ 已載入 {len(self.users)} 位用戶的資料")

            except FileNotFoundError:
                print("📁 資料檔案不存在，將建立新檔案")
                self.users = {}
            except json.JSONDecodeError:
                print("⚠️ 資料檔案格式錯誤，使用空資料開始")
                self.users = {}

            self._loaded = True

    async def _save_data(self) -> None:
        """保存資料到檔案（需要已取得鎖）"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"❌ 保存資料失敗：{e}")

    def _create_default_user_data(
        self, user_obj: Optional[discord.User] = None
    ) -> UserRecord:
        """建立新用戶的預設資料"""
        base_data = {
            "name": user_obj.name if user_obj else "Unknown",
            "lv": DEFAULT_LEVEL,
            "exp": DEFAULT_EXP,
            "money": DEFAULT_MONEY,
            "last_sign_in": None,
            "sign_in_streak": 0,
        }

        # 合併預設欄位
        base_data.update(DEFAULT_USER_FIELDS)
        return base_data

    def _ensure_user_data_integrity(
        self, user_data: UserRecord, user_obj: Optional[discord.User] = None
    ) -> bool:
        """確保用戶資料完整性，返回是否有更新"""
        updated = False

        # 更新用戶名稱
        if user_obj and user_data.get("name") != user_obj.name:
            user_data["name"] = user_obj.name
            updated = True

        # 確保必要欄位存在（向後相容）
        for field, default_value in DEFAULT_USER_FIELDS.items():
            if field not in user_data:
                user_data[field] = default_value
                updated = True

        return updated

    async def get_user(
        self, user_identifier: UserIdentifier, user_obj: Optional[discord.User] = None
    ) -> UserRecord:
        """
        獲取用戶資料，自動處理新用戶初始化和資料完整性

        Args:
            user_identifier: 用戶 ID 或 Discord 用戶物件
            user_obj: 可選的 Discord 用戶物件（當第一個參數是 ID 時使用）
        """
        # 解析用戶資訊
        if isinstance(user_identifier, (discord.User, discord.Member)):
            user_obj = user_identifier
            user_id = user_obj.id
        else:
            user_id = user_identifier
            # user_obj 可能從參數傳入或為 None

        user_id_str = str(user_id)

        # 處理新用戶
        if user_id_str not in self.users:
            async with self._lock:
                if user_id_str not in self.users:  # 雙重檢查
                    print(f"👤 新用戶註冊：{user_obj.name if user_obj else user_id}")
                    self.users[user_id_str] = self._create_default_user_data(user_obj)
                    await self._save_data()

        # 確保資料完整性
        user_data = self.users[user_id_str]
        needs_update = self._ensure_user_data_integrity(user_data, user_obj)

        if needs_update:
            await self.update_user_data(user_id, user_data)

        return user_data

    async def update_user_data(self, user_id: int, data: UserRecord) -> None:
        """更新用戶資料並保存"""
        user_id_str = str(user_id)
        async with self._lock:
            self.users[user_id_str] = data
            await self._save_data()

    def get_top_users(
        self, sort_by: str, limit: int = 10
    ) -> List[Tuple[str, UserRecord]]:
        """
        獲取排行榜

        Args:
            sort_by: 排序依據 ('money', 'exp', 'achievements', 'found_flags')
            limit: 返回數量限制
        """

        def get_sort_key(item: Tuple[str, UserRecord]) -> Union[int, float]:
            user_data = item[1]

            if sort_by == "exp":
                # 經驗值排序：主要按等級，次要按經驗值
                return (user_data.get("lv", 1), user_data.get("exp", 0))
            elif sort_by in ["achievements", "found_flags"]:
                # 列表類型按長度排序
                return len(user_data.get(sort_by, []))
            else:
                # 數值類型直接排序
                return user_data.get(sort_by, 0)

        sorted_users = sorted(self.users.items(), key=get_sort_key, reverse=True)
        return sorted_users[:limit]


# 全域用戶資料管理器實例
user_data_manager = UserDataManager()
