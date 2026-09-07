import os
import shutil
import pytest
from veydrak.workspace.workspace import Workspace

@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create some dummy files
    (project_dir / "app.py").write_text("print('hello world')")
    (project_dir / "utils.py").write_text("def add(a, b): return a + b")
    
    yield str(project_dir)
    
    if project_dir.exists():
        shutil.rmtree(project_dir)

def test_workspace_initialization(temp_project):
    """Verify that Workspace initializes and reads the target directory."""
    ws = Workspace(temp_project)
    
    # Use ws.root
    assert ws.root == temp_project
    assert "app.py" in ws.list_files()
    assert "utils.py" in ws.list_files()

def test_workspace_file_operations(temp_project):
    """Verify read and create file operations."""
    ws = Workspace(temp_project)
    
    # Test reading
    content = ws.read_file("app.py")
    assert "print('hello world')" in content
    
    # Test creating (using write_file)
    ws.write_file("new_file.py", "x = 10")
    assert "new_file.py" in ws.list_files()
    assert ws.read_file("new_file.py") == "x = 10"

def test_workspace_scratch_snapshot(temp_project):
    """Verify that the Scratch Workspace correctly clones and isolates changes."""
    ws = Workspace(temp_project)
    
    # snapshot returns the temp directory
    scratch_dir = ws.snapshot()
    assert os.path.exists(scratch_dir)
    assert os.path.isdir(scratch_dir)
    
    # Files should exist in scratch
    assert os.path.exists(os.path.join(scratch_dir, "app.py"))
    
    # Write to scratch (snapshot is isolated, so we write to the temp dir manually to test isolation)
    with open(os.path.join(scratch_dir, "app.py"), "w") as f:
        f.write("print('modified in scratch')")
    
    # Verify isolation: scratch is modified, target is NOT
    with open(os.path.join(scratch_dir, "app.py"), "r") as f:
        scratch_content = f.read()
        
    with open(os.path.join(temp_project, "app.py"), "r") as f:
        target_content = f.read()
        
    assert "modified in scratch" in scratch_content
    assert "hello world" in target_content

def test_workspace_apply_changes(temp_project):
    """Verify that changes from scratch can be applied back to target."""
    ws = Workspace(temp_project)
    
    changes = [
        {"filepath": "app.py", "code": "print('modified in scratch')"}
    ]
    ws.apply_changes(changes)
    
    # Target should now be modified
    content = ws.read_file("app.py")
    assert "modified in scratch" in content
