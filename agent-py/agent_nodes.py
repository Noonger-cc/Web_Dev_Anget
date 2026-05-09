"""LangGraph Agent node implementations — LLM-powered reasoning + tool execution."""

import json
import logging
import os
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# LLM configuration — set via env vars, defaults to DeepSeek
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

SYSTEM_PROMPT = """You are an intelligent operations (运维) AI assistant. Your capabilities:

1. **Diagnose problems**: Analyze monitoring data, logs, and system state to find root causes.
2. **Execute fixes**: Use SSH, IPMI, and other tools to resolve issues.
3. **Plan tasks**: Break complex requests into actionable steps.
4. **Learn from history**: Reference past cases from the knowledge base.

Available tools:
- ssh_exec(host, cmd): Execute command on one host via SSH
- ssh_batch_exec(hosts, cmd): Execute command on multiple hosts in parallel
- check_monitor(host): Query CPU/memory/disk/network metrics for a host
- query_logs(host, service, lines, filter_keyword): Query recent logs
- query_deploy_history(host, hours): Check recent deployments/changes
- query_knowledge_base(symptom, host): Search historical fault cases
- save_to_knowledge(symptoms, diagnosis, root_cause, solution, hosts, tags): Save resolved case
- ipmi_power(host, action): IPMI power control (status/on/off/reset/cycle)
- ipmi_bootdev(host, device): Set boot device (pxe/cdrom/bios/disk)
- ipmi_reset_password(host): Reset BMC password
- ipmi_sensor(host): Read IPMI sensor data
- ipmi_sel(host): Read IPMI System Event Log

Rules:
1. When diagnosing, check monitor data first, then logs, then deploy history.
2. Before executing dangerous operations (shutdown, reboot, reinstall, password reset, rm),
   clearly explain the risk and ask for confirmation.
3. When you have enough information to diagnose, summarize findings and suggest next steps.
4. After resolving an issue, save the case to the knowledge base.
5. Use ssh_batch_exec for multi-host operations instead of looping ssh_exec.
6. Respond in Chinese when the user writes in Chinese."""


def _make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=LLM_TEMPERATURE,
    )


def _make_llm_with_tools() -> ChatOpenAI:
    llm = _make_llm()
    # Bind tools as OpenAI-compatible function calls
    tools_schema = []
    for t in ALL_TOOLS:
        tools_schema.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.args_schema.schema() if hasattr(t, "args_schema") else {},
            },
        })
    return llm.bind_tools(tools_schema)


# Shared ToolNode instance
tool_node = ToolNode(ALL_TOOLS)


# ---------------------------------------------------------------------------
# Node functions — each receives state dict, returns updated state dict
# ---------------------------------------------------------------------------

async def understand_node(state: dict) -> dict:
    """Parse user intent and extract structured information."""
    user_input = state.get("user_input", "")
    if not user_input:
        state["intent"] = {"intent": "unknown", "target": "", "description": ""}
        return state

    llm = _make_llm()
    prompt = f"""Analyze the following user request and extract intent as JSON.
Return ONLY valid JSON with these fields:
  intent: one of [diagnose, execute, query, deploy, repair, batch_check, general]
  target: specific host(s) or system(s) mentioned
  description: one-line summary of what the user wants
  urgency: high/medium/low

User request: "{user_input}\""""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    try:
        intent = json.loads(response.content)
    except json.JSONDecodeError:
        intent = {"intent": "general", "target": "", "description": user_input, "urgency": "medium"}

    state["intent"] = intent
    state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]
    logger.info("Intent parsed: %s", intent)
    return state


async def plan_node(state: dict) -> dict:
    """LLM creates an execution plan based on the intent."""
    intent = state.get("intent", {})
    knowledge = state.get("knowledge_context", [])

    llm = _make_llm()
    context = f"Intent: {json.dumps(intent, ensure_ascii=False)}\n"
    if knowledge:
        context += f"Related historical cases: {json.dumps(knowledge, ensure_ascii=False)}\n"
    context += "\nCreate a step-by-step plan. Each step must specify which tool to call and why."

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context + "\n\nOutput the plan as a numbered list of steps."),
    ])

    state["plan"] = response.content
    state.setdefault("messages", []).append(AIMessage(content=f"📋 执行计划:\n{response.content}"))
    logger.info("Plan created: %s", response.content[:200])
    return state


async def agent_node(state: dict) -> dict:
    """LLM decides next action: call a tool or finish."""
    llm = _make_llm_with_tools()
    messages = state.get("messages", [])

    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = await llm.ainvoke(messages)
    state["messages"] = messages + [response]

    # Check if LLM wants to call a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        state["pending_tool_calls"] = response.tool_calls
        logger.info("Agent wants to call tools: %s", [tc["name"] for tc in response.tool_calls])
    else:
        state["pending_tool_calls"] = []
        logger.info("Agent finished reasoning, no more tool calls")

    return state


async def tool_call_node(state: dict) -> dict:
    """Execute pending tool calls via LangGraph ToolNode."""
    return await tool_node.ainvoke(state)


async def observe_node(state: dict) -> dict:
    """LLM reflects on tool results and updates its understanding."""
    llm = _make_llm()
    messages = state.get("messages", [])

    observation_prompt = (
        "Review the tool execution results above. "
        "What did we learn? Is the problem solved or do we need more investigation? "
        "If more tools are needed, explain what to check next."
    )
    messages.append(HumanMessage(content=observation_prompt))

    response = await llm.ainvoke(messages)
    state["messages"] = messages + [response]
    state.setdefault("observations", []).append(response.content)
    logger.info("Observation: %s", response.content[:200])
    return state


async def human_approve_node(state: dict) -> dict:
    """Check if the last tool call requires human approval, set flag if so."""
    HIGH_RISK_KEYWORDS = [
        "reboot", "shutdown", "reinstall", "reset_password",
        "rm -rf", "rm -r", "fdisk", "mkfs", "dd if",
        "systemctl stop", "docker rm", "kubectl delete",
        "iptables -F", "power_off", "power_reset",
    ]

    last_msg = ""
    for m in reversed(state.get("messages", [])):
        if isinstance(m, AIMessage) and hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                last_msg += json.dumps(tc, default=str).lower()
        elif hasattr(m, "content"):
            last_msg += str(m.content).lower()

    risk_found = any(kw.lower() in last_msg for kw in HIGH_RISK_KEYWORDS)
    state["require_approval"] = risk_found

    if risk_found:
        warning = ("⚠️ 此操作涉及高危动作，已暂停等待人工确认。请在前端点击 [确认执行] 或 [取消操作]。")
        state.setdefault("messages", []).append(AIMessage(content=warning))
        logger.warning("High-risk action detected, waiting for human approval")

    return state


async def summarize_node(state: dict) -> dict:
    """LLM generates a comprehensive final report."""
    llm = _make_llm()
    messages = state.get("messages", [])
    intent = state.get("intent", {})

    prompt = (
        "Based on the entire conversation above, generate a clear summary report "
        "for the user. Include:\n"
        "1. What was the original request\n"
        "2. What steps were taken\n"
        "3. What was found (root cause if diagnosing)\n"
        "4. What was done to fix it (if applicable)\n"
        "5. Recommendations or next steps\n\n"
        "Format the response in clean Markdown. Use Chinese."
    )

    response = await llm.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + messages + [HumanMessage(content=prompt)]
    )

    state["final_answer"] = response.content
    logger.info("Summary generated (len=%d)", len(response.content))
    return state


async def save_knowledge_node(state: dict) -> dict:
    """Extract case learnings and save to knowledge base."""
    llm = _make_llm()
    messages = state.get("messages", [])

    prompt = (
        "Based on the troubleshooting session above, extract key learnings as JSON:\n"
        '{"symptoms": "brief description", "diagnosis": "what was found", '
        '"root_cause": "the root cause", "solution": "how it was fixed", '
        '"hosts": "affected hosts", "tags": "comma-separated keywords"}\n\n'
        "If no clear diagnosis was reached, return: "
        '{"skip": true, "reason": "no diagnosis made"}\n\n'
        "Return ONLY valid JSON, no other text."
    )

    response = await llm.ainvoke(messages[-20:] + [HumanMessage(content=prompt)])
    try:
        case = json.loads(response.content)
        if case.get("skip"):
            logger.info("Knowledge save skipped: %s", case.get("reason"))
            return state

        from tools.knowledge_tools import save_to_knowledge
        result = save_to_knowledge(
            case.get("symptoms", ""),
            case.get("diagnosis", ""),
            case.get("root_cause", ""),
            case.get("solution", ""),
            case.get("hosts", ""),
            case.get("tags", ""),
        )
        logger.info("Knowledge case saved: %s", result)
        state.setdefault("messages", []).append(
            AIMessage(content=f"📚 知识库已更新: {json.loads(result).get('message', '')}")
        )
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Failed to extract knowledge: %s", exc)

    return state


def should_continue(state: dict) -> str:
    """Conditional edge: continue tool loop or go to summarize."""
    if state.get("require_approval"):
        return "human_approve"
    if state.get("pending_tool_calls"):
        return "tool_call"
    # If last message is from AI and has no tool calls, we're done
    last = state.get("messages", [])[-1] if state.get("messages") else None
    if isinstance(last, AIMessage):
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tool_call"
    # No more actions → summarize
    return "summarize"


def should_continue_after_tool(state: dict) -> str:
    """After tool execution, decide: observe → agent again, or summarize."""
    state["pending_tool_calls"] = []
    # Go back to agent to let LLM decide next step
    return "agent"


def should_approve(state: dict) -> str:
    """After human_approve check, route accordingly."""
    if state.get("require_approval"):
        return "wait_approval"
    return "continue"
