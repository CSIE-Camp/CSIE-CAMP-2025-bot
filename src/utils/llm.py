import google.generativeai as genai

from src import config

llm_model = None
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    llm_model = genai.GenerativeModel("gemini-2.5-flash")
