# LangGraph 智能运维 Agent

基于 LangGraph 工作流编排的智能运维 Agent，支持 Web 管理、SSH 直连和本地客户端双模式。

## 项目结构

```
langgraph-ops-agent/
├── web/              # Vue3 前端
├── server-go/        # Go 后端
├── agent-py/         # Python Agent (LangGraph)
├── client-go/        # Go 目标机客户端
├── docker-compose.yml
├── .env
└── README.md
```

## 技术栈

- **前端**：Vue3 + Vite + Element Plus + Axios + 原生 WebSocket
- **后端**：Go + Gin + SQLite + Gorm + Gorilla WebSocket
- **智能核心**：Python + LangGraph + LangChain + Paramiko
- **客户端**：Go 原生编译（跨平台、无依赖）

## 快速本地运行

### 前置要求

- Node.js 18+
- Go 1.21+
- Python 3.11+

### 启动顺序

#### 1. Go 后端 (8080端口)

```bash
cd server-go
go mod tidy
go run main.go
```

#### 2. Python Agent (8000端口)

```bash
cd agent-py
pip install langgraph langchain paramiko
python langgraph_agent.py
```

#### 3. Vue3 前端 (5173端口)

```bash
cd web
npm install
npm run dev
```

#### 4. Go 客户端 (可选)

```bash
cd client-go
go mod tidy
go run main.go
```

## 访问地址

- Web UI: http://localhost:5173
- 后端 API: http://localhost:8080
- Agent: http://localhost:8000

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

## 功能特性

1. **Web 前端**：登录、主机管理、任务创建、任务列表、日志实时展示
2. **Go 后端**：REST 接口、任务调度、WebSocket 推送、客户端管理
3. **LangGraph Agent**：工作流节点编排、SSH/客户端执行路由、结果校验
4. **Go 客户端**：长连接保活、命令执行、日志回传

## 路由说明

| 路径 | 说明 |
|------|------|
| /login | 登录页 |
| /main/hosts | 主机管理 |
| /main/task/create | 创建任务 |
| /main/tasks | 任务列表 |
| /main/task-log | 日志查看 |

## 技术参数

| 参数 | 值 |
|------|-----|
| 数据库 | ops.db (SQLite) |
| 后端端口 | 8080 |
| 前端端口 | 5173 |
| Agent 端口 | 8000 |
| 客户端心跳 | 30 秒 |
| 任务刷新间隔 | 30 秒 |
| 日志最大条数 | 1000 |

## Docker 部署 (可选)

```bash
docker-compose up -d --build
```

## 目录详情

```
web/
├── src/
│   ├── api/index.js      # API 接口封装
│   ├── views/         # 页面组件
│   │   ├── Login.vue
│   │   ├── Main.vue
│   │   ├── HostManage.vue
│   │   ├── TaskCreate.vue
│   │   ├── TaskList.vue
│   │   └── LogViewer.vue
│   └── router.js

server-go/
├── main.go
├── models/models.go
├── routes/routes.go
└── handlers/handlers.go

agent-py/
└── langgraph_agent.py

client-go/
└── main.go
```

---

**默认管理员账号：admin / admin123**