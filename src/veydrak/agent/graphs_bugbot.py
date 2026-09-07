from typing import Optional
from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from veydrak.schemas.schemas import CodeOutput

class AgentState(TypedDict):
    task: str
    attempts: int
    max_attempts: int
    code: Optional[str]
    explanation: Optional[str]
    error: Optional[str]
    execution_result: Optional[str]
    status: str

def build_bugbot(llm: BaseChatModel, sandbox):
    """
    Builds the self-correcting Bugbot graph.
    """
    # Bind LLM to structured CodeOutput schema
    structured_llm = llm.with_structured_output(CodeOutput)
    
    def _generate_prompt(state: AgentState) -> str:
        prompt = f"Write a Python script to accomplish this task:\n{state['task']}\n\n"
        if state.get("error"):
            prompt += f"Your previous attempt failed with this error:\n```\n{state['error']}\n```\n"
            prompt += "Please fix the code and try again."
        return prompt

    def generate_node(state: AgentState):
        prompt = _generate_prompt(state)
        # Using structured output to guarantee we get back code and explanation
        response = structured_llm.invoke(prompt)
        
        return {
            "code": response.code,
            "explanation": response.explanation,
        }

    def execute_node(state: AgentState):
        code = state["code"]
        attempts = state.get("attempts", 0) + 1
        
        result = sandbox.run_python(code, timeout=3)
        
        if result.ok:
            return {
                "attempts": attempts,
                "execution_result": result.stdout,
                "error": None,
                "status": "success"
            }
        else:
            return {
                "attempts": attempts,
                "execution_result": result.stdout,
                "error": result.stderr,
                "status": "failed"
            }
            
    def should_continue(state: AgentState):
        if state.get("status") == "success":
            return END
        if state.get("attempts", 0) >= state.get("max_attempts", 3):
            return END
        return "generate"

    workflow = StateGraph(AgentState)
    workflow.add_node("generate", generate_node)
    workflow.add_node("execute", execute_node)
    
    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "execute")
    workflow.add_conditional_edges("execute", should_continue, ["generate", END])
    
    return workflow.compile()
