# 全面RAG知识库问答助手

基于 **RAG（检索增强生成）** 技术的智能知识库问答系统。支持多格式文档上传、向量检索、HyDE 假设性文档生成、文档级召回，结合阿里云 DashScope 通义千问大模型，提供精准、高效的知识问答服务。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178c6.svg)](https://www.typescriptlang.org/)

---

## 目录

- [系统架构](#系统架构)
- [核心特性](#核心特性)
- [RAG 检索流程](#rag-检索流程)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [1. 克隆项目](#1-克隆项目)
  - [2. 启动基础设施（PostgreSQL + Redis）](#2-启动基础设施postgresql--redis)
  - [3. 后端配置与启动](#3-后端配置与启动)
  - [4. 前端配置与启动](#4-前端配置与启动)
- [配置说明](#配置说明)
- [API 接口概览](#api-接口概览)
- [部署](#部署)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [License](#license)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (React 19)                      │
│          Vite + TypeScript + TailwindCSS + Radix UI       │
│              Axios SSE 流式通信 / Zustand 状态管理          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────────┐
│                   后端 (FastAPI)                          │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐     │
│  │ JWT 认证  │  │ 限流控制  │  │ 请求日志 / 审计日志  │     │
│  └──────────┘  └──────────┘  └────────────────────┘     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Agent (LangChain)                     │   │
│  │  ┌─────────────┐  ┌──────────────────────────┐   │   │
│  │  │  RAG Tool   │  │  应用启动 Tool (kugou等)  │   │   │
│  │  └──────┬──────┘  └──────────────────────────┘   │   │
│  │         │                                         │   │
│  │  ┌──────▼──────────────────────────────────┐     │   │
│  │  │          RAG Pipeline                     │     │   │
│  │  │  ┌─────────┐  ┌────────┐  ┌─────────┐   │     │   │
│  │  │  │  HyDE   │→│ 向量检索 │→│ 重排序  │   │     │   │
│  │  │  │ 假设文档 │  │ PGVector│  │Reranker │   │     │   │
│  │  │  └─────────┘  └────────┘  └─────────┘   │     │   │
│  │  │       ↓                                    │     │   │
│  │  │  ┌──────────────────────────────────┐     │     │   │
│  │  │  │       文档级召回 (score > 0.75)     │     │     │   │
│  │  │  │  → 取回整篇文档全部分块，避免遗漏     │     │     │   │
│  │  │  └──────────────────────────────────┘     │     │   │
│  │  └───────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              文档处理流水线                          │   │
│  │  MD5去重 → 加载 → 分块 → 元数据标注 → 向量化入库    │   │
│  │  (PDF/Word/PPT/TXT/MD/CSV/Excel)                   │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────┬──────────────┬───────────────────────────┘
               │              │
    ┌──────────▼──┐    ┌──────▼──────┐
    │ PostgreSQL   │    │    Redis    │
    │ + PGVector   │    │ (缓存/Session)│
    └─────────────┘    └─────────────┘
```

---

## 核心特性

### 智能问答
- **通义千问大模型**：基于阿里云 DashScope 的 qwen3-max 模型，支持流式输出（SSE）
- **Agent 自主决策**：LangChain Agent 自动判断何时调用 RAG 检索、何时直接回答
- **历史对话管理**：Token 预算控制（4000 tokens），自动截断过长历史，支持多轮对话
- **异步任务隔离**：数据库写入操作通过 `asyncio.create_task` 与请求生命周期解耦，用户取消请求不会导致数据库连接中断

### RAG 检索增强
- **HyDE 假设性文档生成**：将用户问题先转换为假设性文档，再用假设文档去向量库检索，显著提升召回率
- **PGVector 向量检索**：基于 PostgreSQL + pgvector 扩展，支持余弦相似度检索
- **qwen3-rerank 重排序**：对召回结果进行语义重排序，过滤低相关度文档
- **文档级召回**：当最高分 chunk 超过阈值（0.75）时，自动取回该文档的全部 chunk，避免只召回片段导致回答不完整

### 知识库管理
- **多知识库支持**：创建多个知识库，独立管理不同领域的文档
- **多格式文档**：支持 PDF、Word（.docx）、PPT（.pptx）、TXT、Markdown（.md）、CSV、Excel（.xlsx/.xls）
- **CSV 优化加载**：自定义 CSV 加载器，按 100 行一批合并为 Document，避免一行一个 Document 导致的性能问题
- **表格 AI 摘要**：CSV/Excel 文件上传后自动调用 AI 生成内容摘要作为文档标题，提升文档级召回准确率
- **MD5 去重**：文件入库前计算 MD5 校验，防止重复上传浪费向量存储和 embedding 费用
- **入库重试**：embedding 调用阿里云接口偶发网络抖动时自动重试 3 次

### 用户与安全
- **JWT 认证**：基于 python-jose 的 Token 认证，支持注册、登录、个人信息管理
- **知识库隔离**：数据按用户维度隔离，支持多用户环境
- **请求限流**：可配置的 API 限流控制
- **安全中间件**：审计日志、隐私过滤、Prompt 注入防护

### 前端
- **React 19 + TypeScript**：现代化前端技术栈
- **Vite 8**：极速开发构建
- **TailwindCSS**：原子化 CSS 样式
- **Radix UI**：无障碍访问组件库
- **i18n 国际化**：支持中文 / English 双语切换
- **深色模式**：支持浅色/深色主题切换
- **SSE 流式对话**：实时接收 AI 回答，支持中途停止

---

## RAG 检索流程

```
用户提问
  │
  ├─ 1. HyDE 生成假设性文档
  │     qwen3-max 将问题改写为一篇假设性回答文档
  │
  ├─ 2. PGVector 向量检索
  │     用假设文档去向量库检索 top-k 相似分块
  │
  ├─ 3. qwen3-rerank 重排序
  │     对检索结果进行语义级重排序，过滤低分文档
  │
  ├─ 4. 文档级召回判断
  │     ├─ score > 0.75 → 取回该文档全部 chunk（文档级召回）
  │     └─ score ≤ 0.75 → 仅取回 score > 0.5 的 chunk
  │
  ├─ 5. 上下文拼接
  │     将检索到的文档内容作为上下文注入 Prompt
  │
  └─ 6. 生成最终回答
        qwen3-max 基于上下文生成答案，流式返回
```

---

## 技术栈

### 后端
| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.115+ |
| ASGI 服务器 | Uvicorn |
| LLM 框架 | LangChain 1.3+ / LangGraph 1.2+ |
| 大模型 | 阿里云 DashScope (ChatTongyi qwen3-max) |
| Embedding 模型 | text-embedding-v4 |
| Reranker 模型 | qwen3-rerank |
| 向量数据库 | PostgreSQL 17 + pgvector |
| 关系数据库 | PostgreSQL 17 + SQLAlchemy 2.0 (async) |
| 数据库迁移 | Alembic |
| 缓存 | Redis 7 |
| 认证 | python-jose (JWT) + passlib (bcrypt) |
| 文档加载 | PyMuPDF / Unstructured / python-pptx |
| 监控追踪 | LangSmith |

### 前端
| 类别 | 技术 |
|------|------|
| 框架 | React 19 |
| 语言 | TypeScript 6.0 |
| 构建工具 | Vite 8 |
| 样式 | TailwindCSS 3.4 |
| UI 组件 | Radix UI |
| 状态管理 | Zustand |
| 路由 | React Router 6 |
| HTTP 客户端 | Axios |
| 国际化 | i18next / react-i18next |
| Markdown 渲染 | react-markdown + rehype-highlight |
| 通知 | Sonner |

---

## 项目结构

```
全面RAG知识库问答助手/
├── README.md                          # 项目说明文档
├── .gitignore                         # Git 忽略规则
│
├── agent-backend/                     # 后端服务
│   ├── .env.example                   # 环境变量模板（提交到 Git）
│   ├── .env                           # 实际环境变量（不提交，含密钥）
│   ├── pyproject.toml                 # Python 项目配置与依赖
│   ├── run.py                         # 开发启动入口
│   ├── Dockerfile                     # 生产环境容器镜像
│   ├── docker-compose.yml             # 本地开发基础设施
│   ├── alembic.ini                    # 数据库迁移配置
│   │
│   ├── alembic/                       # 数据库迁移版本
│   │   └── versions/
│   │
│   ├── deploy/                        # 部署配置
│   │   ├── nginx.conf
│   │   └── supervisor.conf
│   │
│   ├── src/                           # 源码目录
│   │   ├── main.py                    # FastAPI 应用入口
│   │   ├── config.py                  # 配置管理（pydantic-settings）
│   │   │
│   │   ├── api/                       # API 路由层
│   │   │   └── routers/
│   │   │       ├── chat.py            # 对话接口（SSE 流式）
│   │   │       ├── conversations.py   # 会话管理
│   │   │       ├── knowledge_bases.py # 知识库 CRUD
│   │   │       ├── documents.py       # 文档上传/管理
│   │   │       ├── users.py           # 用户管理
│   │   │       ├── stats.py           # 统计接口
│   │   │       ├── export_import.py   # 数据导入导出
│   │   │       └── health.py          # 健康检查
│   │   │
│   │   ├── core/                      # 核心业务逻辑
│   │   │   ├── agent/
│   │   │   │   ├── agent.py           # Agent 主逻辑（流式对话）
│   │   │   │   └── factory.py         # 模型工厂（Chat/Embedding/Reranker）
│   │   │   │
│   │   │   ├── rag/                   # RAG 检索增强
│   │   │   │   ├── rag_core.py        # RAG 主流程（HyDE → 检索 → 重排 → 召回）
│   │   │   │   ├── vector_store.py    # PGVector 向量存储服务
│   │   │   │   ├── reranker.py        # 重排序服务
│   │   │   │   ├── text_spliter.py    # 文本分块器
│   │   │   │   ├── document_loader.py # 文档加载器（PDF/Word/PPT/CSV/Excel...）
│   │   │   │   └── document_processor.py # 文档处理流水线
│   │   │   │
│   │   │   └── tools/                 # Agent 工具集
│   │   │       ├── rag.py             # RAG 检索工具
│   │   │       └── app_launcher.py    # 应用启动工具
│   │   │
│   │   ├── models/                    # SQLAlchemy 数据模型
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   ├── knowledge_base.py
│   │   │   └── role.py
│   │   │
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   │   ├── chat.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── knowledge_base.py
│   │   │
│   │   ├── services/                  # 业务服务层
│   │   │   ├── user_service.py        # 用户服务
│   │   │   ├── document_service.py    # 文档管理服务
│   │   │   ├── conversation.py        # 会话服务
│   │   │   ├── file_storage.py        # 文件存储服务
│   │   │   ├── knowledge_base.py      # 知识库服务
│   │   │   ├── stats.py               # 统计服务
│   │   │   ├── feedback.py            # 反馈服务
│   │   │   ├── export_import.py       # 导入导出服务
│   │   │   ├── cache.py               # 缓存服务
│   │   │   ├── rate_limiter.py        # 限流服务
│   │   │   └── task_queue.py          # 任务队列
│   │   │
│   │   ├── middleware/                # 中间件
│   │   │   ├── logging_mw.py          # 请求日志中间件
│   │   │   ├── exception_handler.py   # 全局异常处理
│   │   │   ├── audit_log.py           # 审计日志
│   │   │   ├── privacy_filter.py      # 隐私过滤
│   │   │   └── prompt_injection.py    # Prompt 注入防护
│   │   │
│   │   ├── auth/                      # 认证模块
│   │   │   └── security.py            # JWT 生成/验证
│   │   │
│   │   ├── db/                        # 数据库
│   │   │   ├── session.py             # 异步会话管理
│   │   │   └── redis.py               # Redis 连接
│   │   │
│   │   ├── cache/                     # 缓存
│   │   │   └── redis.py               # Redis 缓存客户端
│   │   │
│   │   ├── configs/                   # 配置文件
│   │   │   └── chroma.yaml            # 向量库/分块配置
│   │   │
│   │   ├── prompt/                    # Prompt 模板
│   │   │   ├── agent_prompt.txt       # Agent 系统提示词
│   │   │   ├── rag_summarize_prompt.txt # RAG 总结提示词
│   │   │   └── prompt_loader.py       # Prompt 加载器
│   │   │
│   │   ├── logger/                    # 日志模块
│   │   │   └── logger.py
│   │   │
│   │   └── data/                      # 运行时数据
│   │       └── md5_hex_store/         # MD5 去重存储
│   │
│   └── tests/                         # 测试目录
│       ├── conftest.py
│       ├── test_api/
│       └── test_core/
│
├── front/                             # 前端项目
│   ├── src/
│   │   ├── main.tsx                   # 应用入口
│   │   ├── App.tsx                    # 根组件
│   │   ├── index.css                  # 全局样式
│   │   │
│   │   ├── api/                       # API 客户端
│   │   │   ├── client.ts              # Axios 实例
│   │   │   ├── auth.ts                # 认证 API
│   │   │   ├── knowledge.ts           # 知识库 API
│   │   │   ├── knowledgeBases.ts      # 知识库管理 API
│   │   │   ├── sessions.ts            # 会话 API
│   │   │   └── endpoints.ts           # 接口地址常量
│   │   │
│   │   ├── components/                # 组件
│   │   │   ├── common/                # 通用组件
│   │   │   │   ├── ConfirmDialog.tsx
│   │   │   │   └── EmptyState.tsx
│   │   │   ├── knowledge/             # 知识库组件
│   │   │   │   └── DocumentDetailDrawer.tsx
│   │   │   └── layout/                # 布局组件
│   │   │       └── Sidebar.tsx
│   │   │
│   │   ├── pages/                     # 页面
│   │   │   ├── AIChat.tsx             # AI 对话页
│   │   │   ├── KnowledgeBase.tsx       # 知识库管理页
│   │   │   ├── Sessions.tsx            # 历史会话页
│   │   │   ├── Profile.tsx             # 个人信息页
│   │   │   ├── Settings.tsx            # 设置页
│   │   │   ├── AboutUs.tsx             # 关于页
│   │   │   ├── Login.tsx               # 登录页
│   │   │   └── Register.tsx            # 注册页
│   │   │
│   │   ├── hooks/                     # 自定义 Hooks
│   │   │   ├── useSSE.ts              # SSE 流式通信 Hook
│   │   │   └── useDebounce.ts         # 防抖 Hook
│   │   │
│   │   ├── i18n/                      # 国际化
│   │   │   ├── index.ts
│   │   │   └── locales/
│   │   │       ├── zh-CN.ts           # 中文翻译
│   │   │       └── en-US.ts           # 英文翻译
│   │   │
│   │   ├── stores/                    # Zustand 状态管理
│   │   │   ├── useUserStore.ts
│   │   │   ├── useSessionStore.ts
│   │   │   ├── useKnowledgeBaseStore.ts
│   │   │   ├── useThemeStore.ts
│   │   │   ├── useLanguageStore.ts
│   │   │   └── useChatColorStore.ts
│   │   │
│   │   ├── router/                    # 路由配置
│   │   │   └── index.tsx
│   │   │
│   │   ├── layouts/                   # 布局
│   │   │   ├── MainLayout.tsx
│   │   │   └── AuthLayout.tsx
│   │   │
│   │   └── types/                     # TypeScript 类型定义
│   │       └── api.ts
│   │
│   ├── public/                        # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.cjs
│   └── tsconfig.json
│
└── .trae/                             # IDE 配置
```

---

## 快速开始

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.11+ | 后端运行环境 |
| Node.js | 18+ | 前端运行环境 |
| PostgreSQL | 17 | 数据库 + PGVector 向量存储 |
| Redis | 7 | 缓存与会话管理 |
| 阿里云 DashScope API Key | - | 大模型调用（[申请地址](https://dashscope.console.aliyun.com/)） |

### 1. 克隆项目

```bash
git clone https://github.com/landaos/HaoBro_agent_repository.git
cd HaoBro_agent_repository
```

### 2. 启动基础设施（PostgreSQL + Redis）

使用 Docker Compose 一键启动：

```bash
cd agent-backend
docker compose up -d
```

这将启动：
- **PostgreSQL 17** + pgvector 扩展（端口 5432）
- **Redis 7**（端口 6379）

> 如果不想用 Docker，也可以手动安装 PostgreSQL（需启用 pgvector 扩展）和 Redis。

### 3. 后端配置与启动

**3.1 创建虚拟环境**

```bash
cd agent-backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3.2 安装依赖**

```bash
pip install -e .
```

**3.3 配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```ini
# 必填项
SECRET_KEY=你的JWT密钥（随机字符串）
ALIYUN_ACCESS_KEY_SECRET=sk-你的阿里云DashScope_API_Key
DB_PASSWORD=你的数据库密码

# 以下已有默认值，可按需修改
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db
DB_USER=agent_user
CHAT_MODEL_NAME=qwen3-max
TEXT_EMBEDDING_MODEL_NAME=text-embedding-v4
RERANKER_MODEL_NAME=qwen3-rerank
```

**3.4 初始化数据库**

```bash
alembic upgrade head
```

**3.5 启动后端服务**

```bash
python run.py
```

后端运行在 `http://localhost:8000`，API 文档自动生成在 `http://localhost:8000/docs`。

### 4. 前端配置与启动

**4.1 安装依赖**

```bash
cd front
npm install
```

**4.2 启动开发服务器**

```bash
npm run dev
```

前端运行在 `http://localhost:5173`，API 请求自动代理到后端 `http://localhost:8000`。

**4.3 构建生产版本**

```bash
npm run build
```

构建产物在 `front/dist/` 目录，可直接部署到 Nginx 或其他静态文件服务器。

---

## 配置说明

### 环境变量 (.env)

| 变量名 | 必填 | 说明 | 示例值 |
|--------|:---:|------|--------|
| `SECRET_KEY` | 是 | JWT 签名密钥 | `随机字符串` |
| `ALIYUN_ACCESS_KEY_SECRET` | 是 | 阿里云 DashScope API Key | `sk-xxxx` |
| `CHAT_MODEL_NAME` | 否 | 对话模型名称 | `qwen3-max` |
| `TEXT_EMBEDDING_MODEL_NAME` | 否 | 向量化模型名称 | `text-embedding-v4` |
| `RERANKER_MODEL_NAME` | 否 | 重排序模型名称 | `qwen3-rerank` |
| `DB_HOST` | 否 | PostgreSQL 主机 | `localhost` |
| `DB_PORT` | 否 | PostgreSQL 端口 | `5432` |
| `DB_NAME` | 否 | 数据库名 | `agent_db` |
| `DB_USER` | 否 | 数据库用户 | `agent_user` |
| `DB_PASSWORD` | 是 | 数据库密码 | `your_password` |
| `REDIS_HOST` | 否 | Redis 主机 | `localhost` |
| `REDIS_PORT` | 否 | Redis 端口 | `6379` |
| `RATE_LIMIT_ENABLED` | 否 | 是否启用限流 | `true` / `false` |
| `LANGCHAIN_TRACING_V2` | 否 | 是否启用 LangSmith 追踪 | `true` / `false` |

### 分块配置 (chroma.yaml)

```yaml
chunk_size: 200          # 每个分块的最大字符数
chunk_overlap: 20        # 相邻分块重叠字符数
k: 5                     # 向量检索返回的 top-k 数量
allow_knowledge_file_types:  # 允许上传的文件类型
  - txt
  - pdf
  - md
  - pptx
  - docx
  - csv
  - xlsx
  - xls
```

---

## API 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 健康检查 |
| `POST` | `/api/v1/auth/register` | 用户注册 |
| `POST` | `/api/v1/auth/login` | 用户登录 |
| `GET` | `/api/v1/users/me` | 获取当前用户信息 |
| `PUT` | `/api/v1/users/me` | 更新用户信息 |
| `POST` | `/api/v1/chat/stream` | 流式对话（SSE） |
| `GET` | `/api/v1/conversations` | 获取会话列表 |
| `DELETE` | `/api/v1/conversations/{id}` | 删除会话 |
| `GET` | `/api/v1/knowledge-bases` | 获取知识库列表 |
| `POST` | `/api/v1/knowledge-bases` | 创建知识库 |
| `DELETE` | `/api/v1/knowledge-bases/{id}` | 删除知识库 |
| `POST` | `/api/v1/knowledge-bases/{id}/documents` | 上传文档 |
| `GET` | `/api/v1/knowledge-bases/{id}/documents` | 获取文档列表 |
| `DELETE` | `/api/v1/knowledge-bases/{id}/documents/{doc_id}` | 删除文档 |
| `POST` | `/api/v1/knowledge-bases/{id}/documents/{doc_id}/reprocess` | 重新处理文档 |

完整 API 文档：启动后端后访问 `http://localhost:8000/docs`（Swagger UI）。

---

## 部署

### Docker 部署（推荐）

```bash
# 1. 构建后端镜像
cd agent-backend
docker build -t agent-backend .

# 2. 启动所有服务
docker compose up -d

# 3. 前端构建
cd ../front
npm run build

# 4. 将 front/dist/ 部署到 Nginx
```

### 手动部署

后端使用 `uvicorn` 启动，推荐配合 `supervisor` 或 `systemd` 管理进程。生产环境需注意：

1. 将 `.env` 中的 `RATE_LIMIT_ENABLED` 设为 `true`
2. 修改 `main.py` 中 CORS 的 `allow_origins` 为具体域名
3. 前端构建后部署到 Nginx，配置反向代理到后端 8000 端口

---

## 开发指南

### 代码规范

- 后端使用 **Ruff** 进行代码格式化与检查
- 前端使用 **ESLint** + **TypeScript** 严格模式
- 提交前运行 `pre-commit` 钩子自动检查

### 运行测试

```bash
cd agent-backend
pytest
```

### 数据库迁移

```bash
# 创建迁移版本
alembic revision --autogenerate -m "描述你的改动"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 常见问题

**Q: 启动后端报 `ValueError: Got a larger chunk overlap than chunk size`**

A: 检查 `src/configs/chroma.yaml` 中的 `chunk_overlap` 必须小于 `chunk_size`。

**Q: 上传 CSV 文件很慢？**

A: 自定义 CSV 加载器按 100 行一批合并，1000 行约产生 10 个 Document。如果 CSV 行数特别多（>5000 行），建议先拆分文件再上传。

**Q: RAG 回答不准确？**

A: 可能原因：
1. 文档分块大小不合适（当前 200 字符），可调整 `chunk_size`
2. 文档标题不够精确，上传时检查 AI 生成的内容摘要是否准确
3. 查看日志中的 `【rag】` 标签，确认检索和重排序的分数

**Q: 如何更换模型？**

A: 修改 `.env` 中的 `CHAT_MODEL_NAME`，支持阿里云 DashScope 所有模型（如 `qwen-plus`、`qwen-max`、`qwen-turbo` 等）。

---

## License

[MIT License](https://opensource.org/licenses/MIT)

Copyright (c) 2026 landaos