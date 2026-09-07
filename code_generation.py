import os
from langchain_core.messages import HumanMessage
from veydrak.llm import get_llm, POWERFUL_MODEL
from veydrak.tools import get_basic_tools
from veydrak.graphs import build_tool_agent

def print_messages(messages):
    for msg in messages:
        print(f"[{msg.__class__.__name__}]")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("Tool calls:", msg.tool_calls)
        if msg.content:
            print(msg.content)
        print("-" * 40)

if __name__ == "__main__":
    print("Setting up LLM and Tools for Code Generation...")
    # For code generation, POWERFUL_MODEL (gpt-4o) might be better, but FAST_MODEL works too.
    llm = get_llm(POWERFUL_MODEL)
    
    ws = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ws, exist_ok=True)
    
    tools = get_basic_tools(ws)
    agent = build_tool_agent(llm, tools)
    
    prompt = """
    Create a Python file called 'generated/calculator.py' with a Calculator class that has:
    - add, subtract, multiply, divide methods
    - A history list that tracks all operations
    - A get_history method that returns the history
    
    Write the file using the write_file tool.
    """
    
    print("Invoking Agent with Code Generation Task...\n")
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    
    print("\n--- Final Conversation History ---")
    print_messages(result["messages"])
