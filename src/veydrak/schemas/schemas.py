from pydantic import BaseModel, Field

class CodeOutput(BaseModel):
    """Schema for returning code with explanations."""
    code: str = Field(description="The generated code.")
    explanation: str = Field(description="Explanation of how the code works.")
    imports: list[str] = Field(description="List of necessary import statements.", default_factory=list)

class ReviewResult(BaseModel):
    """Schema for reviewing code quality."""
    approved: bool = Field(description="True if the code meets quality standards, False otherwise.")
    feedback: str = Field(description="Constructive feedback if rejected, or praise if approved.")


class FileTask(BaseModel):
    """A single file-level task inside a Plan."""
    action: str = Field(description="Either 'create' for a new file or 'modify' for an existing file.")
    filepath: str = Field(description="Path to the file, relative to the workspace root.")
    description: str = Field(description="What to do in this file — clear enough for a coder agent to execute.")


class Plan(BaseModel):
    """A structured plan produced by the planner before any code is written."""
    summary: str = Field(description="One-sentence summary of the overall change.")
    file_tasks: list[FileTask] = Field(description="Ordered list of file-level tasks to implement the change.")
