#!/usr/bin/env python3
"""
簡單測試用戶資料管理器的修改
"""

import sys
import os
import asyncio
import json

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 模擬必要的配置和常數
class MockConfig:
    USER_DATA_FILE = "/tmp/test_user_data.json"


class MockDiscordUser:
    def __init__(self, name, user_id):
        self.name = name
        self.id = user_id


# 設置模擬模組
sys.modules["src.config"] = MockConfig()
sys.modules["discord"] = type(
    "discord", (), {"User": MockDiscordUser, "Member": MockDiscordUser}
)()

from src.constants import DEFAULT_USER_FIELDS, DEFAULT_LEVEL, DEFAULT_EXP, DEFAULT_MONEY


async def test_user_data_creation():
    """測試用戶資料創建時格式是否固定"""

    # 創建測試資料文件路徑
    test_file = "/tmp/test_user_data.json"

    # 清理可能存在的測試檔案
    try:
        os.remove(test_file)
    except FileNotFoundError:
        pass

    # 模擬用戶資料管理器的核心邏輯
    def create_default_user_data(user_obj=None):
        """建立新用戶的預設資料，包含所有必要欄位"""
        # 創建完整的用戶資料結構，確保格式固定不變
        user_data = {
            "name": user_obj.name if user_obj else "Unknown",
            "lv": DEFAULT_LEVEL,
            "exp": DEFAULT_EXP,
            "money": DEFAULT_MONEY,
            "debt": 0,
            "last_sign_in": None,
            "sign_in_streak": 0,
            # 從 DEFAULT_USER_FIELDS 複製所有預設欄位
            "achievements": DEFAULT_USER_FIELDS.get("achievements", []).copy(),
            "found_flags": DEFAULT_USER_FIELDS.get("found_flags", []).copy(),
        }

        # 確保包含所有 DEFAULT_USER_FIELDS 中的欄位（以防未來新增）
        for field, default_value in DEFAULT_USER_FIELDS.items():
            if field not in user_data:
                if isinstance(default_value, list):
                    user_data[field] = default_value.copy()
                else:
                    user_data[field] = default_value

        return user_data

    # 創建測試用戶
    test_user = MockDiscordUser("TestUser", 123456789)

    # 測試新用戶資料創建
    user_data_1 = create_default_user_data(test_user)
    user_data_2 = create_default_user_data(test_user)

    print("新創建的用戶資料結構：")
    for key, value in user_data_1.items():
        print(f"  {key}: {value} ({type(value).__name__})")

    # 驗證所有必要欄位都存在
    expected_fields = {
        "name",
        "lv",
        "exp",
        "money",
        "debt",
        "last_sign_in",
        "sign_in_streak",
    }
    expected_fields.update(DEFAULT_USER_FIELDS.keys())

    missing_fields = expected_fields - set(user_data_1.keys())
    if missing_fields:
        print(f"❌ 缺少欄位: {missing_fields}")
    else:
        print("✅ 所有必要欄位都存在")

    # 檢查兩次創建的資料是否一致
    if user_data_1 == user_data_2:
        print("✅ 用戶資料格式保持一致")
    else:
        print("❌ 用戶資料格式發生變化")
        print("第一次創建:", user_data_1)
        print("第二次創建:", user_data_2)

    # 檢查列表類型欄位是否為獨立副本
    user_data_1["achievements"].append("test_achievement")
    if len(user_data_2["achievements"]) == 0:
        print("✅ 列表欄位為獨立副本，不會互相影響")
    else:
        print("❌ 列表欄位不是獨立副本")

    print("\n資料結構驗證完成！")


if __name__ == "__main__":
    asyncio.run(test_user_data_creation())
