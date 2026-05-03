from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from langgraph_agent import create_ops_agent, ExecutionState

app = FastAPI(title="LangGraph Ops Agent")

ops_agent = create_ops_agent()

class ExecuteRequest(BaseModel):
    task_id: int
    exec_type: str
    command: str
    host_ids: Optional[List[int]] = None
    client_ids: Optional[List[int]] = None

class ExecuteResponse(BaseModel):
    task_id: int
    status: str
    result: str
    logs: List[str]

@app.post("/execute", response_model=ExecuteResponse)
async def execute_task(req: ExecuteRequest):
    try:
        initial_state = ExecutionState(
            task_id=req.task_id,
            exec_type=req.exec_type,
            command=req.command,
            host_ids=req.host_ids or [],
            client_ids=req.client_ids or [],
            logs=[],
            result=""
        )

        final_state = await ops_agent.ainvoke(initial_state)

        return ExecuteResponse(
            task_id=req.task_id,
            status=final_state.get("status", "unknown"),
            result=final_state.get("result", ""),
            logs=final_state.get("logs", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
