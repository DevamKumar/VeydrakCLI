import os
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from veydrak.llm.llm import get_llm, FAST_MODEL
from veydrak.tools.tools import get_basic_tools
from veydrak.agent.graphs import build_tool_agent
from veydrak.codebase.rules import load_rules

async def stream_agent(agent, user_message: str) -> None:
    inputs = {"messages": [HumanMessage(content=user_message)]}
    
    print("\n--- Starting Stream ---")
    async for event in agent.astream_events(inputs, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                # We print tokens dynamically as they arrive
                print(chunk.content, end="", flush=True)
        elif event["event"] == "on_tool_start":
            print(f"\n\n--- calling tool: {event['name']} ---")
        elif event["event"] == "on_tool_end":
            print(f"--- tool done ---\n")

if __name__ == "__main__":
    ROOT = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ROOT, exist_ok=True)
    
    # We compile the system prompt just like before
    SYSTEM_PROMPT = load_rules(ROOT, "generated/calculator.py")
    
    llm = get_llm(FAST_MODEL)
    tools = get_basic_tools(ROOT)
    
    # We omit the system prompt in build_tool_agent because we inject it in the inputs above,
    # or we can pass it to the agent directly and just send HumanMessage in inputs. 
    # Let's pass it to the agent graph like we did in chapter 5 for consistency, 
    # and just pass the HumanMessage to `inputs`.
    agent = build_tool_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
    
    async def main():
        await stream_agent(agent, "List files in the 'generated' directory and read calculator.py")
        
    asyncio.run(main())
