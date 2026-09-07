import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

FAST_MODEL = "gpt-4o-mini"
POWERFUL_MODEL = "gpt-4o"

def get_llm(model_name: str = FAST_MODEL) -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI instance with the specified model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found. Please set it in your .env file.")
        
    return ChatOpenAI(
        model=model_name,
        temperature=0,  # Agents usually perform better with low temperature
        api_key=api_key,
    )

def structured(llm: ChatOpenAI, schema) -> ChatOpenAI:
    """
    Returns an LLM bound to a specific Pydantic schema for structured output.
    """
    return llm.with_structured_output(schema)
