import os
import asyncio
from veydrak.workspace import Workspace
from veydrak.graphs_orchestrator import demo_orchestrator

ROOT = os.path.dirname(__file__)
WORKSPACE = os.path.join(ROOT, "workspace")

ws = Workspace(WORKSPACE)
agent = demo_orchestrator(ROOT, ws)

config = {"configurable": {"thread_id": "demo-1"}}

async def run_time_travel_demo():
    print("=" * 60)
    print("PART 1: Populating state history for demo-1")
    print("=" * 60)
    
    # Run a quick feature request to generate some history.
    # The orchestrator will pause at human_review.
    result = await agent.ainvoke({"feature_request": "Add a simple logging function to config.py"}, config)
    print(f"Agent reached: {result.get('status', 'unknown status')}")
    
    print("\n" + "=" * 60)
    print("PART 2: Inspecting State History (Time-Travel)")
    print("=" * 60)
    
    # Use get_state_history to view the sequence of states
    history = list(agent.get_state_history(config))
    print(f"Total checkpoints for demo-1: {len(history)}\n")
    
    for i, snapshot in enumerate(reversed(history)):
        values = snapshot.values
        # Handle cases where values might be empty for the very first START state
        status = values.get('status', 'initial') if values else 'initial'
        files = len(values.get('generated_code', [])) if values else 0
        tests = values.get('test_attempts', 0) if values else 0
        reviews = values.get('review_attempts', 0) if values else 0
        
        print(
            f"  Step {i}: status={status}, files={files}, "
            f"tests={tests}, reviews={reviews}, next={snapshot.next}"
        )

    print("\n" + "=" * 60)
    print("PART 3: Streaming Node Outputs with astream")
    print("=" * 60)
    
    config2 = {"configurable": {"thread_id": "demo-2"}}
    
    async def stream_second_feature() -> None:
        async for step in agent.astream({"feature_request": (
            "Add a 'Clear Chat' button to the sidebar in app.py that resets st.session_state.messages "
            "to an empty list and reruns the app. Also add a message counter in the sidebar that shows "
            "how many messages are in the conversation."
        )}, config2):
            # step is a dict like {"node_name": {...state...}}
            node_name, output = next(iter(step.items()))
            
            if node_name == "__interrupt__":
                print("\n[PAUSED] waiting for your approval")
                continue
            
            if not isinstance(output, dict):
                continue
                
            if node_name == "plan":
                print(f"[PLAN] {output.get('plan', '')}")
                for ft in output.get("file_tasks", []):
                    print(f"  [{ft['action']}] {ft['filepath']}")
            elif node_name == "code":
                for item in output.get("generated_code", []):
                    print(f"[CODE] {item['filepath']}: {item['explanation'][:80]}")
            elif node_name == "test":
                print(f"[TEST] {output.get('status')}")
            elif node_name == "review":
                print(f"[REVIEW] {output.get('status')}: {output.get('review_result', '')[:100]}")

    await stream_second_feature()
    
    print("\n✓ Step 18 complete — Time-Travel Debugging demonstrated!")

if __name__ == "__main__":
    asyncio.run(run_time_travel_demo())
