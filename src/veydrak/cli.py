import argparse
import asyncio
import os
import sys

from veydrak.workspace.workspace import Workspace
from veydrak.agent.graphs_orchestrator import demo_orchestrator

async def run_agent(feature_request: str, target_dir: str):
    """Run the Veydrak agent with the given feature request."""
    # Ensure target_dir exists
    if not os.path.isdir(target_dir):
        print(f"Error: Target directory '{target_dir}' does not exist.")
        sys.exit(1)
        
    print(f"Initializing Veydrak in workspace: {target_dir}")
    ws = Workspace(target_dir)
    
    # We use the current working directory as ROOT for finding rules/skills if needed,
    # or the target_dir depending on how demo_orchestrator handles it.
    agent = demo_orchestrator(os.path.abspath(target_dir), ws)
    
    config = {"configurable": {"thread_id": "cli-session"}}
    
    print(f"\nFeature Request: {feature_request}\n")
    print("Starting agent... (Press Ctrl+C to exit)\n")
    
    try:
        # We will stream the output so the user sees what's happening
        async for step in agent.astream({"feature_request": feature_request}, config):
            node_name, output = next(iter(step.items()))
            
            if node_name == "__interrupt__":
                print("\n[PAUSED] The agent is waiting for your approval of the tests and code.")
                print("To resume, you must use the LangGraph command resume API (or continue in the code).")
                print("For CLI purposes, this pauses the graph.")
                break
                
            if not isinstance(output, dict):
                continue
                
            if node_name == "plan":
                print(f"[PLAN] {output.get('plan', '')}")
            elif node_name == "code":
                print(f"[CODE] Generated {len(output.get('generated_code', []))} files.")
            elif node_name == "test":
                print(f"[TEST] {output.get('status')}")
            elif node_name == "review":
                print(f"[REVIEW] {output.get('status')}")
                
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")

def main():
    parser = argparse.ArgumentParser(description="Veydrak Coding Agent")
    parser.add_argument("instruction", type=str, help="The feature request or coding instruction.")
    parser.add_argument("--dir", type=str, default=".", help="Target workspace directory (default: current directory)")
    
    args = parser.parse_args()
    
    # We must run asyncio because LangGraph's astream/ainvoke are async
    asyncio.run(run_agent(args.instruction, args.dir))

if __name__ == "__main__":
    main()
