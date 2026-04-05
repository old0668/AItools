import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    print(f"Testing API Key: {api_key[:4]}...{api_key[-4:]}")
    
    client = genai.Client(api_key=api_key)
    print("\n--- Available Models ---")
    try:
        # Note: The new SDK might have a different method to list models
        # or we might need to use the generativeai legacy library for listing
        for model in client.models.list():
            print(f"Model Name: {model.name}")
            print(f"Supported Actions: {model.supported_actions}")
            print("-" * 20)
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
