import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

print("API key loaded" if os.getenv("OPENAI_API_KEY") else "API key NOT found: copy .env.example to .env and add your key")

from veydrak.llm.llm import get_llm, FAST_MODEL

if __name__ == "__main__":
    try:
        print(f"Initializing Veydrak LLM with model: {FAST_MODEL}...")
        llm = get_llm(FAST_MODEL)
        
        print("Sending test message...")
        response = llm.invoke("Say hello in one sentence.")
        print("\nResponse from LLM:")
        print("-" * 20)
        print(response.content)
        print("-" * 20)
    except Exception as e:
        print(f"\nError: {e}")
