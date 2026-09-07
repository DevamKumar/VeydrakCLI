from typing import List, Callable, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

def build_tool_agent(llm: BaseChatModel, tools: List[BaseTool], system_prompt: Optional[str] = None):
    """
    Builds a LangGraph state machine that can invoke tools and accept a system prompt.
    """
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: MessagesState):
        messages = state["messages"]
        # If a system prompt is provided, prepend it to the messages
        if system_prompt:
            # We construct a new list to avoid mutating the original state list directly
            messages = [SystemMessage(content=system_prompt)] + messages
            
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
        
    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
