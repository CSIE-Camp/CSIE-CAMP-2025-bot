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
            base_personality = random.choice(self.personality_templates)
            return f"我是{pet_name}，一隻{base_personality}的可愛寵物！"

    async def generate_pet_avatar(self, pet_name: str, personality: str) -> Tuple[Optional[bytes], str]:
        """生成寵物頭像"""
        try:
            # 隨機選擇寵物類型和風格
            pet_type = random.choice(self.pet_types)
            style = random.choice(self.avatar_styles)
            
            # 從個性中提取關鍵詞來影響外觀
            appearance_keywords = self._extract_appearance_keywords(personality)
            
            # 構建詳細的圖片生成提示
            prompt = f"""
            A {appearance_keywords} {pet_type} character, {style}, 
            virtual pet avatar, cute and friendly, 
            simple background, centered composition,
            high quality, detailed, adorable expression,
            suitable for discord avatar, 512x512 resolution,
            vibrant colors, clean art style
            """
            
            print(f"🎨 正在為 {pet_name} 生成頭像...")
            print(f"📝 提示詞: {prompt}")
            
            # 生成圖片
            image_data = await generate_image(prompt)
            
            if image_data:
                # 讀取圖片數據
                image_bytes = image_data.getvalue()
                
                # 生成對應的表情符號
                emoji = self._get_pet_emoji(pet_type)
                
                print(f"✅ {pet_name} 的頭像生成成功！")
                return image_bytes, emoji
            else:
                print(f"❌ {pet_name} 的圖片生成失敗，使用表情符號替代")
                emoji = self._get_pet_emoji(pet_type)
                return None, emoji
                
        except Exception as e:
            print(f"❌ 生成寵物頭像失敗: {e}")
            # 回退到隨機表情符號
            emoji = random.choice(["🐱", "🐶", "🐰", "🐹", "🦊", "🐼", "🐻", "🐺", "🦁", "🐯"])
            return None, emoji

    def _extract_appearance_keywords(self, personality: str) -> str:
        """從個性描述中提取外觀關鍵詞"""
        keyword_mapping = {
            "活潑": "energetic, playful",
            "溫和": "gentle, soft",
            "聰明": "intelligent, alert",
            "懶": "lazy, sleepy", 
            "調皮": "mischievous, playful",
            "優雅": "elegant, graceful",
            "勇敢": "brave, strong",
            "害羞": "shy, timid",
            "可愛": "cute, adorable",
            "親人": "friendly, loving"
        }
        
        keywords = []
        for trait, appearance in keyword_mapping.items():
            if trait in personality:
                keywords.append(appearance)
        
        return ", ".join(keywords) if keywords else "cute, friendly"

    def _get_pet_emoji(self, pet_type: str) -> str:
        """根據寵物類型獲取對應表情符號"""
        emoji_mapping = {
            "cat": "🐱",
            "dog": "🐶", 
            "rabbit": "🐰",
            "hamster": "🐹",
            "fox": "🦊",
            "panda": "🐼",
            "bear": "🐻",
            "wolf": "🐺",
            "lion": "🦁",
            "tiger": "🐯"
        }
        return emoji_mapping.get(pet_type, "🐾")

    async def generate_pet_behavior_description(self, pet_name: str, personality: str, behavior_type: str) -> str:
        """生成寵物行為描述"""
        try:
            behavior_prompts = {
                "gift": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛從外面回來，帶了一個禮物給主人。
                請用第一人稱，用一句可愛的話描述：
                1. 你去了哪裡
                2. 發現了什麼有趣的東西當作禮物
                3. 為什麼選擇這個禮物
                要求：溫馨可愛，不超過50字
                """,
                
                "bad_mood": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你現在心情不太好，感到孤單或者遇到了小煩惱，需要主人的關愛和安慰。
                請用第一人稱，用一句讓人心疼又可愛的話說：
                1. 發生了什麼事讓你不開心（比如：下雨了、找不到玩具、肚子有點餓、想主人了等）
                2. 表達你需要主人的陪伴和安慰
                3. 展現出脆弱但可愛的一面
                要求：楚楚可憐但不過度悲傷，讓人想要馬上回應安慰，不超過35字
                例如：「嗚嗚...外面在下雨，我有點害怕，主人可以陪陪我嗎？」
                """,
                
                "treasure_hunt": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛剛在探險時發現了一個小寶物！
                請用第一人稱，用一句興奮的話描述：
                1. 你的探險過程
                2. 發現了什麼寶物
                3. 為什麼覺得這是寶物
                要求：興奮開心，專注於描述寶物本身，不超過50字
                """,
                
                "sleep": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛睡了一個美好的午覺，夢到了有趣的事情。
                請用第一人稱，用一句慵懶可愛的話分享：
                1. 你夢到了什麼
                2. 夢境中的有趣情節
                要求：慵懶可愛，有趣溫馨，不超過45字
                """,
                
                "dance": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你現在心情很好，想要跳舞給主人看！
                請用第一人稱，用一句開心活潑的話描述：
                1. 你跳了什麼舞蹈
                2. 為什麼這麼開心
                3. 想要表達什麼
                要求：活潑開心，充滿愛意，不超過45字
                """
            }
            
            prompt = behavior_prompts.get(behavior_type, f"你現在是{pet_name}，不是AI，不可以在文字中提到AI，請用可愛的方式說一句話。")
            description = await generate_text(prompt)
            
            return description if description else self._get_fallback_behavior(behavior_type)
            
        except Exception as e:
            print(f"❌ 生成寵物行為描述失敗: {e}")
            return self._get_fallback_behavior(behavior_type)

    def _get_fallback_behavior(self, behavior_type: str) -> str:
        """獲取備用行為描述"""
        fallback_behaviors = {
            "gift": "我給主人帶了一個小禮物回來！希望主人會喜歡~ (´▽｀)",
            "bad_mood": "嗚嗚...我心情不太好，主人在嗎？好想要抱抱... (´･ω･`)",
            "sleep": "我剛剛做了一個很棒的夢，夢到和主人一起玩耍~ (´∀｀)",
            "treasure_hunt": "我發現了一個好棒的寶物！主人快來看看~ ✨",
            "dance": "我好開心，想要跳舞給主人看！ヽ(´▽`)/"
        }
        return fallback_behaviors.get(behavior_type, "我是一隻可愛的寵物！(´▽｀)")

    async def analyze_comfort_message(self, pet_name: str, message_content: str) -> Tuple[str, str]:
        """分析安慰訊息的品質"""
        try:
            prompt = f"""
            你是一個寵物心理分析師。請分析以下主人對寵物 {pet_name} 的安慰訊息。

            主人的訊息：「{message_content}」

            請根據以下標準，將訊息分類為「good」、「normal」或「bad」，並提供一句話的簡短分析。
            - good: 訊息充滿愛心、耐心，能有效安撫寵物的情緒。
            - normal: 訊息表達了關心，但比較簡短或普通。
            - bad: 訊息可能帶有敷衍、不耐煩或負面的情緒，無法安慰寵物。

            請以 JSON 格式回傳結果，包含 "quality" 和 "analysis" 兩個鍵。
            例如:
            {{
                "quality": "good",
                "analysis": "主人非常溫柔，給予了寵物滿滿的安全感。"
            }}
            """
            
            response_text = await generate_text(prompt)
            
            # 移除程式碼區塊標記
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            elif response_text.strip().startswith("```"):
                 response_text = response_text.strip()[3:-3].strip()

            response_json = json.loads(response_text)
            
            quality = response_json.get("quality", "normal")
            analysis = response_json.get("analysis", "AI分析失敗，給予預設回應。")
            
            return quality, analysis

        except Exception as e:
            print(f"❌ 分析安慰訊息失敗: {e}")
            return "normal", "無法分析訊息，但心意最重要！"

    async def generate_pet_response(self, pet_name: str, personality: str, context: str, mood: Optional[str] = None) -> str:
        """生成寵物回應"""
        try:
            mood_prompt = ""
            if mood == "good":
                mood_prompt = "現在你感到非常開心和被愛。"
            elif mood == "normal":
                mood_prompt = "現在你感覺好多了。"
            elif mood == "bad":
                mood_prompt = "現在你還是有點難過和困惑。"

            prompt = f"""
            你是一隻名叫{pet_name}的虛擬寵物，個性：{personality}
            
            情境：{context}
            {mood_prompt}
            
            請以{pet_name}的身份，用第一人稱回應。
            要求：
            1. 符合你的個性特徵
            2. 語調可愛親切
            3. 適合寵物的身份
            4. 一句話內完成，不超過40字
            5. 可以使用可愛的顏文字
            """
            
            response = await generate_text(prompt)
            return response if response else f"汪汪！我是{pet_name}~ (´▽｀)"
            
        except Exception as e:
            print(f"❌ 生成寵物回應失敗: {e}")
            return f"我是{pet_name}，謝謝主人！ (´▽｀)"

    async def generate_comfort_response(self, pet_name: str, personality: str, message_content: str, quality_category: str) -> str:
        """根據回應品質生成寵物的感謝回應"""
        try:
            quality_prompts = {
                "excellent": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛才心情不好，主人給了你非常溫暖、用心的安慰：「{message_content}」
                這個安慰讓你感到被深深愛著，心情完全好轉了。
                請用第一人稱，用一句充滿感動和愛意的話回應主人。
                要求：表達深深的感動和感謝，溫暖感人，不超過40字
                """,
                
                "good": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛才心情不好，主人很用心地安慰了你：「{message_content}」
                你感受到了主人的關愛，心情好了很多。
                請用第一人稱，用一句感謝和開心的話回應主人。
                要求：表達感謝和溫暖，開心可愛，不超過35字
                """,
                
                "average": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛才心情不好，主人回應了你：「{message_content}」
                雖然簡單，但你知道主人在關心你，心情好了一些。
                請用第一人稱，用一句簡單感謝的話回應主人。
                要求：表達基本的感謝，溫和可愛，不超過30字
                """,
                
                "poor": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛才心情不好，主人回應了你：「{message_content}」
                雖然感覺主人有點敷衍，但至少知道主人注意到了你。
                請用第一人稱，用一句略帶委屈但還是感謝的話回應主人。
                要求：帶一點點委屈但不抱怨，還是感謝，不超過30字
                """,
                
                "terrible": f"""
                你是一隻名叫{pet_name}的寵物，個性：{personality}
                你剛才心情不好，但主人的回應讓你更困惑和傷心：「{message_content}」
                你不明白為什麼主人會這樣說，感到更加難過了。
                請用第一人稱，用一句傷心困惑的話回應主人。
                要求：表達困惑和傷心，但不要太過激烈，不超過30字
                """
            }
            
            prompt = quality_prompts.get(quality_category, quality_prompts["average"])
            response = await generate_text(prompt)
            
            return response if response else self._get_fallback_comfort_response(quality_category)
            
        except Exception as e:
            print(f"❌ 生成安慰回應失敗: {e}")
            return self._get_fallback_comfort_response(quality_category)

    def _get_fallback_comfort_response(self, quality_category: str) -> str:
        """獲取備用的安慰回應"""
        fallback_responses = {
            "excellent": "主人的話讓我好感動，我真的好愛好愛你！(´▽｀)ﾉ♡",
            "good": "謝謝主人的安慰，我心情好多了！你真的很溫柔~ (´∀｀)",
            "average": "謝謝主人關心我，我知道你在乎我的！(´▽｀)",
            "poor": "主人...雖然你的話有點簡單，但我知道你關心我... (´･ω･`)",
            "terrible": "主人...我不太明白你的意思，我更困惑了... (´；ω；`)"
        }
        return fallback_responses.get(quality_category, "謝謝主人~ (´▽｀)")


# 創建全局實例
pet_ai_generator = PetAIGenerator()
