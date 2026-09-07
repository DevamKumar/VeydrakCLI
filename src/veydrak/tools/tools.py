import os
from pathlib import Path
from typing import List, Callable
from langchain_core.tools import tool, BaseTool

def _resolve_path(workspace_dir: str, requested_path: str) -> Path | str:
    """
    Resolves a requested path against the workspace directory.
    Returns the resolved Path object if it is safely within the workspace,
    otherwise returns an Error string.
    """
    try:
        base = Path(workspace_dir).resolve()
        requested = (base / requested_path).resolve()
        
        # Check if the requested path is a subpath of the base path
        if not str(requested).startswith(str(base)):
            return f"Error: Path '{requested_path}' attempts to escape workspace '{workspace_dir}'"
            
        return requested
    except Exception as e:
        return f"Error resolving path: {e}"

def get_basic_tools(workspace_dir: str) -> List[BaseTool]:
    """
    Returns a list of basic tools bound to the specified workspace directory.
    """
    
    @tool
    def read_file(path: str) -> str:
        """
        Read the contents of a file in the workspace.
        """
        resolved = _resolve_path(workspace_dir, path)
        if isinstance(resolved, str):
            return resolved # Error message
        
        try:
            with open(resolved, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File '{path}' not found."
        except Exception as e:
            return f"Error reading file '{path}': {e}"

    @tool
    def write_file(path: str, content: str) -> str:
        """
        Write content to a file in the workspace. Will create directories if they don't exist.
        """
        resolved = _resolve_path(workspace_dir, path)
        if isinstance(resolved, str):
            return resolved # Error message
            
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to '{path}'."
        except Exception as e:
            return f"Error writing to file '{path}': {e}"

    @tool
    def list_directory(path: str = ".") -> str:
        """
        List the contents of a directory within the workspace.
        """
        resolved = _resolve_path(workspace_dir, path)
        if isinstance(resolved, str):
            return resolved # Error message
            
        try:
            if not resolved.exists():
                return f"Error: Directory '{path}' does not exist."
            if not resolved.is_dir():
                return f"Error: '{path}' is not a directory."
                
            items = []
            for item in resolved.iterdir():
                prefix = "DIR  " if item.is_dir() else "FILE "
                items.append(f"{prefix} {item.name}")
                
            if not items:
                return f"Directory '{path}' is empty."
            return "\n".join(sorted(items))
        except Exception as e:
            return f"Error listing directory '{path}': {e}"

    @tool
    def grep_files(pattern: str, path: str = ".") -> str:
        """
        Recursively search for a string or regex pattern across all text files
        in the workspace (or a sub-path of it).  Returns matches in the format
        'file:line: content', one per line.  Returns up to 200 matches.
        Use this to locate functions, class names, imports, or any keyword.
        """
        import re

        resolved = _resolve_path(workspace_dir, path)
        if isinstance(resolved, str):
            return resolved  # Error message

        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"Error: invalid regex pattern '{pattern}': {e}"

        SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
        results: list[str] = []

        search_root = resolved if resolved.is_dir() else resolved.parent

        for dirpath, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for lineno, line in enumerate(text.splitlines(), 1):
                    if compiled.search(line):
                        rel = fpath.relative_to(Path(workspace_dir).resolve())
                        results.append(f"{rel}:{lineno}: {line.strip()}")
                        if len(results) >= 200:
                            results.append("... (truncated at 200 matches)")
                            return "\n".join(results)

        return "\n".join(results) if results else f"No matches found for '{pattern}'."

    @tool
    def glob_files(pattern: str) -> str:
        """
        List all files in the workspace that match a glob pattern.
        Examples: '**/*.py', '**/test_*.py', 'generated/*.txt'.
        Returns one relative file path per line.
        """
        base = Path(workspace_dir).resolve()
        try:
            matches = sorted(base.glob(pattern))
        except Exception as e:
            return f"Error: invalid glob pattern '{pattern}': {e}"

        if not matches:
            return f"No files matched the pattern '{pattern}'."

        lines = [str(p.relative_to(base)) for p in matches if p.is_file()]
        return "\n".join(lines) if lines else f"No files matched the pattern '{pattern}'."
            
    return [read_file, write_file, list_directory, grep_files, glob_files]


def make_tools(workspace_dir: str, sandbox=None) -> dict[str, BaseTool]:
    """
    Returns a **dict** of all workspace tools, keyed by name.

    Includes everything from get_basic_tools() plus:
      - run_python  (execute code through the sandbox)
      - run_command (run a shell command inside the workspace)

    Usage:
        tools = make_tools("workspace", sandbox)
        tools["grep_files"].invoke({"pattern": "def main"})
    """
    import subprocess as _sp

    # Start with the basic set
    basic = get_basic_tools(workspace_dir)
    tool_dict: dict[str, BaseTool] = {t.name: t for t in basic}

    # ── run_python ────────────────────────────────────────────────────────
    @tool
    def run_python(code: str) -> str:
        """
        Execute Python code in a sandboxed subprocess and return the output.
        The code runs in an isolated temporary directory with a 10-second timeout.
        Returns stdout on success, or the error traceback on failure.
        """
        if sandbox is None:
            return "Error: No sandbox configured."

        result = sandbox.run_python(code, timeout=10)
        if result.ok:
            return result.stdout or "(no output)"
        else:
            return f"EXECUTION FAILED\n{result.stderr}"

    tool_dict["run_python"] = run_python

    # ── run_command ───────────────────────────────────────────────────────
    @tool
    def run_command(command: List[str], cwd: str = ".") -> str:
        """
        Run a shell command inside the workspace and return combined stdout+stderr.
        *command* is a list of strings, e.g. ["python", "-c", "print('hi')"].
        *cwd* is relative to the workspace root.
        Timeout: 30 seconds.  The command cannot escape the workspace.
        """
        resolved = _resolve_path(workspace_dir, cwd)
        if isinstance(resolved, str):
            return resolved  # Error message

        try:
            proc = _sp.run(
                command,
                cwd=str(resolved),
                capture_output=True,
                text=True,
                timeout=30,
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            parts = []
            if out:
                parts.append(out)
            if err:
                parts.append(f"STDERR:\n{err}")
            if proc.returncode != 0:
                parts.append(f"(exit code {proc.returncode})")
            return "\n".join(parts) or "(no output)"
        except _sp.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error running command: {e}"

    tool_dict["run_command"] = run_command

    return tool_dict
