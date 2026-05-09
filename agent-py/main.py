"""FastAPI entry point for the LangGraph Ops Agent — with SSE streaming."""

import asyncio
import json
import logging
import time
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_graph import agent_graph, AgentState

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agent-api")

app = FastAPI(title="LangGraph Ops Agent API", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class AgentRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    thread_id: Optional[str] = None
    llm_config: Optional[dict] = None  # {api_key, base_url, model}


class SshExecuteRequest(BaseModel):
    host: str
    port: int = 22
    username: str
    auth_type: str = "password"
    credential: str
    command: str

# ---------------------------------------------------------------------------
# SSE Helper
# ---------------------------------------------------------------------------
def sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0"}


@app.post("/agent/chat")
async def agent_chat(req: AgentRequest):
    """
    SSE streaming endpoint for AI agent interaction.

    Streams events:
      - intent: parsed user intent
      - plan: execution plan
      - tool_start: tool name being called
      - tool_end: tool result
      - thinking: agent's reasoning
      - message: intermediate message
      - done: final report
    """
    thread_id = req.thread_id or f"thread-{int(time.time())}"

    async def event_stream():
        try:
            initial_state = AgentState(
                messages=[],
                user_input=req.message,
                intent={},
                plan="",
                pending_tool_calls=[],
                observations=[],
                final_answer="",
                require_approval=False,
                knowledge_context=[],
                llm_config=req.llm_config or {},
            )

            config = {"configurable": {"thread_id": thread_id}}

            # Stream events from the compiled graph
            async for event in agent_graph.astream_events(initial_state, config, version="v2"):
                kind = event.get("event", "")

                if kind == "on_chat_model_start":
                    yield sse_event("thinking", {"content": "正在思考..."})

                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        yield sse_event("thinking", {"content": chunk.content})

                elif kind == "on_tool_start":
                    name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield sse_event("tool_start", {
                        "tool": name,
                        "input": tool_input,
                    })

                elif kind == "on_tool_end":
                    name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", "")
                    clean = str(output)[:2000] if output else ""
                    yield sse_event("tool_end", {
                        "tool": name,
                        "output": clean,
                    })

                elif kind == "on_chain_end":
                    # Check if it's the final node
                    output = event.get("data", {}).get("output", {})

                    if isinstance(output, dict) and output.get("final_answer"):
                        yield sse_event("done", {
                            "report": output["final_answer"],
                            "intent": output.get("intent", {}),
                        })
                    elif isinstance(output, dict) and "messages" in output:
                        msgs = output.get("messages", [])
                        last_text = ""
                        for m in reversed(msgs):
                            if hasattr(m, "content") and m.content and not hasattr(m, "tool_calls"):
                                last_text = str(m.content)[:500]
                                break
                        if last_text:
                            yield sse_event("message", {"content": last_text})

        except Exception as exc:
            logger.exception("Agent stream error")
            yield sse_event("error", {"message": str(exc)})

        yield sse_event("stream_end", {"thread_id": thread_id})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/agent/chat-simple")
async def agent_chat_simple(req: AgentRequest):
    """Non-streaming version — returns the final answer directly."""
    try:
        initial_state = AgentState(
            messages=[],
            user_input=req.message,
            intent={},
            plan="",
            pending_tool_calls=[],
            observations=[],
            final_answer="",
            require_approval=False,
            knowledge_context=[],
            llm_config=req.llm_config or {},
        )

        result = await agent_graph.ainvoke(initial_state)

        return {
            "success": True,
            "answer": result.get("final_answer", ""),
            "intent": result.get("intent", {}),
            "thread_id": req.thread_id,
        }
    except Exception as exc:
        logger.exception("Agent simple chat error")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ssh-execute")
async def ssh_execute_endpoint(req: SshExecuteRequest):
    """Direct SSH execution — bypasses agent reasoning."""
    try:
        from tools.ssh_tools import ssh_exec
        result_str = await asyncio.to_thread(ssh_exec, req.host, req.command)
        result = json.loads(result_str)
        if result.get("success"):
            return {"success": True, "output": result.get("stdout", "") + ("\n" + result.get("stderr", "") if result.get("stderr") else "")}
        return {"success": False, "message": result.get("error", "Unknown error")}
    except Exception as exc:
        logger.exception("Direct SSH error")
        raise HTTPException(status_code=500, detail=str(exc))

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
