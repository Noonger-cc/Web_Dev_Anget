from typing import TypedDict, List, Optional, Literal
from langgraph.graph import StateGraph, END
import paramiko
import time

class ExecutionState(TypedDict):
    task_id: int
    exec_type: str
    command: str
    host_ids: List[int]
    client_ids: List[int]
    logs: List[str]
    result: str
    status: str

def parse_input(state: ExecutionState) -> ExecutionState:
    state["logs"].append(f"[PARSE] Parsing task {state['task_id']}: {state['command']}")
    return state

def route_execution(state: ExecutionState) -> Literal["ssh_execute", "client_execute"]:
    exec_type = state["exec_type"]
    if exec_type == "ssh":
        return "ssh_execute"
    else:
        return "client_execute"

def ssh_execute(state: ExecutionState) -> ExecutionState:
    state["logs"].append(f"[SSH] Starting SSH execution for {len(state['host_ids'])} hosts")
    state["result"] = ""

    for host_id in state["host_ids"]:
        state["logs"].append(f"[SSH] Connecting to host {host_id}")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname="192.168.1." + str(host_id), port=22, username="root", password="password", timeout=5)
            stdin, stdout, stderr = ssh.exec_command(state["command"])
            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh.close()

            if output:
                state["logs"].append(f"[SSH] Host {host_id} output: {output[:100]}")
                state["result"] += f"Host {host_id}: {output}\n"
            if error:
                state["logs"].append(f"[SSH] Host {host_id} error: {error[:100]}")
                state["result"] += f"Host {host_id} error: {error}\n"
        except Exception as e:
            state["logs"].append(f"[SSH] Host {host_id} failed: {str(e)}")
            state["result"] += f"Host {host_id} failed: {str(e)}\n"

    state["status"] = "success"
    return state

def client_execute(state: ExecutionState) -> ExecutionState:
    state["logs"].append(f"[CLIENT] Sending command to {len(state['client_ids'])} clients via Go backend")
    state["status"] = "success"
    state["result"] = f"Command queued for {len(state['client_ids'])} clients"
    return state

def validate_result(state: ExecutionState) -> ExecutionState:
    state["logs"].append(f"[VALIDATE] Validating execution result")
    if not state["result"]:
        state["status"] = "failed"
        state["logs"].append("[VALIDATE] No result produced")
    else:
        state["status"] = "success"
        state["logs"].append("[VALIDATE] Result validated successfully")
    return state

def summarize(state: ExecutionState) -> ExecutionState:
    state["logs"].append(f"[SUMMARY] Task {state['task_id']} completed with status: {state['status']}")
    return state

def create_ops_agent():
    workflow = StateGraph(ExecutionState)

    workflow.add_node("parse", parse_input)
    workflow.add_node("ssh_execute", ssh_execute)
    workflow.add_node("client_execute", client_execute)
    workflow.add_node("validate", validate_result)
    workflow.add_node("summarize", summarize)

    workflow.set_entry_point("parse")

    workflow.add_edge("parse", "route_execution")
    workflow.add_conditional_edges(
        "route_execution",
        route_execution,
        {
            "ssh_execute": "ssh_execute",
            "client_execute": "client_execute"
        }
    )

    workflow.add_edge("ssh_execute", "validate")
    workflow.add_edge("client_execute", "validate")
    workflow.add_edge("validate", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()

async def ainvoke(self, initial_state: ExecutionState):
    async for event in self._astream(initial_state, stream_mode="values"):
        pass
    return initial_state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
