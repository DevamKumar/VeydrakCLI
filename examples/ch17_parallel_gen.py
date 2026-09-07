import os
import inspect
from veydrak.workspace.workspace import Workspace
from veydrak.agent.graphs_parallel import ParallelState, add_to_list, build_parallel_agent, demo_parallel_agent
from veydrak.agent.graphs_orchestrator import run_tests
from veydrak.sandbox.sandbox import LocalSandbox

ROOT = os.path.dirname(__file__)
WORKSPACE = os.path.join(ROOT, "sample-project")

ws = Workspace(WORKSPACE)
snapshot = Workspace(ws.snapshot())  # the parallel demo works on a copy of the workspace

for name, kind in ParallelState.__annotations__.items():
    print(f"  {name}: {kind}")
print(inspect.getsource(add_to_list))
print(inspect.getsource(build_parallel_agent))

parallel_agent = demo_parallel_agent(ROOT, ws)

result = parallel_agent.invoke({"feature_request": (
    "Add two features to the chatbot: "
    "1) A conversation export button in the sidebar that saves chat history as a .txt file. "
    "2) A model selector dropdown in the sidebar that lets users pick from 3 models. "
    "Update config.py with available models, chat.py to accept a model parameter, "
    "and app.py for the UI controls. Accept the API key from the sidebar as before, do not change it."
)})

print("=" * 60)
print(f"  {len(result.get('generated_code', []))} files generated in parallel")
print("=" * 60)
for item in result.get("generated_code", []):
    print(f"\n--- {item['filepath']} ---")
    print(f"  {item['explanation'][:120]}")
    print(item["code"][:300])
    if len(item["code"]) > 300:
        print("  ...")

for item in result.get("generated_code", []):
    snapshot.write_file(item["filepath"], item["code"])
    print(f"  Applied: {item['filepath']}")

output, ok = run_tests(snapshot, LocalSandbox(), [i["filepath"] for i in result.get("generated_code", [])])
print("\nTests:", "PASS" if ok else "FAIL")
print(output)
