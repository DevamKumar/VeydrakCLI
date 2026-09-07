"""
veydrak/graphs_parallel.py — Parallel Code Generation

Fan out to per-file coders with the Send API for concurrent generation.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from veydrak.schemas import Plan, CodeOutput
from veydrak.workspace import Workspace

# Reducer for parallel nodes to merge generated code
def add_to_list(left: list, right: list) -> list:
    return left + right

class ParallelState(TypedDict):
    feature_request: str
    plan: Optional[str]
    file_tasks: list[dict]
    # Reducer so parallel coders can append their results
    generated_code: Annotated[list[dict], add_to_list]

# For the Send API, we define a small state specifically for the parallel node
class CoderState(TypedDict):
    task: dict
    workspace_context: str

def build_parallel_agent(llm: BaseChatModel, workspace: Workspace):
    structured_planner = llm.with_structured_output(Plan)
    structured_coder = llm.with_structured_output(CodeOutput)

    def plan_node(state: ParallelState):
        """Generate a structured Plan from the feature request."""
        # Provide minimal workspace context for the planner
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
        }

    def route_to_parallel_coders(state: ParallelState):
        """Fan out execution: one Send per file task."""
        # Read the workspace once to pass to all parallel coders
        existing = {}
        for f in workspace.list_files():
            try:
                existing[f] = workspace.read_file(f)
            except Exception:
                pass
        
        workspace_context = "\n\n".join([f"{f}:\n```python\n{c}\n```" for f, c in existing.items()])
        
        # Return a list of Send objects targeting the 'code' node
        return [
            Send("code", {"task": task, "workspace_context": workspace_context})
            for task in state.get("file_tasks", [])
        ]

    def code_node(state: CoderState):
        """Generate code for a SINGLE file task."""
        task = state["task"]
        prompt = (
            f"Generate the COMPLETE Python file content for this task.\n"
            f"Action: {task['action']}\n"
            f"File: {task['filepath']}\n"
            f"Description: {task['description']}\n\n"
        )

        if task["action"] == "modify":
            prompt += (
                f"Current codebase context:\n"
                f"{state.get('workspace_context', '')}\n\n"
                f"Return the COMPLETE modified file. Do not omit any existing "
                f"functionality unless the task explicitly asks you to.\n"
            )

        result = structured_coder.invoke(prompt)
        
        # Return a list so the reducer (add_to_list) can concatenate it correctly
        return {
            "generated_code": [{
                "filepath": task["filepath"],
                "code": result.code,
                "explanation": result.explanation,
            }]
        }

    # Assemble the graph
    workflow = StateGraph(ParallelState)
    
    workflow.add_node("plan", plan_node)
    workflow.add_node("code", code_node)
    
    workflow.add_edge(START, "plan")
    
    # Conditional edge handles the fan-out
    workflow.add_conditional_edges("plan", route_to_parallel_coders, ["code"])
    
    # All parallel code nodes go to END automatically when they finish
    workflow.add_edge("code", END)
    
    return workflow.compile()

def demo_parallel_agent(root_dir: str, workspace: Workspace):
    from veydrak.llm import get_llm, FAST_MODEL
    llm = get_llm(FAST_MODEL)
    return build_parallel_agent(llm, workspace)
