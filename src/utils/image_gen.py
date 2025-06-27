"""
圖片生成工具函式。

此模組負責與 Hugging Face Spaces 的 Gradio 應用程序進行溝通。
"""

from io import BytesIO
from typing import Optional
import requests
from gradio_client import Client
from src import config


async def generate_image(prompt: str) -> Optional[BytesIO]:
    """
    使用 Hugging Face Spaces 的 Gradio 應用程序生成圖片。

    Args:
        prompt: 用於生成圖片的提示詞。

    Returns:
        包含圖片資料的 BytesIO 物件，失敗時返回 None。
    """
    try:
        # 驗證環境配置
        if not _validate_config():
            return None

        # 建立客戶端並生成圖片
        client = _create_client()
        result = client.predict(prompt)

        if result is None:
            print("❌ 無法連接到圖片生成服務")
            return None

        # 處理並返回結果
        return _process_result(result)

    except (ConnectionError, requests.RequestException) as e:
        print(f"❌ 網路錯誤: {e}")
        return None
    except (ValueError, AttributeError) as e:
        _handle_api_error(str(e))
        return None


def _validate_config() -> None:
    """驗證必要的配置是否存在。"""
    if not config.HUGGINGFACE_TOKEN:
        print("錯誤：HUGGINGFACE_TOKEN 未在 .env 中設定")
        return False
    return True


def _create_client() -> Client:
    """建立並返回 Gradio 客戶端。"""
    space_name = (
        getattr(config, "HUGGINGFACE_IMAGE_GEN_MODEL", None)
        or "black-forest-labs/FLUX.1-schnell"
    )
    return Client(space_name, hf_token=config.HUGGINGFACE_TOKEN)


def _process_result(result) -> Optional[BytesIO]:
    """
    處理 Gradio 返回的結果並轉換為 BytesIO。

    Args:
        result: Gradio 客戶端返回的結果。

    Returns:
        包含圖片資料的 BytesIO 物件，失敗時返回 None。
    """
    # 解析結果格式
    actual_result = _extract_actual_result(result)

    # 根據結果類型進行處理
    if isinstance(actual_result, str):
        return _handle_string_result(actual_result)
    if hasattr(actual_result, "read"):
        return _handle_file_object(actual_result)

    print(f"❓ 未知的結果格式: {type(actual_result)}")
    print(f"結果內容: {actual_result}")
    return None


def _extract_actual_result(result):
    """從可能的列表或元組中提取實際結果。"""
    if isinstance(result, (list, tuple)) and len(result) > 0:
        actual_result = result[0]
        return actual_result
    return result


def _handle_string_result(result_str: str) -> Optional[BytesIO]:
    """處理字串類型的結果（URL 或檔案路徑）。"""
    if result_str.startswith("http"):
        return _download_from_url(result_str)
    else:
        return _read_local_file(result_str)


def _download_from_url(url: str) -> Optional[BytesIO]:
    """從 URL 下載圖片。"""
    try:
        print(f"📥 下載圖片 URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BytesIO(response.content)
    except requests.RequestException as e:
        print(f"❌ 下載圖片失敗: {e}")
        return None


def _read_local_file(file_path: str) -> Optional[BytesIO]:
    """讀取本地檔案。"""
    try:
        with open(file_path, "rb") as f:
            return BytesIO(f.read())
    except FileNotFoundError:
        return None


def _handle_file_object(file_obj) -> BytesIO:
    """處理檔案物件。"""
    return BytesIO(file_obj.read())


def _handle_api_error(error_msg: str) -> None:
    """處理 API 相關錯誤並提供詳細的錯誤訊息。"""
    if "401" in error_msg or "Unauthorized" in error_msg:
        _print_auth_error_help()
    elif "403" in error_msg or "Forbidden" in error_msg:
        _print_permission_error_help()
    elif "404" in error_msg or "Not Found" in error_msg:
        _print_not_found_error_help()
    else:
        print(f"❌ 生成圖片時發生錯誤: {error_msg}")


def _print_auth_error_help() -> None:
    """印出認證錯誤的幫助訊息。"""
    print("❌ Token 驗證失敗！請檢查以下幾點：")
    print("1. Token 是否正確複製（沒有多餘的空格）")
    print("2. Token 是否已過期")
    print("3. Token 是否有足夠的權限（需要 'read' 權限）")
    print("4. 請前往 https://huggingface.co/settings/tokens 檢查你的 token 狀態")


def _print_permission_error_help() -> None:
    """印出權限錯誤的幫助訊息。"""
    print("❌ Space 存取被拒絕！可能的原因：")
    print("1. 該 Space 需要特殊權限")
    print("2. 該 Space 可能是私人的")
    print("3. 嘗試使用公開的圖片生成 Space")


def _print_not_found_error_help() -> None:
    """印出找不到資源錯誤的幫助訊息。"""
    print("❌ Space 不存在！")
    print("1. 檢查 Space 名稱是否正確")
    print("2. 該 Space 可能已被刪除或重新命名")
