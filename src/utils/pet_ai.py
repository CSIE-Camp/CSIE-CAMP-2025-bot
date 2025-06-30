"""
寵物 AI 生成工具

此模組負責為虛擬寵物系統提供 AI 生成功能：
- 寵物頭像生成
- 寵物個性敘述生成
- 寵物行為敘述生成
- 寵物對話生成
"""

import random
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
import base64
import json

from src.utils.llm import generate_text
from src.utils.image_gen import generate_image


class PetAIGenerator:
    """寵物 AI 生成器"""
    
    def __init__(self):
        self.personality_templates = [
            "活潑好動，喜歡探索新事物",
            "溫和親人，總是黏著主人",
            "聰明機警，對周圍環境很敏感",
            "慵懶愛睡，享受悠閒時光",
            "調皮搗蛋，經常做出意想不到的事",
            "優雅高貴，舉止端莊有禮",
            "勇敢無畏，保護主人是第一要務",
            "害羞內向，需要時間才會親近陌生人"
        ]
        
        # 頭像生成的風格選項
        self.avatar_styles = [
            "kawaii anime style",
            "cute cartoon style", 
            "chibi art style",
            "adorable mascot style",
            "fluffy digital art style"
        ]
        
        # 寵物類型選項
        self.pet_types = [
            "cat", "dog", "rabbit", "hamster", "fox", 
            "panda", "bear", "wolf", "lion", "tiger"
        ]

    async def generate_treasure_image_prompt(self, treasure_description: str) -> Optional[str]:
        """從寶物描述生成英文圖片提示詞"""
        try:
            prompt = f"""
            根據以下中文描述，生成一個適合 AI 繪圖的、詳細的英文提示詞。
            描述: "{treasure_description}"
            
            要求:
            1. 提示詞應專注於寶物本身的外觀、材質、光澤和細節。
            2. 風格應為：fantasy, magical, detailed, glowing, high quality, cinematic lighting, centered composition。
            3. 只返回英文提示詞，不要包含任何其他文字。

            範例:
            中文描述: "一個閃閃發光，像水晶一樣的蘋果"
            英文提示詞: "A sparkling crystal apple, fantasy, magical, detailed, glowing, high quality, cinematic lighting, centered composition"
            """
            image_prompt = await generate_text(prompt)
            return image_prompt
        except Exception as e:
            print(f"❌ 生成寶物圖片提示詞失敗: {e}")
            return "a small, glowing magic treasure chest, fantasy, magical, detailed, high quality"

    async def generate_pet_personality(self, pet_name: str) -> str:
        """生成寵物個性描述"""
        try:
            # 隨機選擇基礎個性模板
            base_personality = random.choice(self.personality_templates)
            
            prompt = f"""
            請為一隻名叫「{pet_name}」的虛擬寵物創造一個獨特的個性描述。
            
            基礎個性方向：{base_personality}
            
            請用2-3句話描述這隻寵物的：
            1. 主要性格特徵
            2. 喜好和習慣  
            3. 與主人互動的方式
            
            要求：
            - 語調可愛親切
            - 符合寵物的特質
            - 讓人想要親近和關愛
            - 不要超過60個字
            
            範例格式：「我是一隻活潑好動的小貓咪，最喜歡在陽光下打滾和追逐小玩具。雖然有時候會調皮搗蛋，但我最愛和主人撒嬌討抱抱了！」
            """
            
            personality = await generate_text(prompt)
            return personality if personality else f"我是{pet_name}，一隻{base_personality}的可愛寵物！"
        except Exception as e:
            print(f"❌ 生成寵物個性失敗: {e}")
            return f"我是{pet_name}，一隻{random.choice(self.personality_templates)}的可愛寵物！"

    async def generate_pet_avatar(self, pet_name: str, personality: str) -> Tuple[Optional[bytes], str]:
        """生成寵物頭像和代表性 emoji"""
        try:
            # 隨機選擇風格和寵物類型
            style = random.choice(self.avatar_styles)
            pet_type = random.choice(self.pet_types)
            
            # 根據寵物類型選擇 emoji
            emoji_map = {
                "cat": "🐱", "dog": "🐶", "rabbit": "🐰", "hamster": "🐹", "fox": "🦊",
                "panda": "🐼", "bear": "🐻", "wolf": "🐺", "lion": "🦁", "tiger": "🐯"
            }
            avatar_emoji = emoji_map.get(pet_type, "🐾")

            prompt = f"""
            Create a cute avatar for a virtual pet named '{pet_name}'.
            
            **Pet Type:** {pet_type}
            **Style:** {style}, cute, round, big eyes, simple background, profile picture
            **Personality:** {personality}
            
            The avatar should be a high-quality, adorable, and expressive image suitable for a profile picture.
            """
            
            image_bytes = await generate_image(prompt)
            return image_bytes, avatar_emoji
        except Exception as e:
            print(f"❌ 生成寵物頭像失敗: {e}")
            return None, "🐾"

    async def generate_pet_response(self, pet_name: str, personality: str, context: str) -> str:
        """根據情境生成寵物回應"""
        try:
            prompt = f"""
            你是一隻名叫「{pet_name}」的虛擬寵物，你的個性是「{personality}」。
            現在發生了以下事件，請根據你的個性和事件，用寵物的口吻說一句話回應主人。

            事件：{context}

            要求：
            - 語氣要符合你的個性。
            - 回應要自然、可愛、簡短。
            - 不要超過50個字。
            - 直接說話，不要包含任何標籤或前綴，例如「{pet_name}說：」。
            
            範例：
            事件：主人餵我吃了好吃的餅乾。
            回應：謝謝主人～這個餅乾好好吃喔！最喜歡主人了！
            """
            response = await generate_text(prompt)
            return response if response else "..."
        except Exception as e:
            print(f"❌ 生成寵物回應失敗: {e}")
            return "...（看起來很開心的樣子）"

    async def generate_pet_behavior_description(self, pet_name: str, personality: str, event_type: str) -> str:
        """根據事件類型生成寵物行為描述"""
        try:
            event_map = {
                "bad_mood": "心情不好，需要主人安慰",
                "treasure_hunt": "去外面探險，好像發現了什麼寶物",
                "gift": "帶了一個小禮物回來送給主人",
                "dance": "開心地跳起了舞",
                "sleep": "正在安靜地睡覺"
            }
            context = event_map.get(event_type, "正在做一些有趣的事情")

            prompt = f"""
            你是一隻名叫「{pet_name}」的虛擬寵物，你的個性是「{personality}」。
            你現在正在「{context}」。

            請用一句話，以寵物的口吻，生動地描述你現在的行為和心情。

            要求：
            - 語氣要符合你的個性。
            - 描述要自然、可愛、簡短。
            - 不要超過50個字。
            - 直接說話，不要包含任何標籤或前綴，例如「{pet_name}說：」。
            
            範例：
            事件：去外面探險，好像發現了什麼寶物
            回應：嘿嘿，你看我找到了什麼！閃亮亮的！
            """
            response = await generate_text(prompt)
            return response if response else f"我正在{context}！"
        except Exception as e:
            print(f"❌ 生成寵物行為描述失敗: {e}")
            return "我正在做一些有趣的事情！"

    async def analyze_comfort_message(self, pet_name: str, personality: str, user_message: str) -> Dict[str, Any]:
        """分析主人的安慰訊息，並給予評分和理由"""
        try:
            prompt = f"""
            你是一個寵物心情分析師。一隻名叫「{pet_name}」的虛擬寵物（個性：{personality}）現在心情不好，牠的主人對牠說了以下這句話：
            
            主人的話：「{user_message}」
            
            請根據這句話分析主人安慰的品質，並以 JSON 格式輸出分析結果，包含以下三個欄位：
            1.  `score` (integer): 安慰品質的分數，範圍從 1 到 5。
                - 1分：敷衍、無關緊要、甚至有點負面。
                - 2分：稍微有點關心，但很簡短或通用。
                - 3分：標準的安慰，有提到寵物的名字或表達關心。
                - 4分：非常有誠意，能感受到主人的溫暖和理解。
                - 5分：極度有同理心，充滿愛意，提供了具體的關懷或承諾。
            2.  `reasoning` (string): 解釋你為什麼給這個分數，用2-3句話簡要說明。
            3.  `keyword_analysis` (boolean): 這句話是否包含正面關鍵詞，例如「乖」、「秀秀」、「沒事」、「愛你」、「抱抱」等。

            JSON 輸出範例：
            {{
                "score": 4,
                "reasoning": "主人非常溫柔，給予了寵物滿滿的安全感。",
                "keyword_analysis": true
            }}
            """
            
            response_text = await generate_text(prompt)
            
            # 嘗試解析 JSON
            try:
                # 清理可能的 markdown 格式
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3].strip()
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                print(f"❌ 無法解析安慰分析的 JSON: {response_text}")
                # 如果解析失敗，提供一個預設的回應
                return {"score": 2, "reasoning": "主人有關心我，真好。", "keyword_analysis": False}

        except Exception as e:
            print(f"❌ 分析安慰訊息失敗: {e}")
            return {"score": 1, "reasoning": "好像沒有很懂我的心...", "keyword_analysis": False}


# 創建一個全域實例
pet_ai_generator = PetAIGenerator()
