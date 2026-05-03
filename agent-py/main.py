from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import subprocess
import time

app = FastAPI(title="LangGraph Ops Agent")

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

class SshExecuteRequest(BaseModel):
    host: str
    port: int
    username: str
    auth_type: str
    credential: str
    command: str

@app.post("/execute", response_model=ExecuteResponse)
async def execute_task(req: ExecuteRequest):
    logs = [f"[{time.strftime('%H:%M:%S')}] 开始执行任务 {req.task_id}"]
    logs.append(f"[{time.strftime('%H:%M:%S')}] 执行类型: {req.exec_type}")
    logs.append(f"[{time.strftime('%H:%M:%S')}] 命令: {req.command}")
    
    try:
        result = subprocess.run(
            req.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if stdout:
            logs.append(f"[{time.strftime('%H:%M:%S')}] 输出: {stdout}")
        if stderr:
            logs.append(f"[{time.strftime('%H:%M:%S')}] 警告: {stderr}")
        
        logs.append(f"[{time.strftime('%H:%M:%S')}] 执行完成")
        
        final_result = stdout if stdout else "命令执行完成"
        if stderr:
            final_result = f"{final_result}\n错误: {stderr}"
        
        return ExecuteResponse(
            task_id=req.task_id,
            status="success",
            result=final_result,
            logs=logs
        )
    except subprocess.TimeoutExpired:
        logs.append(f"[{time.strftime('%H:%M:%S')}] 执行超时")
        return ExecuteResponse(
            task_id=req.task_id,
            status="failed",
            result="执行超时",
            logs=logs
        )
    except Exception as e:
        logs.append(f"[{time.strftime('%H:%M:%S')}] 错误: {str(e)}")
        return ExecuteResponse(
            task_id=req.task_id,
            status="failed",
            result=str(e),
            logs=logs
        )

@app.post("/ssh-execute")
async def ssh_execute(req: SshExecuteRequest):
    try:
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if req.auth_type == "password":
                ssh.connect(
                    req.host,
                    port=req.port,
                    username=req.username,
                    password=req.credential,
                    timeout=10
                )
            else:
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