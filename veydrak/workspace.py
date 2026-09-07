"""
veydrak/workspace.py — Managed workspace wrapper.

Provides file I/O, snapshot (copy to temp dir), and change application
for the orchestrator graph.
"""

import os
import shutil
import tempfile
from pathlib import Path


class Workspace:
    """A managed wrapper around a workspace directory."""

    def __init__(self, root_dir: str):
        self.root = str(Path(root_dir).resolve())

    # ── File operations ───────────────────────────────────────────────────

    def read_file(self, rel_path: str) -> str:
        """Read a file relative to the workspace root."""
        return (Path(self.root) / rel_path).read_text(encoding="utf-8")

    def write_file(self, rel_path: str, content: str) -> None:
        """Write content to a file, creating parent dirs if needed."""
        target = Path(self.root) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def list_files(self, extensions: tuple[str, ...] = (".py",)) -> list[str]:
        """
        Return a list of relative paths of files in the workspace
        whose extension is in *extensions*.  Skips hidden dirs and venv.
        """
        SKIP = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".cursor"}
        result: list[str] = []
        root = Path(self.root)

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP]
            for fname in sorted(filenames):
                if any(fname.endswith(ext) for ext in extensions):
                    rel = str(Path(dirpath, fname).relative_to(root))
                    result.append(rel)
        return result

    # ── Snapshot & apply ──────────────────────────────────────────────────

    def snapshot(self) -> str:
        """
        Copy the entire workspace to a temporary directory.
        Returns the path to the copy.  Caller is responsible for cleanup.
        """
        tmp = tempfile.mkdtemp(prefix="veydrak_snap_")
        dest = os.path.join(tmp, "workspace")
        shutil.copytree(self.root, dest, dirs_exist_ok=True)
        return dest

    def apply_changes(self, changes: list[dict]) -> None:
        """
        Write a list of ``{filepath, code, ...}`` dicts to the workspace.
        Each dict must have at least ``filepath`` and ``code`` keys.
        """
        for change in changes:
            self.write_file(change["filepath"], change["code"])

    def __repr__(self) -> str:
        return f"Workspace({self.root!r})"
