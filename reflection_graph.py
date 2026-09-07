from veydrak.llm import get_llm, structured, FAST_MODEL
from veydrak.schemas import ReviewResult
from veydrak.sandbox import LocalSandbox
from veydrak.graphs_reflection import build_full_agent, FullAgentState
import inspect

if __name__ == "__main__":
    llm = get_llm(FAST_MODEL)
    
    print("--- 1. Testing Reviewer LLM Component ---")
    reviewer = structured(llm, ReviewResult)
    test_code = "x = [1,2,3]\nfor i in x:\n print(i)"
    review = reviewer.invoke(f"Review this Python code for quality (type hints, naming, PEP 8, efficiency):\n\n{test_code}")
    print(f"Approved: {review.approved}")
    print(f"Feedback: {review.feedback}")
    
    print("\n--- 2. Compiling Full Agent ---")
    sandbox = LocalSandbox()
    full_agent = build_full_agent(llm, sandbox)
    print("Full agent compiled with Reflection!")
    
    print("\n--- 3. Task: Sieve of Eratosthenes (Invoke) ---")
    result = full_agent.invoke({
        "task": "Write a function to find all prime numbers up to n using the Sieve of Eratosthenes. Test it by printing primes up to 50.",
        "rules": "Must include type hints and clear variable names.",
        "attempts": 0,
        "max_attempts": 3,
    })
    print(f"Status: {result.get('status')} (after {result.get('attempts')} attempt(s))")
    print(f"Output:\n{result.get('execution_result')}")
    
    print("\n--- 4. Task: Point Dataclass (Stream) ---")
    inputs = {
        "task": "Create a dataclass called 'Point' with x,y coordinates. Add methods for distance_to(other), midpoint(other), and __str__. Test with Point(3,4) and Point(0,0).",
        "rules": "",
        "attempts": 0,
        "max_attempts": 3,
    }
    
    for step in full_agent.stream(inputs):
        node_name, state = next(iter(step.items()))
        if node_name == "generate":
            print(f"[generate] Code length: {len(state.get('code', ''))} chars")
        elif node_name == "execute":
            if state.get("error"):
                print(f"[execute] FAILED: {state['error'][:150].replace(chr(10), ' ')}")
            else:
                print(f"[execute] OK: {state.get('execution_result', '')[:150].replace(chr(10), ' ')}")
        elif node_name == "review":
            print(f"[review] {state.get('status')}: {state.get('review_feedback', '')[:150].replace(chr(10), ' ')}")
