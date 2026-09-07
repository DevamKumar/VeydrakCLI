from typing import Optional
from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from veydrak.schemas import CodeOutput, ReviewResult
from veydrak.sandbox import LocalSandbox

class FullAgentState(TypedDict):
    task: str
    rules: str
    attempts: int
    max_attempts: int
    code: Optional[str]
    explanation: Optional[str]
    error: Optional[str]
    execution_result: Optional[str]
    review_feedback: Optional[str]
    status: str

def build_full_agent(llm: BaseChatModel, sandbox: LocalSandbox):
    structured_coder = llm.with_structured_output(CodeOutput)
    structured_reviewer = llm.with_structured_output(ReviewResult)
    
    def generate_node(state: FullAgentState):
        prompt = f"Task:\n{state['task']}\n\n"
        if state.get("rules"):
            prompt += f"Coding Rules:\n{state['rules']}\n\n"
            
        if state.get("status") == "failed" and state.get("error"):
            prompt += f"Your previous attempt failed execution with this error:\n```\n{state['error']}\n```\n"
            prompt += "Please fix the code and try again."
        elif state.get("status") == "rejected" and state.get("review_feedback"):
            prompt += f"Your previous code ran successfully, but was rejected by the reviewer with this feedback:\n```\n{state['review_feedback']}\n```\n"
            prompt += "Please improve the code and try again."
            
        response = structured_coder.invoke(prompt)
        return {
            "code": response.code,
            "explanation": response.explanation,
        }

    def execute_node(state: FullAgentState):
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
            
    def review_node(state: FullAgentState):
        prompt = "Review this Python code for quality (type hints, naming, PEP 8, efficiency, edge cases):\n\n"
        if state.get("rules"):
            prompt += f"Ensure it follows these rules:\n{state['rules']}\n\n"
        prompt += f"Code:\n```python\n{state['code']}\n```\n"
        
        review = structured_reviewer.invoke(prompt)
        
        return {
            "status": "approved" if review.approved else "rejected",
            "review_feedback": review.feedback
        }

    def should_review(state: FullAgentState):
        if state.get("status") == "success":
            return "review"
        if state.get("attempts", 0) >= state.get("max_attempts", 3):
            return END
        return "generate"
        
    def should_finish(state: FullAgentState):
        if state.get("status") == "approved":
            return END
        if state.get("attempts", 0) >= state.get("max_attempts", 3):
            return END
        return "generate"

    workflow = StateGraph(FullAgentState)
    workflow.add_node("generate", generate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("review", review_node)
    
    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "execute")
    workflow.add_conditional_edges("execute", should_review, ["review", "generate", END])
    workflow.add_conditional_edges("review", should_finish, ["generate", END])
    
    return workflow.compile()
