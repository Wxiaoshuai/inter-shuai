# AI RAG & Agent Service

智能文档处理与检索增强生成（RAG）系统，支持上传 Word/Excel 文件并通过 AI 智能体进行分析处理。

## 功能特性

### RAG 知识库
- 文档上传与分块存储
- 向量检索（Milvus）
- 会话管理

### Agent 智能体
- Word/Excel 文档智能分析
- 图表生成（热力图、柱状图、折线图、饼图、散点图、直方图）
- 多步骤处理流程与结果验证
- 工作流图形可视化（支持分支）

## 项目结构

```
├── python/                  # 后端 (FastAPI + LangChain)
│   ├── src/
│   │   ├── agent/           # Agent 智能体模块
│   │   │   ├── doc_agent.py     # 文档处理 Agent
│   │   │   ├── tools.py         # 文档处理工具（读取、图表生成）
│   │   │   ├── file_service.py  # 文件存储服务
│   │   │   ├── routers.py       # API 路由
│   │   │   ├── schemas.py       # Pydantic 模型
│   │   │   └── service.py       # 业务逻辑
│   │   ├── core/            # 核心组件
│   │   │   ├── llm.py           # LLM 接口
│   │   │   └── embedding.py     # 向量嵌入
│   │   ├── db/              # 数据库
│   │   │   ├── mysql.py         # MySQL 连接池
│   │   │   └── models.py        # 数据模型
│   │   ├── memory/          # 记忆管理
│   │   ├── rag/             # RAG 模块
│   │   └── main.py          # FastAPI 入口
│   └── pyproject.toml      # 依赖配置
│
├── web/                     # 前端 (Vue 3)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentPage.vue    # Agent 文档处理页面
│   │   │   ├── RagPage.vue      # RAG 知识库页面
│   │   │   ├── HomePage.vue     # 首页
│   │   │   └── Dock.vue         # 导航栏
│   │   └── composables/
│   │       └── useApi.js        # API 调用封装
│   └── vite.config.js      # Vite 配置
│
└── .gitignore
```

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **AI**: LangChain + LangGraph
- **向量数据库**: Milvus
- **关系数据库**: MySQL (aiomysql)
- **文档处理**: pandas, openpyxl, python-docx, matplotlib

### 前端
- **框架**: Vue 3 (Composition API)
- **构建**: Vite
- **Markdown**: marked
- **样式**: CSS (原生)

## 快速开始

### 后端

```bash
cd python
uv sync
uv run fastapi dev src/main.py
```

### 前端

```bash
cd web
npm install
npm run dev
```

## API 接口

### Agent 接口
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/agent/file-upload` | 上传 Word/Excel 文件 |
| POST | `/agent/process` | 处理文档 |
| GET | `/agent/chart/{image_id}` | 获取图表图片 |
| DELETE | `/agent/file/{file_id}` | 删除文件 |
| GET | `/agent/graph` | 获取工作流图 |
| GET | `/agent/list` | 列出所有 Agent |

### RAG 接口
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/rag/sessions` | 创建会话 |
| GET | `/rag/sessions` | 获取会话列表 |
| POST | `/rag/index/create` | 创建索引 |
| POST | `/rag/search` | 检索 |
| POST | `/rag/ask` | 问答 |

## 工作流程

### Agent 文档处理流程

```
上传文件 → 读取文件 → LLM 分析 → 生成图表? → 验证结果 → 整理输出
                                  ↓
                              [继续/结束]
```

### 处理状态说明
- `needs_confirmation`: 分析结果需用户确认是否继续
- `success`: 处理完成

## 环境变量

```bash
# python/.env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_rag

MILVUS_HOST=localhost
MILVUS_PORT=19530

DASHSCOPE_API_KEY=your_api_key
```

## 注意事项

- 上传文件存储在 `python/uploads/`
- 生成的图表存储在 `python/outputs/`
- 删除任务时会同时清理相关文件