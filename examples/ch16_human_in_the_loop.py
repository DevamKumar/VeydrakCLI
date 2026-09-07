"""
ch16_human_in_the_loop.py — Step 16: Human-in-the-Loop with Tests

Demonstrates:
  1. Inspect the orchestrator graph — nodes, routes, human_review_node source
  2. Feature request → plan → code → test → review → interrupt at human_review
  3. Approve → apply → final verification
  4. Reject flow → feedback carried back to coder → re-generate → interrupt again
"""

import os
import sys
import asyncio
import inspect

ROOT = os.path.dirname(__file__)
WORKSPACE = os.path.join(ROOT, "sample-project")

from veydrak.workspace.workspace import Workspace
from veydrak.agent.graphs_orchestrator import build_orchestrator, demo_orchestrator, OrchestratorState
from langgraph.types import Command


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Inspect the graph
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PART 1: Graph inspection")
print("=" * 60)

# Show the human_review_node source
source = inspect.getsource(build_orchestrator)
start = source.index("def human_review_node")
end = source.index("def apply_node")
print(source[start:end].strip())

# Compile the agent
ws = Workspace(WORKSPACE)
agent = demo_orchestrator(ROOT, ws)

nodes = set(agent.get_graph().nodes) - {"__start__", "__end__"}
print(f"\nAgent compiled: {len(nodes)} nodes, 4 conditional routes, checkpointing enabled")
print(f"Nodes: {sorted(nodes)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Feature request → interrupt at human_review
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 2: Feature request → plan → code → test → review → PAUSE")
print("=" * 60)

FEATURE = (
    "Add a system prompt feature to the chatbot. "
    "Add a DEFAULT_SYSTEM_PROMPT constant in config.py. "
    "Modify chat.py so stream_response accepts an optional system_prompt parameter "
    "and prepends it as a system message. "
    "Modify app.py to add a sidebar text area where users can edit the system prompt, "
    "and pass it to stream_response."
)

config = {"configurable": {"thread_id": "demo-1"}}
print("Sending feature request to the agent...\n")

result = asyncio.run(agent.ainvoke({"feature_request": FEATURE}, config))

if "__interrupt__" not in result:
    print("ERROR: Graph did not interrupt. Status:", result.get("status"))
    sys.exit(1)

payload = result["__interrupt__"][0].value

print("=" * 60)
print("Agent paused. Waiting for human review")
print("=" * 60)
print(f"Plan: {payload['plan']}")
print(f"Review: {payload['review_result'][:200]}")
print(f"Tests:\n{payload['test_output'][:400]}")
for change in payload["changes"]:
    print(f"  {change['filepath']}: {change['explanation'][:80]}")

# Inspect the frozen state
state = asyncio.run(agent.aget_state(config))
print(f"\nAgent is waiting at node: {state.next}")

for item in state.values["generated_code"]:
    print("=" * 60)
    print(f"  {item['filepath']}")
    print("=" * 60)
    print(item["code"][:300])
    if len(item["code"]) > 300:
        print("  ... (truncated)")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Approve → apply → done
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 3: Approve → apply files → verify")
print("=" * 60)

result = asyncio.run(
    agent.ainvoke(
        Command(resume={"decision": "approve", "feedback": ""}),
        config,
    )
)

print(f"Status: {result['status']}")
print(f"\nTest output:\n{result['test_output']}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Reject flow — feedback sent back to coder
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 4: Reject flow — feedback carried back to the coder")
print("=" * 60)

# Use a snapshot of the workspace (with the approved files) and a fresh thread
config_b = {"configurable": {"thread_id": "demo-1b"}}
snapshot = ws.snapshot()
scratch_ws = Workspace(snapshot)
scratch_agent = demo_orchestrator(ROOT, scratch_ws)

paused = asyncio.run(
    scratch_agent.ainvoke(
        {
            "feature_request": (
                "Add a PAGE_SUBTITLE constant to config.py "
                "and show it under the title in app.py."
            )
        },
        config_b,
    )
)

if "__interrupt__" not in paused:
    print("ERROR: Second request did not interrupt. Status:", paused.get("status"))
    sys.exit(1)

print("Paused with:", [c["filepath"] for c in paused["__interrupt__"][0].value["changes"]])

# Reject with specific feedback
print("\nRejecting with feedback: 'Call the constant TAGLINE, not PAGE_SUBTITLE'")

paused_again = asyncio.run(
    scratch_agent.ainvoke(
        Command(
            resume={
                "decision": "reject",
                "feedback": "Call the constant TAGLINE, not PAGE_SUBTITLE, and keep it under 40 characters.",
            }
        ),
        config_b,
    )
)

if "__interrupt__" not in paused_again:
    print("ERROR: Rejected request did not re-interrupt. Status:", paused_again.get("status"))
    sys.exit(1)

state_b = asyncio.run(scratch_agent.aget_state(config_b))
print(
    "Attempt counters after the reject:",
    f"review_attempts={state_b.values.get('review_attempts', 0)},",
    f"test_attempts={state_b.values.get('test_attempts', 0)}",
)

for change in paused_again["__interrupt__"][0].value["changes"]:
    print(f"\n--- {change['filepath']} ---")
    preview = change["preview"][:400]
    print(preview)
    if len(change["preview"]) > 400:
        print("  ... (truncated)")

# Clean up the snapshot
import shutil
shutil.rmtree(os.path.dirname(snapshot), ignore_errors=True)

print("\n✓ Step 16 complete — Veydrak has human-in-the-loop with tests!")
