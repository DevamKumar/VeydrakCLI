"""
ch14_toolkit_and_planner.py — Step 14: Toolkit, MCP & Planner

Demonstrates:
  1. make_tools()  — unified tool dict with run_python + run_command
  2. run_command    — execute a shell command inside the workspace
  3. Web tools      — MCP client (or fallback stubs) + researcher agent
  4. Planner        — structured Plan output with FileTask entries
  5. OrchestratorState — the TypedDict that drives the multi-agent graph
"""

import os
import asyncio

ROOT = os.path.dirname(__file__)
WORKSPACE = os.path.join(ROOT, "sample-project")

# ── Imports ──────────────────────────────────────────────────────────────────
from langchain_core.messages import HumanMessage

from veydrak.llm.llm import get_llm, structured, FAST_MODEL
from veydrak.sandbox.sandbox import LocalSandbox
from veydrak.tools.tools import make_tools
from veydrak.tools.mcp import MCP_SERVER_URL, aget_mcp_tools, get_fallback_web_tools
from veydrak.schemas.schemas import Plan
from veydrak.agent.orchestrator import OrchestratorState
from veydrak.agent.graphs import build_tool_agent
from veydrak.codebase.rules import load_rules

# ── Setup ─────────────────────────────────────────────────────────────────────
llm = get_llm(FAST_MODEL)
sandbox = LocalSandbox()
SYSTEM_PROMPT = load_rules(ROOT, "workspace/AGENTS.md")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Toolkit inventory
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PART 1: make_tools() — unified toolkit inventory")
print("=" * 60)

local = make_tools(WORKSPACE, sandbox)

print(f"MCP server URL: {MCP_SERVER_URL}")
print(f"\nLocal tools ({len(local)}):")
for name, t in local.items():
    desc = t.description[:70].replace("\n", " ")
    print(f"  {name:20s} {desc}")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: run_command demo
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 2: run_command demo")
print("=" * 60)

result = local["run_command"].invoke({
    "command": ["python", "-c", "print('hello from Veydrak')"],
    "cwd": ".",
})
print(f"run_command output: {result}")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Web tools + researcher agent
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 3: Web tools + researcher agent")
print("=" * 60)

# Try MCP first, fall back to stubs
def run(coro):
    """Run a coroutine synchronously — Python 3.14 compatible."""
    return asyncio.run(coro)

try:
    web_tools = run(aget_mcp_tools())
except Exception:
    web_tools = get_fallback_web_tools()


print(f"Web tools ({len(web_tools)}):")
for t in web_tools:
    desc = t.description[:70].replace("\n", " ")
    print(f"  {t.name:20s} {desc}")

# .cursor/mcp.json gives Cursor the same server.  Same tool, two agents.
mcp_json_path = os.path.join(WORKSPACE, ".cursor", "mcp.json")
print(f"\n.cursor/mcp.json exists: {os.path.exists(mcp_json_path)}")

# Build a researcher agent with grep + read + web tools
researcher = build_tool_agent(
    llm,
    [local["grep_files"], local["read_file"], *web_tools],
    system_prompt=SYSTEM_PROMPT,
)

result = run(researcher.ainvoke({"messages": [HumanMessage(content=(
    "streaming.py streams completions with the openai package. "
    "Search the web for the current way to stream chat completions with the "
    "OpenAI Python SDK, then read streaming.py and say whether it matches. "
    "Cite the URL you found."
))]}))

print("\n=== Researcher answer ===")
print(result["messages"][-1].content)

print("\n=== Tool calls made ===")
for msg in result["messages"]:
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            args_preview = str(tc.get("args", {}))[:80]
            print(f"  [{tc['name']}] {args_preview}")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Planner — structured Plan output
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 4: Structured Planner")
print("=" * 60)

planner = structured(llm, Plan)

plan = planner.invoke(
    "You are a coding planner.  Create a plan.\n\n"
    "Feature: Add a system prompt setting to the chatbot\n"
    "Codebase: config.py has PAGE_TITLE, PAGE_ICON, MODEL, BASE_URL. "
    "chat.py has get_client(api_key) and stream_response(client, messages). "
    "app.py is the Streamlit UI with chat history and streaming."
)

print(f"Plan: {plan.summary}")
for ft in plan.file_tasks:
    print(f"  [{ft.action:6s}] {ft.filepath}: {ft.description[:80]}")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: OrchestratorState
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 5: OrchestratorState fields")
print("=" * 60)

for name, kind in OrchestratorState.__annotations__.items():
    print(f"  {name}: {kind}")

print("\n✓ Step 14 complete — Veydrak has a toolkit, web reach, and a planner!")
