# AI RAG & Agent API Service

一个提供 RAG（检索增强生成）系统和 Agent 智能体系统接口的 FastAPI 服务。

## 功能特性

- **RAG 接口**：文档索引创建、语义检索、问答
- **Agent 接口**：智能体创建、运行、对话、人机交互
- **模块化设计**：分离工具类、服务层、路由层
- **可配置化**：通过环境变量管理配置

## 技术栈

- FastAPI - Web 框架
- LangChain / LangGraph - RAG 和 Agent 框架
- Milvus - 向量数据库
- DeepSeek / 阿里云百炼 - LLM 和 Embedding

## 项目结构

```
ai/
├── src/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── rag/                 # RAG 模块
│   │   ├── routers.py       # API 路由
│   │   ├── service.py       # 服务逻辑
│   │   ├── tools.py         # 工具类
│   │   └── schemas.py       # Pydantic 模型
│   ├── agent/               # Agent 模块
│   │   ├── routers.py       # API 路由
│   │   ├── service.py       # 服务逻辑
│   │   ├── graph.py         # LangGraph 工作流
│   │   └── schemas.py       # Pydantic 模型
│   └── core/                # 核心模块
│       ├── llm.py           # LLM 初始化
│       ├── embedding.py     # Embedding 初始化
│       └── milvus.py        # Milvus 客户端
├── .env.example
└── pyproject.toml
```

## 快速开始

### 1. 安装依赖

```bash
cd ai
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写 API 密钥
```

### 3. 启动服务

```bash
uvicorn src.main:app --reload --port 8000
# 使用uv
uv run uvicorn src.main:app --reload --port 8000
```

### 4. 访问 API 文档

打开 http://localhost:8000/docs 查看交互式 API 文档。

## API 端点

### RAG 接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/rag/index/create` | 创建文档索引 |
| POST | `/rag/index/{collection}` | 添加文档到索引 |
| DELETE | `/rag/index/{collection}` | 删除索引 |
| POST | `/rag/search` | 语义检索 |
| POST | `/rag/ask` | RAG 问答 |
| GET | `/rag/collections` | 获取所有集合 |

### Agent 接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/agent/create` | 创建 Agent |
| GET | `/agent/list` | 列出所有 Agent |
| DELETE | `/agent/{id}` | 删除 Agent |
| POST | `/agent/{id}/run` | 运行 Agent |
| POST | `/agent/{id}/chat` | 与 Agent 对话 |
| GET | `/agent/{id}/state` | 获取 Agent 状态 |
| POST | `/agent/{id}/human-feedback` | 人工反馈 |
| GET | `/agent/{id}/history` | 获取对话历史 |

## 使用示例

### RAG 问答

```bash
# 创建索引
curl -X POST http://localhost:8000/rag/index/create \
  -H "Content-Type: application/json" \
  -d '{"documents":[{"content":"这是一个测试文档"}],"collection":"test"}'

# PowerShell 语法
Invoke-WebRequest -Uri http://localhost:8000/rag/index/create -Method POST -ContentType "application/json" -Body '{"documents":[{"content":"这是一个测试文档"}],"collection":"test"}'


# 语义检索
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query":"测试","collection":"test","k":3}'

# PowerShell 语法
Invoke-WebRequest -Uri http://localhost:8000/rag/search -Method POST -ContentType "application/json" -Body '{"query":"测试","collection":"test","k":3}'


# 问答
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"文档内容是什么？","collection":"test"}'

# PowerShell 语法
Invoke-WebRequest -Uri http://localhost:8000/rag/ask -Method POST -ContentType "application/json" -Body '{"question":"文档内容是什么？","collection":"test"}'
```

### Agent 对话

```bash
# 创建 Agent
curl -X POST http://localhost:8000/agent/create \
  -H "Content-Type: application/json" \
  -d '{"name":"my_agent","description":"我的智能体"}'

# PowerShell 语法
Invoke-WebRequest -Uri http://localhost:8000/agent/create -Method POST -ContentType "application/json" -Body '{"name":"my_agent","description":"我的智能体"}'


# 与 Agent 对话 (假设 agent_id = 你的id)
curl -X POST http://localhost:8000/agent/{agent_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'

# PowerShell 语法
Invoke-WebRequest -Uri http://localhost:8000/agent/{agent_id}/chat -Method POST -ContentType "application/json" -Body '{"message":"你好"}'
```