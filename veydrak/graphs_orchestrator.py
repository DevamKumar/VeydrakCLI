"""
veydrak/graphs_orchestrator.py — Full multi-agent orchestrator graph.

Six nodes, four conditional routes, checkpoint-backed human-in-the-loop.

Flow:
  START → plan → code → test ─┬→ review ─┬→ human_review ─┬→ apply → END
                               │          │                │
                               └→ code    └→ code          └→ code
                               (retry)    (revise)         (human feedback)

Key features:
  - interrupt() pauses at human_review with a rich payload
  - Command(resume={"decision": "approve"|"reject", "feedback": "..."})
  - Reject resets attempt counters so the coder gets a fresh budget
  - Tests run against a scratch snapshot, not the real workspace
"""

import os
import shutil
import subprocess
from typing import Optional

from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

from veydrak.schemas import Plan, CodeOutput, ReviewResult
from veydrak.sandbox import LocalSandbox
from veydrak.workspace import Workspace


# ═══════════════════════════════════════════════════════════════════════════════
# State
# ═══════════════════════════════════════════════════════════════════════════════

class OrchestratorState(TypedDict):
    feature_request: str                # The user's original request
    plan: Optional[str]                 # Plan summary text
    file_tasks: list[dict]              # [{action, filepath, description}]
    generated_code: list[dict]          # [{filepath, code, explanation}]
    test_output: Optional[str]          # Test stdout
    test_attempts: int                  # Test retry counter
    review_attempts: int                # Review retry counter
    review_result: Optional[str]        # AI reviewer's verdict
    changes: list[dict]                 # [{filepath, code, explanation, preview}]
    status: str                         # planning|coding|testing|reviewing|approved|applying|done
    human_feedback: Optional[str]       # Feedback from human reject


# ═══════════════════════════════════════════════════════════════════════════════
# Graph builder
# ═══════════════════════════════════════════════════════════════════════════════

MAX_TEST_ATTEMPTS = 3
MAX_REVIEW_ATTEMPTS = 4

def run_tests(snapshot: Workspace, sandbox: LocalSandbox, filepaths: list[str]) -> tuple[str, bool]:
    """Run syntax checks and pytest against a workspace snapshot."""
    results = []
    all_pass = True

    # Syntax-check every generated file
    for filepath in filepaths:
        fpath = os.path.join(snapshot.root, filepath)
        try:
            proc = subprocess.run(
                ["python", "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                results.append(f"✓ {filepath}: syntax OK")
            else:
                err = proc.stderr.strip().split("\n")[-1]
                results.append(f"✗ {filepath}: {err}")
                all_pass = False
        except Exception as e:
            results.append(f"✗ {filepath}: {e}")
            all_pass = False

    # Run pytest if there are test files
    try:
        test_files = [
            f
            for f in os.listdir(snapshot.root)
            if f.startswith("test_") and f.endswith(".py")
        ]
        if test_files:
            proc = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"] + test_files,
                cwd=snapshot.root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            results.append(f"\npytest:\n{proc.stdout.strip()}")
            if proc.returncode != 0:
                all_pass = False
    except Exception:
        pass

    return "\n".join(results), all_pass



def build_orchestrator(
    llm: BaseChatModel,
    sandbox: LocalSandbox,
    workspace: Workspace,
):
    """
    Build and return the full orchestrator graph with checkpointing enabled.
    """
    structured_planner = llm.with_structured_output(Plan)
    structured_coder = llm.with_structured_output(CodeOutput)
    structured_reviewer = llm.with_structured_output(ReviewResult)

    # ── plan_node ─────────────────────────────────────────────────────────

    def plan_node(state: OrchestratorState):
        """Generate a structured Plan from the feature request."""
        existing_files = workspace.list_files()
        codebase_parts = []
        for f in existing_files:
            try:
                content = workspace.read_file(f)
                codebase_parts.append(f"{f}:\n```python\n{content}\n```")
            except Exception:
                pass

        codebase = "\n\n".join(codebase_parts) if codebase_parts else "Empty workspace."

        plan = structured_planner.invoke(
            f"You are a coding planner. Create a plan.\n\n"
            f"Feature: {state['feature_request']}\n\n"
            f"Codebase:\n{codebase}"
        )

        return {
            "plan": plan.summary,
            "file_tasks": [
                {
                    "action": ft.action,
                    "filepath": ft.filepath,
                    "description": ft.description,
                }
                for ft in plan.file_tasks
            ],
            "status": "coding",
        }

    # ── code_node ─────────────────────────────────────────────────────────

    def code_node(state: OrchestratorState):
        """Generate (or regenerate) code for every file task in the plan."""
        # Read current workspace files for modify context
        existing = {}
        for f in workspace.list_files():
            try:
                existing[f] = workspace.read_file(f)
            except Exception:
                pass

        generated = []
        for ft in state.get("file_tasks", []):
            prompt = (
                f"Generate the COMPLETE Python file content for this task.\n"
                f"Action: {ft['action']}\n"
                f"File: {ft['filepath']}\n"
                f"Description: {ft['description']}\n\n"
            )

            if ft["action"] == "modify" and ft["filepath"] in existing:
                prompt += (
                    f"Current content of {ft['filepath']}:\n"
                    f"```python\n{existing[ft['filepath']]}\n```\n\n"
                    f"Return the COMPLETE modified file. Do not omit any existing "
                    f"functionality unless the task explicitly asks you to.\n"
                )

            # Error context for retries
            if state.get("test_output") and "✗" in state.get("test_output", ""):
                prompt += (
                    f"\nPrevious test FAILED with this output:\n"
                    f"{state['test_output']}\nFix the issues.\n"
                )
            if state.get("review_result") and state.get("status") == "reviewing":
                prompt += (
                    f"\nThe AI reviewer REJECTED the code:\n"
                    f"{state['review_result']}\nAddress the feedback.\n"
                )
            if state.get("human_feedback"):
                prompt += (
                    f"\nThe human reviewer said:\n"
                    f"{state['human_feedback']}\n"
                    f"Apply this feedback EXACTLY.\n"
                )

            result = structured_coder.invoke(prompt)
            generated.append(
                {
                    "filepath": ft["filepath"],
                    "code": result.code,
                    "explanation": result.explanation,
                }
            )

        return {
            "generated_code": generated,
            "changes": [
                {
                    "filepath": g["filepath"],
                    "code": g["code"],
                    "explanation": g["explanation"],
                    "preview": g["code"],
                }
                for g in generated
            ],
            "status": "testing",
            "human_feedback": None,
        }

    def test_node(state: OrchestratorState):
        """
        Apply generated files to a scratch snapshot of the workspace,
        run syntax checks and pytest, return the output.
        """
        scratch_path = workspace.snapshot()

        try:
            scratch_ws = Workspace(scratch_path)
            scratch_ws.apply_changes(state["generated_code"])

            filepaths = [item["filepath"] for item in state["generated_code"]]
            output, all_pass = run_tests(scratch_ws, sandbox, filepaths)

        finally:
            shutil.rmtree(os.path.dirname(scratch_path), ignore_errors=True)

        attempts = state.get("test_attempts", 0) + 1

        return {
            "test_output": output,
            "test_attempts": attempts,
            "status": "reviewing" if all_pass else "testing",
        }

    # ── review_node ───────────────────────────────────────────────────────

    def review_node(state: OrchestratorState):
        """AI reviewer evaluates code quality."""
        code_parts = []
        for item in state.get("generated_code", []):
            code_parts.append(
                f"--- {item['filepath']} ---\n"
                f"```python\n{item['code']}\n```"
            )
        all_code = "\n\n".join(code_parts)

        review = structured_reviewer.invoke(
            f"Review this generated code. APPROVE it if the code is correct, "
            f"complete, and implements the requested feature. Only REJECT if "
            f"there are critical bugs, missing functionality, or the code would "
            f"not work. Minor style issues are NOT grounds for rejection.\n\n"
            f"Feature request: {state['feature_request']}\n"
            f"Plan: {state.get('plan', 'N/A')}\n\n"
            f"Code:\n{all_code}"
        )

        attempts = state.get("review_attempts", 0) + 1

        return {
            "review_result": review.feedback,
            "review_attempts": attempts,
            "status": "approved" if review.approved else "reviewing",
        }

    # ── human_review_node ─────────────────────────────────────────────────

    def human_review_node(state: OrchestratorState):
        """
        Freeze the graph with interrupt().  Hand the plan, diffs, test
        output, and review to the human.  Resume with approve or reject.
        """
        payload = {
            "plan": state.get("plan", ""),
            "review_result": state.get("review_result", ""),
            "test_output": state.get("test_output", ""),
            "changes": state.get("changes", []),
        }

        decision = interrupt(payload)

        if decision.get("decision") == "approve":
            return {"status": "applying"}
        else:
            # Reject: carry the feedback, reset counters
            return {
                "status": "coding",
                "human_feedback": decision.get("feedback", ""),
                "test_attempts": 0,
                "review_attempts": 0,
            }

    # ── apply_node ────────────────────────────────────────────────────────

    def apply_node(state: OrchestratorState):
        """Write approved code to the real workspace and verify."""
        workspace.apply_changes(state["generated_code"])

        results = []
        for item in state["generated_code"]:
            fpath = os.path.join(workspace.root, item["filepath"])
            try:
                proc = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if proc.returncode == 0:
                    results.append(f"✓ {item['filepath']}: applied and verified")
                else:
                    results.append(
                        f"⚠ {item['filepath']}: applied but: "
                        f"{proc.stderr.strip().split(chr(10))[-1]}"
                    )
            except Exception as e:
                results.append(f"⚠ {item['filepath']}: {e}")

        return {
            "test_output": "\n".join(results),
            "status": "done",
        }

    # ── Routing functions ─────────────────────────────────────────────────

    def route_after_test(state: OrchestratorState):
        if state.get("status") == "reviewing":
            return "review"
        if state.get("test_attempts", 0) >= MAX_TEST_ATTEMPTS:
            return END
        return "code"

    def route_after_review(state: OrchestratorState):
        if state.get("status") == "approved":
            return "human_review"
        if state.get("review_attempts", 0) >= MAX_REVIEW_ATTEMPTS:
            return END
        return "code"

    def route_after_human(state: OrchestratorState):
        if state.get("status") == "applying":
            return "apply"
        return "code"

    # ── Assemble the graph ────────────────────────────────────────────────

    workflow = StateGraph(OrchestratorState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("code", code_node)
    workflow.add_node("test", test_node)
    workflow.add_node("review", review_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("apply", apply_node)

    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "code")
    workflow.add_edge("code", "test")
    workflow.add_conditional_edges(
        "test", route_after_test, ["review", "code", END]
    )
    workflow.add_conditional_edges(
        "review", route_after_review, ["human_review", "code", END]
    )
    workflow.add_conditional_edges(
        "human_review", route_after_human, ["apply", "code"]
    )
    workflow.add_edge("apply", END)

    return workflow.compile(checkpointer=MemorySaver())


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience factory
# ═══════════════════════════════════════════════════════════════════════════════


def demo_orchestrator(root_dir: str, workspace: Workspace):
    """
    Wire up the LLM, sandbox, and workspace into a compiled orchestrator.
    """
    from veydrak.llm import get_llm, FAST_MODEL

    llm = get_llm(FAST_MODEL)
    sandbox = LocalSandbox()

    return build_orchestrator(llm, sandbox, workspace)
