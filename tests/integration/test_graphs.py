import os
import pytest
from veydrak.workspace.workspace import Workspace
from veydrak.agent.graphs_orchestrator import build_orchestrator
from veydrak.agent.graphs_parallel import build_parallel_agent, add_to_list
from veydrak.llm.llm import get_llm, FAST_MODEL
from veydrak.sandbox.sandbox import LocalSandbox

@pytest.fixture
def empty_workspace(tmp_path):
    return Workspace(str(tmp_path))

def test_add_to_list_reducer():
    """Verify that the parallel map-reduce state reducer works correctly."""
    current = [{"code": "a"}]
    new_items = [{"code": "b"}, {"code": "c"}]
    
    result = add_to_list(current, new_items)
    assert len(result) == 3
    assert result[0]["code"] == "a"
    assert result[2]["code"] == "c"
    
    # Test adding single item (must be list)
    result2 = add_to_list(result, [{"code": "d"}])
    assert len(result2) == 4

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="Requires OpenAI API Key for structured output compilation")
def test_orchestrator_graph_compiles(empty_workspace):
    """Verify that the main Orchestrator graph compiles without routing errors."""
    llm = get_llm(FAST_MODEL)
    sandbox = LocalSandbox()
    agent = build_orchestrator(llm, sandbox, empty_workspace)
    assert agent is not None
    
    # Check that memory saver is attached
    assert agent.checkpointer is not None

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="Requires OpenAI API Key for structured output compilation")
def test_parallel_agent_compiles(empty_workspace):
    """Verify that the Map-Reduce Parallel Generation graph compiles."""
    llm = get_llm(FAST_MODEL)
    agent = build_parallel_agent(llm, empty_workspace)
    assert agent is not None

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="Requires OpenAI API Key")
@pytest.mark.asyncio
async def test_orchestrator_execution(empty_workspace):
    """
    Full end-to-end integration test of the agent using a simple prompt.
    Only runs if API key is present.
    """
    llm = get_llm(FAST_MODEL)
    sandbox = LocalSandbox()
    agent = build_orchestrator(llm, sandbox, empty_workspace)
    config = {"configurable": {"thread_id": "test_e2e_session"}}
    
    async for step in agent.astream({"feature_request": "Create a file named log.txt with the word 'done'"}, config):
        node_name = next(iter(step.keys()))
        if node_name == "__interrupt__":
            break
            
    # Verify state execution produced some values
    state = agent.get_state(config)
    
    values = state.values
    assert "plan" in values
    assert isinstance(values["plan"], str)
    assert len(values.get("generated_code", [])) > 0
