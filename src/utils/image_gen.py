"""
圖片生成工具函式。

此模組負責與 Hugging Face Spaces 的 Gradio 應用程序進行溝通。
"""

from io import BytesIO
from gradio_client import Client
from src import config
import requests


async def generate_image(prompt: str) -> BytesIO | None:
    """
    使用 Hugging Face Spaces 的 Gradio 應用程序生成圖片，並將其作為 BytesIO 物件回傳。

    Args:
        prompt: 用於生成圖片的提示詞。

    Returns:
        包含圖片資料的 BytesIO 物件 (如果成功)，否則為 None。
    """
    try:
        # 檢查必要的環境變數
        if not config.HUGGINGFACE_TOKEN:
            print("錯誤：HUGGINGFACE_TOKEN 未在 .env 中設定。")
            return None

        # 使用指定的 Space 或預設 Space
        space_name = (
            getattr(config, "HUGGINGFACE_IMAGE_GEN_MODEL", None)
            or "black-forest-labs/FLUX.1-schnell"
        )
        print(space_name)

        # 初始化 Gradio Client 連接到指定的 Space
        print(f"🔗 正在連接到 Hugging Face Space: {space_name}")
        client = Client(space_name, hf_token=config.HUGGINGFACE_TOKEN)

        # 嘗試不同的常見 API 端點名稱
        api_endpoints = ["/predict", "", None, "/generate", "/inference"]

        result = None
        successful_endpoint = None

        print("🎯 開始圖片生成請求...")
        for api_name in api_endpoints:
            try:
                print(f"嘗試端點: {api_name or 'default'}")
                if api_name is None:
                    result = client.predict(prompt)
                else:
                    result = client.predict(prompt, api_name=api_name)
                successful_endpoint = api_name
                break
            except Exception:
                continue

        if result is None:
            print("❌ 無法連接到圖片生成服務")
            return None

        print(f"✅ 收到結果: {type(result)}")
        print(f"結果內容預覽: {str(result)[:200]}...")

        # 處理結果 - Gradio 可能返回不同格式的結果
        if isinstance(result, (list, tuple)) and len(result) > 0:
            # 如果結果是列表或元組，取第一個元素
            actual_result = result[0]
            print(f"從列表中取得結果: {type(actual_result)}")
        else:
            actual_result = result

        if isinstance(actual_result, str):
            # 如果結果是檔案路徑或 URL
            if actual_result.startswith("http"):
                # 是 URL，下載圖片
                print(f"📥 下載圖片 URL: {actual_result}")
                response = requests.get(actual_result, timeout=30)
                response.raise_for_status()
                return BytesIO(response.content)
            else:
                # 是本地檔案路徑，讀取檔案
                print(f"📁 讀取本地檔案: {actual_result}")
                try:
                    with open(actual_result, "rb") as f:
                        return BytesIO(f.read())
                except FileNotFoundError:
                    print(f"❌ 找不到檔案: {actual_result}")
                    return None
        elif hasattr(actual_result, "read"):
            # 如果結果是檔案物件
            print("📄 處理檔案物件")
            return BytesIO(actual_result.read())
        else:
            print(f"❓ 未知的結果格式: {type(actual_result)}")
            print(f"結果內容: {actual_result}")
            return None

    except (ConnectionError, requests.RequestException, FileNotFoundError) as e:
        print(f"❌ 網路或檔案錯誤: {e}")
        return None
    except ImportError as e:
        print(f"❌ 缺少必要的套件: {e}")
        print("請執行: pip install gradio_client pillow")
        return None
    except (ValueError, AttributeError) as e:
        error_msg = str(e)

        if "401" in error_msg or "Unauthorized" in error_msg:
            print("❌ Token 驗證失敗！請檢查以下幾點：")
            print("1. Token 是否正確複製（沒有多餘的空格）")
            print("2. Token 是否已過期")
            print("3. Token 是否有足夠的權限（需要 'read' 權限）")
            print(
                "4. 請前往 https://huggingface.co/settings/tokens 檢查你的 token 狀態"
            )
        elif "403" in error_msg or "Forbidden" in error_msg:
            print("❌ Space 存取被拒絕！可能的原因：")
            print("1. 該 Space 需要特殊權限")
            print("2. 該 Space 可能是私人的")
            print("3. 嘗試使用公開的圖片生成 Space")
        elif "404" in error_msg or "Not Found" in error_msg:
            print("❌ Space 不存在！")
            print("1. 檢查 Space 名稱是否正確")
            print("2. 該 Space 可能已被刪除或重新命名")
        else:
            print(f"❌ 生成圖片時發生錯誤: {e}")
            print("完整錯誤訊息:", error_msg)

        return None
