from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import subprocess
import time
import paramiko
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="LangGraph Ops Agent")

# LangGraph 状态定义
class TaskState:
    def __init__(self):
        self.task_id: int = 0
        self.exec_type: str = ""
        self.command: str = ""
        self.host_ids: Optional[List[int]] = None
        self.client_ids: Optional[List[int]] = None
        self.host_info: Optional[Dict[str, Any]] = None
        self.logs: List[str] = []
        self.result: str = ""
        self.status: str = "pending"

class ExecuteRequest(BaseModel):
    task_id: int
    exec_type: str
    command: str
    host_ids: Optional[List[int]] = None
    client_ids: Optional[List[int]] = None
    host_info: Optional[Dict[str, Any]] = None

class ExecuteResponse(BaseModel):
    task_id: int
    status: str
    result: str
    logs: List[str]

class SshExecuteRequest(BaseModel):
    host: str
    port: int
    username: str
    auth_type: str
    credential: str
    command: str

# LangGraph 节点函数
def parse_task(state: TaskState) -> TaskState:
    """解析任务参数"""
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 开始解析任务 {state.task_id}")
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 执行类型: {state.exec_type}")
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 命令: {state.command}")
    state.status = "parsing"
    return state

def execute_ssh(state: TaskState) -> TaskState:
    """SSH 执行任务"""
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 开始SSH执行")
    try:
        if not state.host_info:
            raise Exception("缺少主机信息")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = state.host_info.get("host")
        port = state.host_info.get("port", 22)
        username = state.host_info.get("username")
        auth_type = state.host_info.get("auth_type")
        credential = state.host_info.get("credential")

        if auth_type == "password":
            ssh.connect(host, port=port, username=username, password=credential, timeout=10)
        else:
            # 密钥认证
            key = paramiko.RSAKey.from_private_key_file(credential)
            ssh.connect(host, port=port, username=username, pkey=key, timeout=10)

        stdin, stdout, stderr = ssh.exec_command(state.command, timeout=30)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            state.logs.append(f"[{time.strftime('%H:%M:%S')}] SSH输出: {output}")
        if error:
            state.logs.append(f"[{time.strftime('%H:%M:%S')}] SSH错误: {error}")

        state.result = output if output else "SSH执行完成"
        if error:
            state.result += f"\n错误: {error}"

        state.status = "success"
        ssh.close()

    except Exception as e:
        state.logs.append(f"[{time.strftime('%H:%M:%S')}] SSH执行错误: {str(e)}")
        state.result = f"SSH执行失败: {str(e)}"
        state.status = "failed"

    return state

def execute_local(state: TaskState) -> TaskState:
    """本地执行任务"""
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 开始本地执行")
    try:
        result = subprocess.run(
            state.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            state.logs.append(f"[{time.strftime('%H:%M:%S')}] 输出: {stdout}")
        if stderr:
            state.logs.append(f"[{time.strftime('%H:%M:%S')}] 错误: {stderr}")

        state.result = stdout if stdout else "命令执行完成"
        if stderr:
            state.result += f"\n错误: {stderr}"

        state.status = "success"

    except subprocess.TimeoutExpired:
        state.logs.append(f"[{time.strftime('%H:%M:%S')}] 执行超时")
        state.result = "执行超时"
        state.status = "failed"
    except Exception as e:
        state.logs.append(f"[{time.strftime('%H:%M:%S')}] 执行错误: {str(e)}")
        state.result = str(e)
        state.status = "failed"

    return state

def collect_result(state: TaskState) -> TaskState:
    """收集执行结果"""
    state.logs.append(f"[{time.strftime('%H:%M:%S')}] 任务执行完成，状态: {state.status}")
    return state

# 路由函数
def should_execute_ssh(state: TaskState) -> str:
    """决定是否使用SSH执行"""
    return "ssh" if state.exec_type == "ssh" and state.host_info else "local"

def should_execute_client(state: TaskState) -> str:
    """决定是否使用客户端执行"""
    return "client" if state.exec_type == "client" and state.client_ids else "local"

# 创建工作流图
workflow = StateGraph(TaskState)

# 添加节点
workflow.add_node("parse_task", parse_task)
workflow.add_node("execute_ssh", execute_ssh)
workflow.add_node("execute_local", execute_local)
workflow.add_node("collect_result", collect_result)

# 设置入口
workflow.set_entry_point("parse_task")

# 添加边
workflow.add_conditional_edges(
    "parse_task",
    should_execute_ssh,
    {
        "ssh": "execute_ssh",
        "local": "execute_local"
    }
)

workflow.add_edge("execute_ssh", "collect_result")
workflow.add_edge("execute_local", "collect_result")
workflow.add_edge("collect_result", END)

# 编译图
app_graph = workflow.compile()

@app.post("/execute", response_model=ExecuteResponse)
async def execute_task(req: ExecuteRequest):
    # 初始化状态
    initial_state = TaskState()
    initial_state.task_id = req.task_id
    initial_state.exec_type = req.exec_type
    initial_state.command = req.command
    initial_state.host_ids = req.host_ids
    initial_state.client_ids = req.client_ids
    initial_state.host_info = req.host_info

    # 运行工作流
    try:
        final_state = app_graph.invoke(initial_state)

        return ExecuteResponse(
            task_id=final_state.task_id,
            status=final_state.status,
            result=final_state.result,
            logs=final_state.logs
        )
    except Exception as e:
        return ExecuteResponse(
            task_id=req.task_id,
            status="failed",
            result=f"工作流执行错误: {str(e)}",
            logs=[f"[{time.strftime('%H:%M:%S')}] 工作流错误: {str(e)}"]
        )

@app.post("/ssh-execute")
async def ssh_execute(req: SshExecuteRequest):
    # 直接SSH执行，不使用工作流
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if req.auth_type == "password":
            ssh.connect(req.host, port=req.port, username=req.username, password=req.credential, timeout=10)
        else:
            key = paramiko.RSAKey.from_private_key_file(req.credential)
            ssh.connect(req.host, port=req.port, username=req.username, pkey=key, timeout=10)

        stdin, stdout, stderr = ssh.exec_command(req.command, timeout=30)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        ssh.close()

        result = output if output else "SSH执行完成"
        if error:
            result += f"\n错误: {error}"

        return {"success": True, "output": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
                from io import StringIO
                key = paramiko.RSAKey.from_private_key(StringIO(req.credential))
                ssh.connect(
                    req.host,
                    port=req.port,
                    username=req.username,
                    pkey=key,
                    timeout=10
                )
            
            stdin, stdout, stderr = ssh.exec_command(req.command, timeout=30)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            ssh.close()
            
            if error:
                return {"success": True, "output": f"{output}\n{error}"}
            return {"success": True, "output": output}
        except ImportError:
            return {"success": False, "message": "paramiko 未安装，请安装: pip install paramiko"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)