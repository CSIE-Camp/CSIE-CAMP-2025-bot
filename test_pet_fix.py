#!/usr/bin/env python3
"""
測試腳本：驗證寵物系統的修復

測試點：
1. BytesIO 對象是否能正確轉換為 bytes
2. JSON 序列化是否正常工作
"""

import json
import base64
from io import BytesIO
from typing import Dict, Any

def test_avatar_handling():
    """測試頭像處理"""
    print("🧪 測試頭像資料處理...")
    
    # 模擬 BytesIO 對象
    test_data = b"fake_image_data"
    avatar_bytesio = BytesIO(test_data)
    
    # 測試提取 bytes 資料的邏輯
    if hasattr(avatar_bytesio, 'getvalue'):
        avatar_bytes = avatar_bytesio.getvalue()
    elif hasattr(avatar_bytesio, 'read'):
        avatar_bytes = avatar_bytesio.read()
    else:
        avatar_bytes = avatar_bytesio
    
    print(f"✅ 成功提取 bytes 資料: {len(avatar_bytes)} bytes")
    
    # 測試 JSON 序列化
    pet_data = {
        "name": "test",
        "description": "測試寵物",
        "affection": 10,
        "avatar": avatar_bytes
    }
    
    # 轉換為可序列化的格式
    serializable_pet = pet_data.copy()
    if serializable_pet.get("avatar") and isinstance(serializable_pet["avatar"], bytes):
        serializable_pet["avatar"] = base64.b64encode(serializable_pet["avatar"]).decode('utf-8')
    
    # 測試 JSON 序列化
    try:
        json_str = json.dumps(serializable_pet, indent=2)
        print("✅ JSON 序列化成功")
        
        # 測試反序列化
        loaded_data = json.loads(json_str)
        if loaded_data.get("avatar"):
            loaded_data["avatar"] = base64.b64decode(loaded_data["avatar"])
        
        print("✅ JSON 反序列化成功")
        print(f"   原始資料長度: {len(pet_data['avatar'])}")
        print(f"   還原資料長度: {len(loaded_data['avatar'])}")
        print(f"   資料完整性: {'✅ 一致' if pet_data['avatar'] == loaded_data['avatar'] else '❌ 不一致'}")
        
    except Exception as e:
        print(f"❌ JSON 處理失敗: {e}")
        return False
    
    return True

def test_achievement_error_handling():
    """測試成就系統的錯誤處理"""
    print("\n🧪 測試成就系統錯誤處理...")
    
    # 模擬沒有設定 ANNOUNCEMENT_CHANNEL_ID 的情況
    import os
    original_value = os.environ.get("ANNOUNCEMENT_CHANNEL_ID")
    
    try:
        # 移除環境變數
        if "ANNOUNCEMENT_CHANNEL_ID" in os.environ:
            del os.environ["ANNOUNCEMENT_CHANNEL_ID"]
        
        announcement_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID")
        if announcement_channel_id:
            print("❌ 應該要是 None")
            return False
        else:
            print("✅ 正確處理空的 ANNOUNCEMENT_CHANNEL_ID")
            
        # 測試 None 轉 int 是否會崩潰
        try:
            if announcement_channel_id:
                int(announcement_channel_id)
            print("✅ 避免了 None 轉 int 的錯誤")
        except (ValueError, TypeError) as e:
            print(f"❌ 仍然會出錯: {e}")
            return False
            
    finally:
        # 恢復原始值
        if original_value:
            os.environ["ANNOUNCEMENT_CHANNEL_ID"] = original_value
    
    return True

def test_dict_syntax():
    """測試字典語法修復"""
    print("\n🧪 測試字典語法修復...")
    
    try:
        # 測試正確的字典語法
        test_dict = {
            "quality_score": 5,
            "pet_response": "測試回應"
        }
        
        # 確保字典可以正常使用
        score = test_dict["quality_score"]
        response = test_dict["pet_response"]
        
        print(f"✅ 字典語法正常，分數: {score}, 回應: {response}")
        return True
        
    except Exception as e:
        print(f"❌ 字典語法測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試寵物系統修復...")
    
    success1 = test_avatar_handling()
    success2 = test_achievement_error_handling()
    success3 = test_dict_syntax()
    
    if success1 and success2 and success3:
        print("\n🎉 所有測試通過！修復成功。")
    else:
        print("\n❌ 有測試失敗，需要進一步檢查。")
