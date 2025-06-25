# -*- coding: utf-8 -*-
"""
圖片生成工具函式。

此模組負責與後端圖片生成 API 進行溝通。
"""
import requests
import base64
from io import BytesIO
from src import config


async def request_photo(prompt: str) -> requests.Response | None:
    """
    發送請求到後端 API 端點，以生成圖片。

    Args:
        prompt: 用於生成圖片的提示詞。

    Returns:
        requests.Response 物件 (如果請求成功)，否則為 None。
    """
    if not config.NGROK_URL:
        print("錯誤：NGROK_URL 未在 config.py 中設定。")
        return None

    # 注意：requests 是同步函式庫，在異步程式中使用會阻塞事件循環。
    # 為了簡單起見暫時使用，但在正式產品中建議改用 aiohttp。
    try:
        response = requests.post(
            f"{config.NGROK_URL}/",
            json={"prompt": prompt},
            timeout=120,  # 設定較長的超時時間以應對可能較慢的圖片生成
        )
        response.raise_for_status()  # 若狀態碼非 2xx，則拋出異常
        return response
    except requests.exceptions.RequestException as e:
        print(f"圖片生成 API 請求時發生網路錯誤: {e}")
        return None


async def generate_bytesIO(prompt: str) -> BytesIO | None:
    """
    調用 API 生成圖片，並將其作為 BytesIO 物件回傳。

    Args:
        prompt: 用於生成圖片的提示詞。

    Returns:
        包含圖片資料的 BytesIO 物件 (如果成功)，否則為 None。
    """
    try:
        response = await request_photo(prompt)

        if response is None:
            # request_photo 內部已記錄錯誤
            return None

        data = response.json()

        if data.get("status") != "success":
            error_message = data.get("message", "未提供詳細錯誤訊息")
            print(f"API 返回圖片生成失敗狀態: {error_message}")
            return None

        # 將 base64 字串解碼為圖片二進位資料
        image_data = base64.b64decode(data["image"])
        return BytesIO(image_data)

    except Exception as e:
        print(f"圖片生成或資料解碼過程中發生未預期錯誤: {e}")
        return None
