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

    async def analyze_comfort_message(self, pet_name: str, pet_description: str, user_message: str) -> Dict[str, Any]:
        """
        分析主人的安慰訊息，評分後生成寵物回應。
        返回包含品質分數和寵物回應的字典。
        """
        try:
            # --- 第一步：分析安慰品質 ---
            analysis_prompt = f"""
            你是一個寵物心情分析師。一隻名叫「{pet_name}」的虛擬寵物（個性：{pet_description}）現在心情不好，牠的主人對牠說了以下這句話：
            
            主人的話：「{user_message}」
            
            請根據這句話分析主人安慰的品質，並以 JSON 格式輸出分析結果，包含以下兩個欄位：
            1.  `quality_score` (integer): 安慰品質的分數，範圍從 1 到 10。
                - 1-3: 敷衍或無效的安慰。
                - 4-7: 標準或還不錯的安慰。
                - 8-10: 非常有同理心、高品質的安慰。
            2.  `reasoning` (string): 簡要解釋你給這個分數的理由。

            JSON 輸出範例：
            {{
                "quality_score": 8,
                "reasoning": "主人非常溫柔，給予了寵物滿滿的安全感，並承諾會陪伴牠。"
            }}
            """
            
            analysis_response_text = await generate_text(analysis_prompt)
            
            analysis_result = {}
            try:
                if analysis_response_text.startswith("```json"):
                    analysis_response_text = analysis_response_text[7:-3].strip()
                analysis_result = json.loads(analysis_response_text)
            except json.JSONDecodeError:
                print(f"⚠️ 無法解析安慰分析的 JSON，使用預設值: {analysis_response_text}")
                analysis_result = {{"quality_score": 5, "reasoning": "主人有關心我。"}}

            quality_score = analysis_result.get("quality_score", 5)
            reasoning = analysis_result.get("reasoning", "主人有關心我。")

            # --- 第二步：根據分析結果生成寵物回應 ---
            response_prompt = f"""
            你是一隻名叫「{pet_name}」的虛擬寵物，你的個性是「{pet_description}」。
            你剛剛因為心情不好而很難過，你的主人安慰了你。

            對主人安慰的分析如下：
            - 安慰品質分數: {quality_score}/10
            - 分析理由: {reasoning}

            現在，請根據這個分析結果，用你的口吻對主人說一句話，表達你現在的心情。

            要求：
            - 如果分數很高 (8-10)，你的回應應該充滿感激和愛意，感覺完全被治癒了。
            - 如果分數中等 (4-7)，你的回應應該是感覺好多了，但可能還帶有一點點的委屈或需要更多關愛。
            - 如果分數很低 (1-3)，你的回應應該是困惑、覺得沒有被理解，或者心情沒有太大變化。
            - 語氣要完全符合你的寵物個性和當下情境。
            - 回應要自然、可愛、簡短，不超過50個字。
            - 直接說話，不要包含任何標籤或前綴，例如「{pet_name}說：」。

            範例 (高分): "嗚...謝謝主人，你的抱抱最溫暖了，我現在感覺好多了！"
            範例 (中分): "嗯...好吧...謝謝主人的關心..."
            範例 (低分): "...？"
            """

            pet_response = await generate_text(response_prompt)
            
            if not pet_response:
                pet_response = "..." if quality_score < 5 else "謝謝主人，我感覺好多了！"

            return {{
                "quality_score": quality_score,
                "pet_response": pet_response
            }}

        except Exception as e:
            print(f"❌ 分析安慰訊息並生成回應時失敗: {e}")
            return {{
                "quality_score": 1, 
                "pet_response": "...(歪著頭看著你，好像不太明白你的意思)"
            }}


# 創建一個全域實例
pet_ai_generator = PetAIGenerator()
