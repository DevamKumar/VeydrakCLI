import os
from langchain_core.messages import HumanMessage
from veydrak.llm import get_llm, POWERFUL_MODEL
from veydrak.tools import get_basic_tools
from veydrak.graphs import build_tool_agent
from veydrak.rules import load_rules

def print_messages(messages):
    for msg in messages:
        print(f"[{msg.__class__.__name__}]")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("Tool calls:", [tc["name"] for tc in msg.tool_calls])
        if msg.content:
            print(msg.content[:200] + ("..." if len(msg.content) > 200 else ""))
        print("-" * 40)

if __name__ == "__main__":
    ROOT = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ROOT, exist_ok=True)
    
    SYSTEM_PROMPT = load_rules(ROOT, "generated/logger.py")
    
    llm = get_llm(POWERFUL_MODEL)
    tools = get_basic_tools(ROOT)
    agent = build_tool_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
    
    # TURN 1
    print("\n--- TURN 1: Creating logger.py ---")
    messages = [
        HumanMessage(content="Create 'generated/logger.py' with a SimpleLogger class that writes timestamped messages to a log file.")
    ]
    result = agent.invoke({"messages": messages})
    messages = result["messages"]
    print_messages(messages)
    print("=== Turn 1 complete ===\n")
    
    # TURN 2
    print("--- TURN 2: Adding features to logger.py ---")
    messages.append(HumanMessage(content="""
    Now read the logger.py file and add these features:
    - Log levels: INFO, WARNING, ERROR
    - A method to filter logs by level
    Write the updated file.
    """))
    result = agent.invoke({"messages": messages})
    messages = result["messages"]
    print_messages(messages[-3:]) # Print just the new messages
    print("=== Turn 2 complete ===\n")
