"""
ch13_codebase_search.py — Step 13: Codebase Search (grep, glob, read)

Demonstrates how Veydrak explores a codebase before making changes:
  1. Manual grep_files call — find every occurrence of "stream" in the project.
  2. repo_map — print a compact tree of the workspace.
  3. search_codebase — score files by relevance to a query string.
  4. Tool-agent challenge — ask the agent how streaming works; it autonomously
     uses grep_files and read_file to discover the answer.
"""

import os
import sys

ROOT = os.path.dirname(__file__)
WORKSPACE = os.path.join(ROOT, "sample-project")
PROJECT_DIR = ROOT  # search the whole project source for streaming demos

# ── Imports ──────────────────────────────────────────────────────────────────
from langchain_core.messages import HumanMessage, SystemMessage

from veydrak.codebase.search import repo_map, search_codebase
from veydrak.tools.tools import get_basic_tools
from veydrak.llm.llm import get_llm, FAST_MODEL
from veydrak.agent.graphs import build_tool_agent
from veydrak.codebase.rules import load_rules

# ── LLM & system prompt ──────────────────────────────────────────────────────
llm = get_llm(FAST_MODEL)
SYSTEM_PROMPT = load_rules(ROOT, "workspace/AGENTS.md")

# ── 1. Manual grep ───────────────────────────────────────────────────────────
print("=" * 60)
print("PART 1: grep_files('stream') across the project source")
print("=" * 60)

# Build the grep tool bound to the whole project directory so we can call
# it directly (not via the agent).
tools_bound_to_project = get_basic_tools(PROJECT_DIR)
grep_tool = next(t for t in tools_bound_to_project if t.name == "grep_files")

grep_results = grep_tool.invoke({"pattern": "stream", "path": "."})
print(grep_results)

# ── 2. repo_map ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART 2: repo_map of the workspace")
print("=" * 60)

print(repo_map(WORKSPACE))

# ── 3. search_codebase ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART 3: search_codebase('streaming chat response')")
print("=" * 60)

ranked = search_codebase(PROJECT_DIR, "streaming chat response")
print("Top-ranked files:")
for i, path in enumerate(ranked, 1):
    rel = os.path.relpath(path, ROOT)
    print(f"  {i}. {rel}")

# ── 4. Tool-agent codebase exploration ───────────────────────────────────────
print("\n" + "=" * 60)
print("PART 4: Agent explores the codebase autonomously")
print("=" * 60)

# Give the agent tools scoped to the WHOLE project so it can grep our source.
project_tools = get_basic_tools(PROJECT_DIR)
agent = build_tool_agent(llm, project_tools, system_prompt=SYSTEM_PROMPT)

question = (
    "How does the streaming response work in this project? "
    "Use grep_files and read_file to find the answer. "
    "Name the exact file and function responsible."
)

result = agent.invoke({"messages": [HumanMessage(content=question)]})

print("\n=== Agent's answer ===")
print(result["messages"][-1].content)

print("\n=== Tool calls made ===")
for msg in result["messages"]:
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            args_preview = str(tc.get("args", {}))[:80]
            print(f"  [{tc['name']}] {args_preview}")

print("\n✓ Step 13 complete — Veydrak can now explore a codebase before editing!")
