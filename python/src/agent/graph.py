"""LangGraph workflow for Agent."""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.core.llm import get_llm
from src.config import settings


class AgentState(TypedDict):
    """Agent state definition."""
    messages: list
    current_step: str
    iterations: int
    result: str
    needs_human: bool
    human_feedback: str


def create_agent_graph(tools: list = None):
    """
    Create an agent workflow graph.

    Args:
        tools: List of tools for the agent

    Returns:
        Compiled StateGraph
    """
    llm = get_llm()

    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm

    builder = StateGraph(AgentState)

    def should_continue(state: AgentState) -> str:
        """Determine if agent should continue or end."""
        if state.get("needs_human"):
            return "human"
        if state["iterations"] >= settings.max_iterations:
            return "end"
        return "continue"

    def call_model(state: AgentState):
        """Call the LLM with current messages."""
        response = llm_with_tools.invoke(state["messages"])
        return {
            "messages": [response],
            "current_step": "model_response",
            "iterations": state["iterations"] + 1,
        }

    def human_node(state: AgentState):
        """Handle human interaction."""
        return {"needs_human": False, "human_feedback": ""}

    builder.add_node("model", call_model)
    builder.add_node("human", human_node)

    builder.set_entry_point("model")

    builder.add_conditional_edges(
        "model",
        should_continue,
        {
            "continue": "model",
            "human": "human",
            "end": END,
        }
    )

    builder.add_edge("human", "model")

    return builder.compile()


class AgentGraph:
    """Agent graph manager."""

    def __init__(self, agent_id: str, name: str, tools: list = None):
        self.agent_id = agent_id
        self.name = name
        self.tools = tools or []
        self.graph = create_agent_graph(tools)
        self._initial_state = {
            "messages": [],
            "current_step": "init",
            "iterations": 0,
            "result": "",
            "needs_human": False,
            "human_feedback": "",
        }

    def run(self, input: str) -> dict:
        """Run the agent with input."""
        state = self._initial_state.copy()
        state["messages"] = [{"role": "user", "content": input}]

        result = self.graph.invoke(state)

        return {
            "status": "success",
            "result": result.get("result", ""),
            "iterations": result.get("iterations", 0),
            "messages": result.get("messages", []),
        }

    def get_state(self) -> dict:
        """Get current state."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": "running",
            "iterations": 0,
        }