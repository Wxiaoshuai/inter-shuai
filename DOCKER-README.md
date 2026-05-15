# AI RAG & Agent Service - Docker 部署指南

## 项目简介

AI RAG & Agent Service 是一个智能文档处理与检索增强生成（RAG）系统，支持：

- **RAG 知识库**: 文档上传、分块存储、向量检索（Milvus）、会话管理
- **Agent 智能体**: Word/Excel 文档智能分析、图表生成（热力图、柱状图等）、工作流可视化

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vue 3 Frontend                       │
│                    (localhost:3000)                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                        │
│                  (localhost:8000)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Agent API  │  │  RAG API     │  │  Memory     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
         ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    MySQL     │  │   Milvus     │  │    LLM API   │
│   (8.4)      │  │  (v2.6.15)   │  │  (DashScope) │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM（推荐 8GB+）

## 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp python/.env.example python/.env

# 编辑配置
vim python/.env
```

必需配置：
```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
MYSQL_PASSWORD=your_mysql_password_here
```

### 2. 启动服务

```bash
# 方式一：使用管理脚本（推荐）
./scripts/docker.sh up

# 方式二：直接使用 docker-compose
docker-compose up -d
```

### 3. 验证服务

```bash
# 检查容器状态
docker-compose ps

# 查看应用日志
docker-compose logs -f app

# 访问 API 文档
open http://localhost:8000/docs
```

## Docker 管理命令

### 启动与停止

```bash
./scripts/docker.sh up        # 启动所有服务
./scripts/docker.sh start     # 同 up
./scripts/docker.sh down      # 停止所有服务
./scripts/docker.sh stop      # 同 down
./scripts/docker.sh restart   # 重启所有服务
```

### 构建与清理

```bash
./scripts/docker.sh build     # 仅构建镜像
./scripts/docker.sh clean     # 停止服务并删除数据卷
```

### 日志查看

```bash
./scripts/docker.sh logs              # 查看 app 日志
./scripts/docker.sh logs app          # 同上
./scripts/docker.sh logs mysql        # 查看 MySQL 日志
./scripts/docker.sh logs milvus       # 查看 Milvus 日志
docker-compose logs -f [service]       # 实时查看指定服务日志
```

### 进入容器

```bash
docker exec -it ai-rag-agent-app-1 /bin/bash    # 进入应用容器
docker exec -it ai-rag-agent-mysql-1 mysql -u root -p   # 进入 MySQL
```

## 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 应用 | http://localhost:8000 | FastAPI 主服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 前端 | http://localhost:3000 | Vue 3 前端（需单独启动） |
| Milvus | localhost:19530 | 向量数据库连接 |
| MySQL | localhost:3306 | 数据库连接 |

## 数据管理

### 数据持久化目录

| 宿主机路径 | 容器内路径 | 说明 |
|------------|-----------|------|
| `python/uploads/` | `/app/uploads` | 用户上传文件 |
| `python/outputs/` | `/app/outputs` | 生成的图表文件 |
| mysql_data (volume) | `/var/lib/mysql` | MySQL 数据 |
| milvus_data (volume) | `/var/lib/milvus` | Milvus 数据 |

### 备份数据库

```bash
# 备份 MySQL
docker exec ai-rag-agent-mysql-1 mysqldump -u root -p ai_rag > backup.sql

# 恢复 MySQL
docker exec -i ai-rag-agent-mysql-1 mysql -u root -p ai_rag < backup.sql
```

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose up

# 检查端口占用
netstat -an | grep 3306
netstat -an | grep 19530
netstat -an | grep 8000
```

### 数据库连接失败

```bash
# 检查 MySQL 健康状态
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 测试连接
docker exec -it ai-rag-agent-mysql-1 mysql -u root -p
```

### 清理并重新开始

```bash
# 停止服务并删除所有数据
./scripts/docker.sh clean

# 删除镜像
docker rmi ai-rag-agent:latest

# 重新构建
./scripts/docker.sh up --build
```

## Docker Compose 常用命令

```bash
docker-compose up -d              # 后台启动
docker-compose down               # 停止
docker-compose ps                 # 查看状态
docker-compose logs -f            # 查看日志
docker-compose restart            # 重启
docker-compose pull               # 更新镜像
docker-compose config             # 验证配置
```

## 前端开发模式

如果需要修改前端代码，可以单独运行前端：

```bash
cd web
npm install
npm run dev
# 访问 http://localhost:3000
```

前端开发模式下，API 请求通过 Vite 代理转发到 `localhost:8000`。

## 生产环境部署建议

1. **修改默认密码**: 更新 `MYSQL_PASSWORD`
2. **配置 HTTPS**: 使用 Nginx 反向代理
3. **资源限制**: 根据服务器配置调整 docker-compose 中的资源限制
4. **数据备份**: 定期备份 `uploads/` 和 `outputs/` 目录
5. **日志管理**: 配置日志轮转，避免磁盘空间不足