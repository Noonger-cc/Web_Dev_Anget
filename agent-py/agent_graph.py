"""LangGraph Agent graph assembly — the thinking loop."""

import logging

from langgraph.graph import END, StateGraph

from agent_nodes import (
    agent_node,
    human_approve_node,
    observe_node,
    plan_node,
    save_knowledge_node,
    should_continue,
    should_continue_after_tool,
    summarize_node,
    tool_call_node,
    understand_node,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------
class AgentState(dict):
    """LangGraph agent state. Fields:
    - messages: List[BaseMessage] — full conversation history
    - user_input: str — the user's original request
    - intent: dict — parsed intent {intent, target, description, urgency}
    - plan: str — LLM-generated execution plan
    - pending_tool_calls: list — tool calls waiting to execute
    - observations: list — LLM observations after each tool execution
    - final_answer: str — final report from summarize node
    - require_approval: bool — whether human approval is needed
    - knowledge_context: list — relevant historical cases
    """
    pass


def create_agent_graph():
    """Build and compile the intelligent Agent StateGraph."""

    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("understand", understand_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool_call", tool_call_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("human_approve", human_approve_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("save_knowledge", save_knowledge_node)

    # Entry
    workflow.set_entry_point("understand")

    # Edges
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "agent")

    # Core loop: agent → tool_call → observe → agent → ...
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tool_call": "tool_call",
            "summarize": "summarize",
            "human_approve": "human_approve",
        },
    )

    workflow.add_conditional_edges(
        "tool_call",
        should_continue_after_tool,
        {
            "agent": "agent",
        },
    )

    workflow.add_edge("observe", "agent")
    workflow.add_edge("human_approve", "summarize")

    # Final chain
    workflow.add_edge("summarize", "save_knowledge")
    workflow.add_edge("save_knowledge", END)

    logger.info("Agent graph compiled successfully")
    return workflow.compile()


# Singleton
agent_graph = create_agent_graph()
