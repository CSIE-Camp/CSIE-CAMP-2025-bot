import google.generativeai as genai

from src import config

llm_model = None
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    llm_model = genai.GenerativeModel("gemini-2.5-flash")

async def generate_text(prompt: str) -> str:
    """
    使用 Gemini AI 生成文字回應
    參數:
        prompt (str): 輸入給 AI 的提示文字
    回傳:
        str: AI 生成的回應文字
    """
    try:
        if not llm_model:
            return "AI 服務暫時不可用，請稍後再試。"
        
        response = llm_model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "抱歉，AI 沒有生成有效的回應。"
    
    except Exception as e:
        print(f"❌ AI 文字生成失敗: {e}")
        return "AI 服務發生錯誤，請稍後再試。"
