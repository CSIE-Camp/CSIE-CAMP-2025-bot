"""
Mygo

"""

import aiohttp
import random
from src import config

async def get_mygo_imgs(keyword: str):
    async with aiohttp.ClientSession() as session:
        try:
            api_url = f"https://mygoapi.miyago9267.com/mygo/img?keyword={keyword}"
            async with session.get(api_url) as response:
                response.raise_for_status()
                result = await response.json()

                if not result.get("urls"):
                    return None
                print(result)
                return result
                # image_url = random.choice(result["urls"])["url"]
                
        except aiohttp.ClientError as e:
            print(f"呼叫 MyGo API 時發生網路錯誤: {e}")
        except Exception as e:
            print(f"處理 MyGo 搜尋時發生未預期錯誤: {e}")