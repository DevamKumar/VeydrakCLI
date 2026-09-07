"""
veydrak/orchestrator.py — OrchestratorState for the multi-agent graph.

This TypedDict defines the shared state that flows between nodes
(planner, coder, reviewer) in the full orchestrator graph (Step 15).

Defined here in Step 14 so the planner can populate it.
"""

from typing import Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from veydrak.schemas import Plan, FileTask


class OrchestratorState(TypedDict):
    """Shared state for the multi-agent orchestrator graph."""

    task: str
    """The user's original request / feature description."""

    plan: Optional[Plan]
    """The structured plan produced by the planner node."""

    messages: list[BaseMessage]
    """Conversation history and tool call exchanges."""

    current_file_task: Optional[FileTask]
    """The file task the coder node is currently working on."""

    completed_tasks: list[str]
    """File paths of successfully completed file tasks."""

    status: str
    """Current phase: 'planning' | 'coding' | 'reviewing' | 'done'."""
