import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key":
        print("錯誤：您的 GEMINI_API_KEY 仍然是佔位符！")
        return
    
    print(f"正在嘗試連接 Gemini API (Key: {key[:5]}...{key[-5:]})")
    try:
        client = genai.Client(api_key=key)
        print("連線成功！以下是您可以使用的模型列表：")
        models = client.models.list()
        for m in models:
            print(f"- {m.name}")
            if "flash" in m.name.lower():
                print(f"  (建議使用的名稱: {m.name.split('/')[-1]})")
    except Exception as e:
        print(f"連線失敗：{e}")

if __name__ == "__main__":
    diagnose()
