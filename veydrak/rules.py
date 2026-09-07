import os
from pathlib import Path
from dataclasses import dataclass
import fnmatch

@dataclass
class Rule:
    source: str
    always_apply: bool
    globs: str
    content: str

def parse_mdc(file_path: str) -> Rule:
    """Parses a Cursor .mdc file and extracts frontmatter globs and markdown content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    globs = "*"
    content_lines = []
    
    in_frontmatter = False
    frontmatter_processed = False
    
    for line in lines:
        if line.strip() == "---" and not frontmatter_processed:
            if not in_frontmatter:
                in_frontmatter = True
            else:
                in_frontmatter = False
                frontmatter_processed = True
            continue
            
        if in_frontmatter:
            if line.startswith("globs:"):
                # Extract glob pattern (e.g., globs: "*.py" -> *.py)
                globs = line.split(":", 1)[1].strip().strip('"').strip("'")
        else:
            content_lines.append(line)
            
    return Rule(
        source=os.path.basename(file_path),
        always_apply=False,
        globs=globs,
        content="".join(content_lines).strip()
    )

def list_rules(root_dir: str) -> list[Rule]:
    """Scans root_dir for AGENTS.md and .cursor/rules/*.mdc"""
    rules = []
    root = Path(root_dir)
    
    # 1. Check for AGENTS.md
    agents_md = root / "AGENTS.md"
    if agents_md.exists():
        with open(agents_md, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            rules.append(Rule(
                source="AGENTS.md",
                always_apply=True,
                globs="*",
                content=content
            ))
            
    # 2. Check for .cursor/rules/*.mdc
    rules_dir = root / ".cursor" / "rules"
    if rules_dir.exists() and rules_dir.is_dir():
        for mdc_file in rules_dir.glob("*.mdc"):
            rules.append(parse_mdc(str(mdc_file)))
            
    return rules

def load_rules(root_dir: str, target_file: str) -> str:
    """Compiles the System Prompt based on AGENTS.md and applicable .mdc rules."""
    rules = list_rules(root_dir)
    target_name = os.path.basename(target_file)
    
    system_prompt_parts = []
    
    for rule in rules:
        # Apply if always_apply is True, or if target_name matches the rule's glob
        if rule.always_apply or fnmatch.fnmatch(target_name, rule.globs):
            system_prompt_parts.append(f"--- Rule from {rule.source} ---")
            system_prompt_parts.append(rule.content)
            
    return "\n\n".join(system_prompt_parts)
