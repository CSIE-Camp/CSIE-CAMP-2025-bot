import google.generativeai as genai

from src import config

llm_model = None
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    # 使用 gemini-1.5-flash，它在速度和能力之間取得了很好的平衡
    llm_model = genai.GenerativeModel("gemini-1.5-flash")
