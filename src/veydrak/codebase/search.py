"""
veydrak/search.py — Codebase exploration utilities.

Provides two functions:
  - repo_map: returns a tree-style string of all .py files in a directory.
  - search_codebase: scores files by query-term frequency and returns ranked paths.

These replicate what Cursor, Claude Code, and Codex do before planning edits:
grep for relevant terms, read the top hits, repeat if needed.  No index required.
"""

import os
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# repo_map
# ---------------------------------------------------------------------------

def repo_map(root_dir: str, extensions: tuple[str, ...] = (".py",)) -> str:
    """
    Walk *root_dir* and return a compact, human-readable map of every file
    whose extension is in *extensions*.

    Output format (one file per line, indented by depth):
        veydrak/
          __init__.py
          llm.py
          search.py
          ...
    """
    root = Path(root_dir).resolve()
    lines: list[str] = []

    # Directories to skip entirely
    SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".cursor"}

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune unwanted dirs in-place so os.walk doesn't descend into them
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)

        current = Path(dirpath)
        depth = len(current.relative_to(root).parts)
        indent = "  " * depth

        # Print directory header (only for subdirectories, not the root itself)
        if depth > 0:
            lines.append(f"{indent[:-2]}{current.name}/")

        for fname in sorted(filenames):
            if any(fname.endswith(ext) for ext in extensions):
                lines.append(f"{indent}{fname}")

    if not lines:
        return f"(no {'/'.join(extensions)} files found in {root_dir})"

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# search_codebase
# ---------------------------------------------------------------------------

def search_codebase(
    root_dir: str,
    query: str,
    top_n: int = 5,
    extensions: tuple[str, ...] = (".py",),
) -> list[str]:
    """
    A grep-based semantic search over *root_dir*.

    Algorithm:
      1. Tokenise *query* into lowercase words (strip punctuation).
      2. Walk every file with a matching extension.
      3. Count how many query tokens appear in the file (case-insensitive).
      4. Rank files by hit count (descending); return the top *top_n* paths.

    Returns a list of absolute path strings, best match first.
    """
    root = Path(root_dir).resolve()
    tokens = set(re.findall(r"[a-z0-9_]+", query.lower()))
    if not tokens:
        return []

    SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".cursor"}
    scores: dict[Path, int] = defaultdict(int)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if not any(fname.endswith(ext) for ext in extensions):
                continue

            fpath = Path(dirpath) / fname
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue

            hit = sum(1 for tok in tokens if tok in text)
            if hit > 0:
                scores[fpath] = hit

    ranked = sorted(scores, key=lambda p: scores[p], reverse=True)
    return [str(p) for p in ranked[:top_n]]
