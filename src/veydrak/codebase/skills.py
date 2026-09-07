import os
import yaml
from dataclasses import dataclass
from langchain_core.tools import tool

@dataclass
class Skill:
    name: str
    description: str
    content: str

def load_skills(root_dir: str) -> dict[str, Skill]:
    """Scans .cursor/skills/<name>/SKILL.md files and parses them."""
    skills = {}
    skills_dir = os.path.join(root_dir, ".cursor", "skills")
    
    if not os.path.exists(skills_dir):
        return skills
        
    for skill_name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
        if os.path.isfile(skill_path):
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Naive YAML frontmatter parsing
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        name = frontmatter.get("name", skill_name)
                        description = frontmatter.get("description", "No description provided.")
                        body = parts[2].strip()
                        skills[name] = Skill(name=name, description=description, content=body)
                    except Exception as e:
                        print(f"Failed to parse skill frontmatter in {skill_path}: {e}")
    return skills

def skills_catalog(skills: dict[str, Skill]) -> str:
    """Generates a catalog string to be injected into the system prompt."""
    if not skills:
        return ""
        
    catalog = "Available Skills:\n"
    for name, skill in skills.items():
        catalog += f"- {name}: {skill.description}\n"
        
    catalog += "\nTo read the full steps of a skill, use the `read_skill` tool."
    return catalog

def make_read_skill_tool(skills: dict[str, Skill]):
    """Returns a LangChain tool bound to the available skills dict."""
    
    @tool
    def read_skill(skill_name: str) -> str:
        """Reads the full content of a specified skill by its name."""
        skill = skills.get(skill_name)
        if skill:
            return skill.content
        return f"Error: Skill '{skill_name}' not found."
        
    return read_skill
