import os
import pytest
from veydrak.codebase.search import search_codebase, repo_map
from veydrak.sandbox.sandbox import LocalSandbox
from veydrak.workspace.workspace import Workspace

@pytest.fixture
def sample_workspace_path(tmp_path):
    project_dir = tmp_path / "search_project"
    project_dir.mkdir()
    
    (project_dir / "main.py").write_text("def run():\n    print('Hello')\n")
    (project_dir / "config.py").write_text("DEBUG = True\nPORT = 8080\n")
    
    yield str(project_dir)

def test_repo_map(sample_workspace_path):
    """Verify repo_map generates a tree structure string."""
    ws = Workspace(sample_workspace_path)
    tree = repo_map(ws.root)
    assert "main.py" in tree
    assert "config.py" in tree

def test_search_codebase(sample_workspace_path):
    """Verify search codebase finds terms across files."""
    # search_codebase takes (root_dir: str, query: str)
    results = search_codebase(sample_workspace_path, "DEBUG")
    
    # Returns a list of paths
    assert any("config.py" in str(res) for res in results)

def test_local_sandbox_execution():
    """Verify LocalSandbox successfully executes Python code and captures output."""
    sandbox = LocalSandbox()
    
    code = "print('sandbox output')\nx = 10"
    result = sandbox.run_python(code)
    
    assert result.ok is True
    assert "sandbox output" in result.stdout
    assert result.timed_out is False

def test_local_sandbox_failure():
    """Verify LocalSandbox handles syntax/runtime errors and returns traceback."""
    sandbox = LocalSandbox()
    
    code = "def error():\n    raise ValueError('Test error')\nerror()"
    result = sandbox.run_python(code)
    
    assert result.ok is False
    assert "ValueError: Test error" in result.stderr
