from veydrak.sandbox.sandbox import LocalSandbox
from veydrak.agent.graphs_bugbot import build_bugbot, AgentState
from veydrak.llm.llm import get_llm, FAST_MODEL
import inspect
from veydrak import graphs_bugbot

if __name__ == "__main__":
    print("--- 1. Testing Sandbox ---")
    sandbox = LocalSandbox()
    out = sandbox.run_python("import time; time.sleep(20)", timeout=2)
    print(out)
    print("ok:", out.ok, "timed_out:", out.timed_out)
    
    print("\n--- 2. Inspecting AgentState ---")
    for name, kind in AgentState.__annotations__.items():
        print(f"  {name}: {kind}")
        
    print("\n--- 3. Compiling Bugbot ---")
    llm = get_llm(FAST_MODEL)
    bugbot = build_bugbot(llm, sandbox)
    print("Self-correcting graph compiled")
    
    print("\n--- 4. Easy Task: Fibonacci (Should succeed quickly) ---")
    result = bugbot.invoke({"task": "Print the first 10 Fibonacci numbers", "attempts": 0, "max_attempts": 3})
    print(f"Status: {result.get('status')}")
    print(f"Attempts: {result.get('attempts')}")
    print(f"Explanation: {result.get('explanation')}")
    print(f"Output: {result.get('execution_result')}")
    
    print("\n--- 5. Impossible Task: Diffusers (Should fail 3 times due to ImportError) ---")
    inputs = {
        "task": "Write the diffusers code to generate an image of a cat using the model 'CompVis/stable-diffusion-v1-4'. Import diffusers, torch, and anything else you need.",
        "attempts": 0,
        "max_attempts": 3,
    }
    
    for step in bugbot.stream(inputs):
        node_name, state = next(iter(step.items()))
        if node_name == "generate":
            print(f"[generate] Attempt {state.get('attempts', 0) + 1}")
            code_preview = state.get('code', '')[:80].replace('\n', ' ')
            print(f"  Code preview: {code_preview}...")
        elif node_name == "execute":
            if state.get("error"):
                error_preview = state['error'][:100].replace('\n', ' ')
                print(f"[execute] FAILED: {error_preview}")
            else:
                out_preview = state.get('execution_result', '')[:100].replace('\n', ' ')
                print(f"[execute] SUCCESS: {out_preview}")
    print("\nFinished stream test.")
