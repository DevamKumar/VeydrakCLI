import os
from langchain_core.messages import HumanMessage
from veydrak.llm import get_llm, FAST_MODEL
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
    print("Setting up LLM and Tools...")
    llm = get_llm(FAST_MODEL)
    
    ws = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ws, exist_ok=True)
    
    # Let's create a dummy file in the workspace so we have something to list
    with open(os.path.join(ws, "hello.txt"), "w") as f:
        f.write("Hello Veydrak!")
        
    tools = get_basic_tools(ws)
    
    print("Building Agent Graph...")
    agent = build_tool_agent(llm, tools)
    print("Graph compiled successfully.\n")
    
    print("Invoking Agent Loop...")
    result = agent.invoke({"messages": [HumanMessage(content="List the files in the current directory")]})
    
    print("\n--- Final Conversation History ---")
    print_messages(result["messages"])
