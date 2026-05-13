# 架构设计文档

## 整体架构

KnowablePlat 采用**客户端-服务端严格分离**的架构：

```
浏览器 (React SPA) ←→ FastAPI (REST API) ←→ PostgreSQL + Redis
                          ↓
                      LLM API (智谱AI glm-5.1)
```

### 分层架构

```
┌─────────────────────────────────┐
│  React SPA (web/)               │  ← 纯 UI 壳
├─────────────────────────────────┤
│  API 路由层 (app/api/)          │  ← 参数校验 + 调用 Service
├─────────────────────────────────┤
│  业务逻辑层 (app/services/)     │  ← Ingest/Query/Generate/Notification
├─────────────────────────────────┤
│  数据访问层 (app/repositories/) │  ← 封装数据库操作
├─────────────────────────────────┤
│  数据模型层 (app/models/)       │  ← SQLAlchemy ORM + Pydantic Schema
└─────────────────────────────────┘
```

### 依赖方向

```
api/ → services/ → models/ + repositories/
```

- 禁止反向依赖
- services 之间可以互相调用，但不允许循环依赖
- 所有 I/O 操作使用 async/await

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | Python 3.13 |
| 数据库 | PostgreSQL 17 | pgvector 扩展 |
| 缓存 | Redis | - |
| ORM | SQLAlchemy 2.x (async) | asyncpg 驱动 |
| 迁移 | Alembic | - |
| 前端 | React + Vite SPA | TypeScript 严格模式 |
| 状态管理 | TanStack Query + Zustand | - |
| 样式 | Tailwind CSS | - |
| 路由 | React Router v7 | 客户端路由 |
| LLM | 智谱AI glm-5.1 | Anthropic 兼容接口 |
| 数据库迁移 | Alembic | - |

## 核心模块

### 知识库管理 (KnowledgeBase)

每个知识库是独立的知识空间，包含独立的来源集合和 wiki 页面集合。知识库之间互不干扰。

- **普通知识库** (`kb_type = knowledge`) — 用户创建的独立知识库
- **工具装备库** (`kb_type = tool_arsenal`) — 系统内置，不可删除

### 来源管理 (Source)

来源是不可变的原始文档（抓取的文章、用户笔记）。归属于某个知识库。

- 抓取服务：`services/fetcher.py` — URL → 干净 Markdown（Jina Reader）
- 文件存储：`raw/{kb_slug}/` 目录

### Wiki 引擎 (WikiPage)

Wiki 是 LLM 生成和维护的结构化 Markdown 文件集合。每个知识库有独立的 wiki 空间。

- 页面类型：source / entity / concept / comparison / tool / tool_category
- 交叉引用：[[wikilinks]] 双向链接
- 文件存储：`wiki/{kb_slug}/` 目录
- 搜索：PostgreSQL tsvector 全文搜索 + pgvector 向量搜索

### Ingest 流水线

将来源转化为 wiki 页面的完整流水线。详见 [ingest-pipeline.md](ingest-pipeline.md)。

### LLM 集成

- 提示词外部化存储在 `app/prompts/*.md`
- 统一 LLM 接口：`services/llm.py`
- 结构化输出（JSON mode）减少 token 消耗

## 文件系统布局

```
backend/app/
├── raw/{kb_slug}/          # 原始来源文档（不可变）
├── wiki/{kb_slug}/         # Wiki 页面
│   ├── index.md            # 知识库目录
│   ├── log.md              # 活动日志
│   └── *.md                # 各类 wiki 页面
└── prompts/                # LLM 提示词模板
    └── *.md                # 外部化提示词
```

## 数据库设计

详见 CLAUDE.md 中的数据库设计章节。核心表：

- `users` — 用户
- `knowledge_bases` — 知识库
- `sources` — 原始来源
- `wiki_pages` — Wiki 页面（含 tsvector 和 vector 列）
- `entities` — 实体
- `rss_feeds` / `rss_entries` — RSS 订阅
- `notifications` — 知识新增通知
- `generated_docs` — 生成文档
- `activity_log` — 操作日志
