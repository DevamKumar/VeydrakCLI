from veydrak.llm import get_llm, structured, FAST_MODEL
from veydrak.schemas import CodeOutput

if __name__ == "__main__":
    print("--- 1. Testing Unstructured LLM ---\n")
    llm = get_llm(FAST_MODEL)
    result = llm.invoke("Write a Python function that checks if a number is prime. Do not output anything other than the function.")
    print("Raw Content returned:\n")
    print(result.content)
    print("\n" + "="*50 + "\n")
    
    print("--- 2. Testing Structured LLM ---\n")
    structured_llm = structured(llm, CodeOutput)
    structured_result = structured_llm.invoke("Write a Python function that checks if a number is prime")
    
    print("Structured Result type:", type(structured_result))
    print("\nParsed Fields:")
    print("Imports:", structured_result.imports)
    print("\nCode:")
    print(structured_result.code)
    print("\nExplanation:")
    print(structured_result.explanation)
