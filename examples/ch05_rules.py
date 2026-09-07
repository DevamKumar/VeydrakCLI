import os
from langchain_core.messages import HumanMessage
from veydrak.llm.llm import get_llm, POWERFUL_MODEL
from veydrak.tools.tools import get_basic_tools
from veydrak.agent.graphs import build_tool_agent
from veydrak.codebase.rules import list_rules, load_rules

if __name__ == "__main__":
    # Ensure workspace exists
    ROOT = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ROOT, exist_ok=True)
    
    print("--- Detected Rules ---")
    for rule in list_rules(ROOT):
        print(f"{rule.source:20} always={str(rule.always_apply):5} globs={rule.globs}")
        
    print("\n--- Compiling System Prompt for 'generated/data_processor.py' ---")
    SYSTEM_PROMPT = load_rules(ROOT, "generated/data_processor.py")
    print(SYSTEM_PROMPT)
    print("-" * 50)
    
    print("\nSetting up Agent with System Prompt...")
    llm = get_llm(POWERFUL_MODEL)
    tools = get_basic_tools(ROOT)
    
    agent = build_tool_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
    
    prompt = """
    Create a file 'generated/data_processor.py' with a DataProcessor class that:
    - Takes a list of dictionaries in __init__
    - Has filter_by(key, value) -> returns filtered list
    - Has group_by(key) -> returns dict of grouped items
    - Has summarize() -> returns count, keys present, sample row
    
    Make sure to write the file using the write_file tool.
    """
    
    print("\nInvoking Agent...")
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    
    print("\n--- Final Agent Response ---")
    for msg in result["messages"]:
        if msg.type == "ai" and not msg.tool_calls:
            print(msg.content)
