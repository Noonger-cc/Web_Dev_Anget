# LangGraph 智能运维 Agent

基于 LangGraph 工作流编排的智能运维 Agent，支持 Web 管理、SSH 直连和本地客户端双模式。

## 项目结构

```
langgraph-ops-agent/
├── web/              # Vue3 前端
├── server-go/        # Go 后端
├── agent-py/         # Python LangGraph 核心
├── client-go/        # Go 目标机客户端
├── docker-compose.yml
├── .env
└── README.md
```

## 技术栈

- **前端**：Vue3 + Vite + Element Plus + Axios + WebSocket
- **后端**：Go + Gin + SQLite + Gorilla WebSocket
- **智能核心**：Python + LangGraph + LangChain + Paramiko + FastAPI
- **客户端**：Go 原生编译

## 快速部署

```bash
docker-compose up -d --build
```

## 本地运行

### 前端
```bash
cd web
npm install
npm run dev
```

### 后端
```bash
cd server-go
go mod tidy
go run main.go
```

### Agent
```bash
cd agent-py
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 客户端
```bash
cd client-go
go mod tidy
go run main.go
```

## 功能特性

1. Web 前端页面：主机管理、任务创建、日志实时展示
2. Go 后端服务：接口提供、任务调度、WebSocket 推送
3. Python LangGraph 核心：运维工作流编排、指令决策
4. SSH 直连模式：无需客户端，直接远程执行命令
5. Go 本地客户端：内网机器长连接、命令执行、日志回传

## 访问地址

- Web UI: http://localhost
- API: http://localhost:8080
- Agent API: http://localhost:8000

## 默认账号

- 用户名：admin
- 密码：admin123
