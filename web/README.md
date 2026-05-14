# AI Assistant - RAG & Agent 智能助手

一个基于 Vue 3 + FastAPI 的智能助手前端应用，提供 RAG（检索增强生成）对话和 Agent 智能体交互功能。

## 功能特性

- **macOS 风格 Dock 菜单** - 底部图标悬停放大效果，流畅的交互体验
- **RAG 智能对话** - 文档上传、索引创建、语义检索、问答
- **Agent 智能体** - 与 AI 智能体进行对话交互
- **深色玻璃态设计** - 使用 oklch 色彩空间打造的现代界面
- **响应式布局** - 自适应不同屏幕尺寸

## 技术栈

- **前端框架**: Vue 3
- **构建工具**: Vite 5
- **样式**: 纯 CSS / CSS Variables
- **后端**: FastAPI (Python)
- **色彩空间**: oklch

## 快速开始

### 1. 安装依赖

```bash
cd web
npm install
```

### 2. 启动后端服务

```bash
cd ../python
uv run uvicorn src.main:app --reload --port 8000
```

后端服务运行在 http://localhost:8000

### 3. 启动前端开发服务器

```bash
cd web
npm run dev
```

前端服务运行在 http://localhost:3000

### 4. 访问应用

打开浏览器访问 http://localhost:3000

## 项目命令

| 命令 | 描述 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |

## 界面说明

### 首页

展示项目欢迎界面，采用深色渐变背景和柔和的青色光晕效果。

### RAG 展示

智能文档问答界面，包含以下功能：

- **新建对话**: 点击左侧边栏的「+ 新建」按钮
- **对话列表**: 左侧边栏显示所有历史对话
- **发送消息**: 在底部输入框输入问题，按 Enter 或点击发送按钮
- **上传文档**: 支持 .txt 和 .md 格式文件
- **创建索引**: 上传文档后可点击「创建索引」建立向量索引

### Agent 展示

Agent 智能体交互界面（功能开发中）。

### 关于我

个人信息页面（内容开发中）。

## API 接口

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
| POST | `/agent/{id}/chat` | 与 Agent 对话 |
| GET | `/agent/{id}/history` | 获取对话历史 |
| GET | `/agent/{id}/state` | 获取 Agent 状态 |

## 项目结构

```
web/
├── index.html              # 应用入口
├── package.json            # 项目配置
├── vite.config.js          # Vite 配置
├── README.md               # 本文档
└── src/
    ├── main.js             # 应用入口
    ├── App.vue             # 根组件
    ├── styles/
    │   └── global.css      # 全局样式与 CSS 变量
    ├── components/
    │   ├── Dock.vue        # Dock 菜单组件
    │   ├── HomePage.vue    # 首页
    │   ├── RagPage.vue     # RAG 展示页
    │   ├── AgentPage.vue   # Agent 展示页
    │   └── AboutPage.vue   # 关于我页
    └── composables/
        └── useApi.js       # API 调用封装
```

## 设计系统

### 色彩

```css
--color-bg-primary: oklch(12% 0.02 265);    /* 主背景 */
--color-bg-secondary: oklch(18% 0.015 280); /* 次背景 */
--color-accent: oklch(68% 0.14 175);        /* 强调色-青色 */
--color-text-primary: oklch(95% 0.01 250);  /* 主文字 */
--color-text-secondary: oklch(70% 0.02 250); /* 次文字 */
```

### 字体

使用 Sora 字体，避免了常见的 Inter、Roboto 等字体。

### 圆角

- 大圆角: 16-24px (卡片)
- 小圆角: 8-12px (按钮、输入框)

### 动效

- 默认过渡: `cubic-bezier(0.4, 0, 0.2, 1)`
- 弹性效果: `cubic-bezier(0.34, 1.56, 0.64, 1)`

## 注意事项

1. 确保后端服务已启动并运行在 http://localhost:8000
2. 前端开发服务器代理 API 请求到后端（配置在 vite.config.js）
3. 文件上传功能目前仅支持 .txt 和 .md 格式
4. 对话记录保存在浏览器 localStorage 中

## 许可证

MIT