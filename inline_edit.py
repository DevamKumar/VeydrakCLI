import os
from veydrak.llm import get_llm, POWERFUL_MODEL
from veydrak.sandbox import LocalSandbox
from veydrak.graphs_reflection import build_full_agent

if __name__ == "__main__":
    llm = get_llm(POWERFUL_MODEL)
    sandbox = LocalSandbox()
    full_agent = build_full_agent(llm, sandbox)
    
    print("--- 1. Testing Basic Inline Edit ---")
    existing_code = """
def greet(name):
    print("Hello " + name)
    
greet("World")
"""
    result = full_agent.invoke({
        "task": f"""Modify this existing code:
```python
{existing_code}
```
Changes requested:
- Add type hints
- Add a docstring
- Support an optional greeting parameter (default "Hello")
- Return the string instead of printing it
- Add tests that verify the output""",
        "rules": "",
        "attempts": 0,
        "max_attempts": 3,
    })
    print(f"Status: {result.get('status')} (attempts: {result.get('attempts')})")
    print(f"Output: {result.get('execution_result')}")
    print(f"\nModified code:\n{result.get('code')}")
    
    print("\n" + "="*50 + "\n")
    
    print("--- 2. Testing Rule-Enforced Inline Modernization ---")
    legacy_code = """
import csv
def read_data(file):
    f = open(file)
    r = csv.reader(f)
    data = []
    for row in r:
        data.append(row)
    f.close()
    return data
    
d = read_data("test.csv")
print(d)
"""
    MODERNIZE_RULES = """- Use context managers (with statement) for file handling
- Use pathlib.Path instead of string paths
- Use list comprehensions where appropriate
- Add proper error messages
- Use type hints everywhere"""
    
    result = full_agent.invoke({
        "task": f"""Modernize this legacy code:
```python
{legacy_code}
```
Rewrite it following modern Python best practices. Create a small test CSV inline using io.StringIO for testing.""",
        "rules": MODERNIZE_RULES,
        "attempts": 0,
        "max_attempts": 3,
    })
    print(f"Status: {result.get('status')} (attempts: {result.get('attempts')})")
    print(f"Output: {result.get('execution_result')}")
    print(f"\nModernized code:\n{result.get('code')}")
