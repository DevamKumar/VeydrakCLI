import pytest
import veydrak
from veydrak.schemas.schemas import Plan, FileTask, CodeOutput, ReviewResult

def test_package_import():
    """Verify that the package imports successfully."""
    assert veydrak.__version__ is not None

def test_schemas():
    """Verify that the Pydantic schemas work correctly."""
    # Test FileTask
    task = FileTask(action="create", filepath="test.py", description="A test file")
    assert task.action == "create"
    
    # Test Plan
    plan = Plan(summary="A test plan", file_tasks=[task])
    assert len(plan.file_tasks) == 1
    
    # Test CodeOutput
    code = CodeOutput(code="print('hello')", explanation="Simple print")
    assert code.code == "print('hello')"

    # Test ReviewResult
    review = ReviewResult(approved=True, feedback="Looks good!")
    assert review.approved is True
