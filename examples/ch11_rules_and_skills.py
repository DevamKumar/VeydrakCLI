import os
from veydrak.codebase.rules import load_rules
from veydrak.llm.llm import get_llm, FAST_MODEL
from veydrak.sandbox.sandbox import LocalSandbox
from veydrak.agent.graphs_reflection import build_full_agent
from veydrak.codebase.skills import load_skills, skills_catalog, make_read_skill_tool
from veydrak.agent.graphs import build_tool_agent
from langchain_core.messages import HumanMessage

def print_messages(messages, width=100):
    for msg in messages:
        print(f"[{msg.__class__.__name__}]")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("Tool calls:", [tc["name"] for tc in msg.tool_calls])
        if msg.content:
            print(msg.content[:width] + ("..." if len(msg.content) > width else ""))
        print("-" * 40)

if __name__ == "__main__":
    ROOT = os.path.join(os.getcwd(), "workspace")
    os.makedirs(ROOT, exist_ok=True)
    
    print("--- 1. Testing Dynamic Rules Globbing ---")
    app_rules = load_rules(ROOT, "workspace/app.py")
    test_rules = load_rules(ROOT, "workspace/tests/test_sort.py")
    
    print("rules for app.py mention tests.mdc:", "Testing Guidelines" in app_rules)
    print("rules for tests/test_sort.py mention tests.mdc:", "Testing Guidelines" in test_rules)
    
    print("\n--- 2. Invoking Full Agent with test_rules ---")
    llm = get_llm(FAST_MODEL)
    sandbox = LocalSandbox()
    full_agent = build_full_agent(llm, sandbox)
    
    result_with_rules = full_agent.invoke({
        "task": "Write a function to sort a list of dictionaries by a given key. Write a single function to do this, and then call it using sample data and assert its output. Do not write a unittest class or function.",
        "rules": test_rules,
        "attempts": 0,
        "max_attempts": 3,
    })
    print("=== With the test-file rules ===")
    print(result_with_rules.get("code", ""))
    
    print("\n--- 3. Testing Skills Engine ---")
    skills = load_skills(ROOT)
    print("Skills Catalog:")
    print(skills_catalog(skills))
    
    # We build a tool agent equipped with the read_skill tool, 
    # and the skills catalog as its system prompt.
    print("--- 4. Invoking Tool Agent to load a skill ---")
    skill_agent = build_tool_agent(llm, [make_read_skill_tool(skills)], system_prompt=skills_catalog(skills))
    
    result = skill_agent.invoke({"messages": [HumanMessage(content=(
        "I am about to add a feature to an unfamiliar codebase. Load the skill that covers this "
        "and give me its steps, one line each."
    ))]})
    print_messages(result["messages"], width=300)
