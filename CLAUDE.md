# KnowablePlat — LLM 驱动的知识管理平台

## 项目概述

一个全栈知识管理平台，灵感来自 Karpathy 的 LLM-Wiki 模式。用户提交在线文章链接，系统抓取并存储，然后使用 LLM 增量构建和维护一个结构化、互相链接的 wiki。通过网页端进行浏览、查询和学习。

**核心理念：** 不同于 RAG（每次查询都从原始文档检索），LLM 增量构建并维护一个**持久的 wiki** —— 一个结构化、互相链接的 Markdown 文件集合。知识只编译一次并持续更新，而非每次查询重新推导。每添加一个新来源、每提一个问题，wiki 都会变得更丰富。

**关键差异：wiki 是一个持久的、可复利的产物。** 交叉引用已经建立，矛盾已经标记，综合分析已反映所有已读内容。人类负责策展来源、引导分析、提出好问题。LLM 负责其余所有工作——摘要、交叉引用、归档、簿记。

**仓库地址：** https://github.com/xvgawa-art/knowablePlat

**技术栈：** Python 3.13 + FastAPI + PostgreSQL + Next.js + Redis

**多层架构（Karpathy LLM-Wiki 模式 + 知识库分类）：**
1. **Knowledge Bases（知识库层）** — 用户创建的独立知识库（如「Web 安全」「鸿蒙安全」「AI 安全」），每个知识库拥有独立的 wiki 空间、来源集合和学习队列。知识库之间互不干扰。
2. **Raw Sources（原始来源层）** — 不可变的源文档（抓取的文章、PDF、用户笔记）。归属于某个知识库。LLM 只读不写。
3. **The Wiki（Wiki 层）** — 每个知识库下独立的 LLM 生成 Markdown：摘要页、实体页、概念页、对比页、交叉引用。LLM 完全拥有这一层。
4. **The Schema（Schema 层）** — 本 CLAUDE.md + 配置文件，告诉 LLM wiki 的结构、约定和操作流程。

---

## 项目架构

```
knowableplat/
├── CLAUDE.md                  # 本文件 — 项目规则与上下文
├── llm-wiki.md                # Karpathy LLM-Wiki 原始 idea 文件（参考）
├── test_link.md               # URL 抓取测试链接
├── RSS_test.md                # RSS 订阅源测试链接
├── README.md                  # 用户文档
├── docker-compose.yml         # 全栈部署配置
├── pyproject.toml             # Python 项目配置 (uv)
├── docs/                      # 项目文档（全部中文）
│   ├── architecture.md        # 架构设计文档
│   ├── api.md                 # API 接口文档
│   ├── ingest-pipeline.md     # Ingest 流水线文档
│   ├── query-pipeline.md      # Query 查询流水线文档
│   ├── learning-system.md     # 学习系统文档
│   └── deployment.md          # 部署运维文档
│
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置 & 环境变量
│   │   ├── models/            # 数据模型
│   │   │   ├── knowledge_base.py  # 知识库
│   │   │   ├── source.py      # 原始来源文档
│   │   │   ├── rss_feed.py    # RSS 订阅源
│   │   │   ├── wiki_page.py   # Wiki 页面
│   │   │   ├── entity.py      # 实体（人物、概念、组织）
│   │   │   └── log.py         # 操作日志
│   │   ├── api/               # REST API 路由
│   │   │   ├── knowledge_bases.py  # 知识库 CRUD
│   │   │   ├── sources.py     # 来源 CRUD + URL 抓取
│   │   │   ├── rss.py         # RSS 订阅源 CRUD + 手动触发抓取
│   │   │   ├── wiki.py        # Wiki 浏览/搜索/查询
│   │   │   ├── generate.py    # 跨知识库文档生成
│   │   │   ├── learn.py       # 学习 & 测验
│   │   │   └── auth.py        # 用户认证
│   │   ├── services/          # 业务逻辑
│   │   │   ├── fetcher.py     # URL → 干净 Markdown (Firecrawl/Jina)
│   │   │   ├── rss_fetcher.py # RSS/Atom 订阅源解析 & 定期轮询
│   │   │   ├── ingest.py      # 来源 → wiki 页面 流水线
│   │   │   ├── wiki_engine.py # Wiki 维护（交叉引用、lint、更新）
│   │   │   ├── query.py       # 问题 → 带引用的回答
│   │   │   ├── generate.py    # 跨知识库文档生成
│   │   │   ├── llm.py         # LLM 抽象层 (Anthropic/OpenAI)
│   │   │   └── learning.py    # 间隔重复 & 测题生成
│   │   ├── prompts/           # LLM 提示词模板
│   │   │   ├── ingest_extract.md      # 提取实体、概念、论点
│   │   │   ├── ingest_synthesize.md   # 生成 wiki 页面内容
│   │   │   ├── ingest_crossref.md     # 查找与已有 wiki 的关联
│   │   │   ├── query_answer.md        # 基于 wiki 上下文回答问题
│   │   │   ├── generate_retrieve.md    # 跨知识库知识检索
│   │   │   ├── generate_outline.md     # 生成文档大纲
│   │   │   ├── generate_section.md     # 分章节生成内容
│   │   │   ├── generate_integrate.md   # 整合生成完整文档
│   │   │   ├── lint_contradictions.md # 检测页面间矛盾
│   │   │   ├── learn_quiz.md          # 从 wiki 内容生成测验题
│   │   │   └── learn_flashcard.md     # 生成闪卡
│   │   ├── wiki/              # Wiki 层（按知识库隔离）
│   │   │   └── {kb_slug}/     # 每个知识库独立的 wiki 空间
│   │   │       ├── index.md   # 该知识库的内容目录
│   │   │       ├── log.md     # 该知识库的活动日志
│   │   │       ├── entities/  # 实体页面
│   │   │       ├── concepts/  # 概念/主题页面
│   │   │       ├── comparisons/  # 对比 & 分析页面
│   │   │       └── sources/   # 来源摘要页面
│   │   └── raw/               # 原始来源文档（不可变，按知识库隔离）
│   │       └── {kb_slug}/     # 每个知识库的原始文档
│   │           └── assets/    # 下载的图片
│   ├── tests/
│   ├── alembic/               # 数据库迁移
│   └── alembic.ini
│
├── web/                       # Next.js 网页前端（唯一客户端）
│   ├── package.json
│   ├── src/
│   │   ├── app/               # Next.js App Router 页面
│   │   │   ├── layout.tsx     # 全局布局（侧边栏 + 顶栏）
│   │   │   ├── page.tsx       # 仪表盘首页
│   │   │   ├── wiki/          # Wiki 浏览器（图谱视图、搜索、详情）
│   │   │   │   └── [slug]/    # Wiki 页面详情
│   │   │   ├── sources/       # 来源管理（提交 URL、列表、详情）
│   │   │   ├── learn/         # 学习 & 复习（闪卡、测验、统计）
│   │   │   └── chat/          # 对话查询界面
│   │   ├── components/        # 共享 UI 组件
│   │   │   ├── Sidebar.tsx    # 侧边导航栏
│   │   │   ├── MarkdownRenderer.tsx  # Wiki Markdown 渲染器
│   │   │   ├── GraphView.tsx  # 知识图谱可视化
│   │   │   ├── SearchBar.tsx  # 全局搜索
│   │   │   └── FlashCard.tsx  # 闪卡组件
│   │   └── lib/               # API 客户端、工具函数
│   └── tailwind.config.ts
│
└── scripts/
    ├── seed_demo.py           # 填充演示数据
    └── lint_wiki.py           # Wiki 健康检查脚本
```

---

## 网页端页面设计

### 整体布局
- **左侧：** 知识库选择器（顶部下拉）+ 固定侧边导航栏（Wiki、来源、学习、对话）
- **顶部：** 搜索栏 + 当前知识库名称 + 用户头像
- **主区域：** 根据当前路由显示内容，所有操作限定在当前选中的知识库范围内

### 页面列表

| 页面 | 路由 | 功能 |
|------|------|------|
| 仪表盘 | `/` | 全局概览（知识库列表、各库统计、最近活动） |
| 知识库详情 | `/kb/{kb_slug}` | 单个知识库的仪表盘（来源数、wiki 页数、待复习数） |
| 知识库管理 | `/kb` | 创建/编辑/删除知识库，列表展示 |
| Wiki 浏览 | `/kb/{kb_slug}/wiki` | 当前知识库的 wiki 页面列表，按类型/标签筛选，图谱视图切换 |
| Wiki 详情 | `/kb/{kb_slug}/wiki/[slug]` | 单个 wiki 页面内容、反向链接、相关页面 |
| 来源列表 | `/kb/{kb_slug}/sources` | 当前知识库的来源列表，状态（处理中/完成/失败） |
| 提交来源 | `/kb/{kb_slug}/sources` (modal) | 输入 URL 弹窗，选择目标知识库，显示处理进度 |
| 来源详情 | `/kb/{kb_slug}/sources/[id]` | 原始内容 + 生成的 wiki 页面列表 |
| RSS 管理 | `/kb/{kb_slug}/rss` | 当前知识库的 RSS 订阅源列表、添加/编辑/删除订阅 |
| RSS 详情 | `/kb/{kb_slug}/rss/[id]` | 单个订阅源详情、抓取历史、已归档文章列表 |
| 学习首页 | `/kb/{kb_slug}/learn` | 当前知识库的待复习、学习统计、连续打卡 |
| 闪卡复习 | `/kb/{kb_slug}/learn/review` | 滑动式闪卡，SM-2 评分 |
| 测验 | `/kb/{kb_slug}/learn/quiz/[slug]` | LLM 生成的测验题 |
| 对话查询 | `/kb/{kb_slug}/chat` | 在当前知识库上下文中问答，带 wiki 引用的回答 |
| 图谱视图 | `/kb/{kb_slug}/wiki/graph` | 当前知识库的 wiki 页面关系力导向图 |
| 知识生成 | `/generate` | 跨知识库文档生成（多选知识库、输入主题、生成结构化文档） |
| 生成历史 | `/generate/history` | 已生成文档列表，支持查看/下载/删除 |

### 响应式设计
- 桌面端（>= 1024px）：完整侧边栏 + 宽内容区
- 平板端（768-1023px）：可折叠侧边栏
- 手机浏览器（< 768px）：底部标签栏 + 全屏内容，支持移动端操作

---

## LLM-Wiki 操作流程

### Ingest（摄入）流水线

当用户向某个知识库提交一个 URL：

1. **抓取（Fetch）** — 使用 Firecrawl/Jina Reader 将 URL 转为干净的 Markdown
2. **存储原始内容** — 保存到 `raw/{kb_slug}/` 目录（不可变），在 `sources` 表中记录，关联 `kb_id`
3. **提取（Extract）** — LLM 阅读来源，提取关键实体、概念、论点
4. **撰写摘要页** — 创建 `wiki/{kb_slug}/sources/<slug>.md` 结构化摘要
5. **更新实体页** — 创建或更新 `wiki/{kb_slug}/entities/<entity>.md`
6. **更新概念页** — 创建或更新 `wiki/{kb_slug}/concepts/<topic>.md`
7. **交叉引用** — 将新内容与**同一知识库内**的已有 wiki 页面链接（双向 `[[wikilinks]]`）
8. **更新索引** — 刷新 `wiki/{kb_slug}/index.md` 加入新条目
9. **追加日志** — 向 `wiki/{kb_slug}/log.md` 添加条目：`## [YYYY-MM-DD] ingest | 文章标题`
10. **标记矛盾** — 如果新来源与同一知识库内已有论点矛盾，创建 `wiki/{kb_slug}/comparisons/` 对比页

一个来源可能涉及 10-15 个 wiki 页面。LLM 完成所有交叉引用和维护工作。

### RSS 订阅流水线

除了手动提交 URL，知识库还支持通过 RSS/Atom 订阅源自动摄入内容：

**配置阶段：**
1. **添加订阅源** — 用户为某个知识库配置 RSS 订阅（如安全博客、技术周刊、arXiv 分类等）
2. **设置规则** — 可选配置过滤规则（关键词过滤、作者过滤、分类过滤），只摄入符合条件的文章

**定时轮询阶段（后台定时任务）：**
1. **拉取 Feed** — 按配置的间隔（默认每小时）拉取 RSS/Atom 订阅源，解析出新条目
2. **去重检查** — 对比 `rss_entries` 表中已处理的条目 GUID/URL，跳过已存在的
3. **规则过滤** — 对新条目应用用户配置的过滤规则，丢弃不符合条件的
4. **逐条 Ingest** — 将通过过滤的每篇文章当作普通来源，走完整的 Ingest 流水线：
   - 抓取全文（Firecrawl/Jina）
   - 存储到 `raw/{kb_slug}/`
   - LLM 提取、生成 wiki 页面、交叉引用、更新索引和日志
5. **记录归档** — 在 `rss_entries` 表中记录已处理的条目，避免重复摄入

**用户可在网页端：**
- 查看 RSS 订阅源列表和状态（上次抓取时间、新文章数、失败数）
- 手动触发立即抓取
- 查看每次抓取的归档历史
- 暂停/恢复订阅

### Query（查询）流水线

当用户在某个知识库中提出问题：

1. **读取索引** — LLM 先读 `wiki/{kb_slug}/index.md` 找到相关页面
2. **深入阅读** — 读取**同一知识库内**与问题相关的具体 wiki 页面
3. **综合回答** — 生成带 `[[wikilink]]` 引用的回答
4. **可选：归档回答** — 如果回答有价值（对比、分析），保存为新的 wiki 页面

**好的回答可以回存到 wiki。** 你的探索在知识库中复利积累，和摄入的来源一样。

### Generate（知识生成）流水线

当用户要求生成一篇主题文档时（可跨多个知识库）：

1. **选择知识库** — 用户多选要参考的知识库（如同时选「Web 安全」和「AI 安全」）
2. **输入主题要求** — 用户描述生成需求（如「生成一篇关于 Harness 发展史的文章」）
3. **知识检索** — 系统从所有选中知识库的 wiki 中检索与主题相关的页面：
   - 读取各知识库的 `index.md` 定位相关页面
   - 读取相关 wiki 页面的完整内容
   - 汇总来自不同知识库的知识片段
4. **规划文档结构** — LLM 根据检索到的知识和主题要求，规划文档大纲（章节结构、要点分布）
5. **分段生成** — 按大纲逐章节生成内容，每段引用来源知识库和具体 wiki 页面
6. **汇总整合** — 合并各章节，检查逻辑连贯性，消除重复，统一风格
7. **输出文档** — 生成完整的结构化 Markdown 文档，包含：
   - 标题、摘要、目录
   - 分章节正文（每节标注引用来源：`[来源：知识库名/wiki页面]`）
   - 参考资料列表（列出用到的知识库和 wiki 页面链接）
8. **保存记录** — 生成的文档保存到 `generated_docs` 表，用户可查看/下载历史

**与 Query 的区别：** Query 是单库问答（短回答），Generate 是跨库文档生成（长文输出，有完整结构和引用）。

### Lint（健康检查）

定期审核 wiki 健康状况：
- 页面间的矛盾
- 被新来源取代的过时论点
- 没有入链的孤儿页面
- 被提及但缺少独立页面的重要概念
- 缺失的交叉引用
- 可通过网络搜索填补的数据空白

LLM 擅长建议新的调查问题和新的来源。这让 wiki 在增长过程中保持健康。

### 索引与日志

**`wiki/{kb_slug}/index.md`** — 每个知识库有独立的内容目录。按类别组织，每个页面列出链接、一行摘要、可选元数据（日期、来源数量）。LLM 每次查询先读索引定位相关页面。在中等规模（~100 个来源、~数百页面）下效果很好，无需向量 RAG 基础设施。

**`wiki/{kb_slug}/log.md`** — 每个知识库有独立的活动日志。只追加。统一前缀格式：`## [YYYY-MM-DD] ingest | 文章标题`。可用简单工具解析：`grep "^## \[" wiki/{kb_slug}/log.md | tail -5`。

---

## Wiki 页面格式

每个 wiki 页面遵循以下 frontmatter 结构：

```markdown
---
title: 页面标题
type: source | entity | concept | comparison | answer
created: 2026-05-13
updated: 2026-05-13
sources:
  - source-slug-1
  - source-slug-2
tags: [标签1, 标签2]
---

# 页面标题

## 概要
<!-- 一段综合摘要 -->

## 关键要点
<!-- 从来源中提取的要点列表 -->

## 详细内容
<!-- 完整内容 -->

## 相关
<!-- [[wikilinks]] 到相关页面 -->

## 来源
<!-- 引用回原始来源 -->
```

---

## 数据库设计

### knowledge_bases（知识库表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| name | string, unique | 知识库名称（如「Web 安全」「AI 安全」） |
| slug | string, unique | URL 友好标识符（如 `web-security`） |
| description | text | 知识库描述 |
| icon | string | 图标标识（可选） |
| color | string | 主题色（可选，用于 UI 区分） |
| is_public | boolean | 是否公开（默认 false） |
| source_count | integer | 来源总数（反规范化，定期更新） |
| wiki_page_count | integer | Wiki 页面总数（反规范化） |
| created_at / updated_at | datetime | 创建/更新时间 |

### sources（来源表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| kb_id | UUID, FK | 所属知识库 |
| url | string | 来源 URL（同一知识库内唯一） |
| title | string | 文章标题 |
| raw_content | text | 原始抓取的 Markdown |
| status | enum | pending / processing / completed / failed |
| fetched_at | datetime | 抓取时间 |
| created_at / updated_at | datetime | 创建/更新时间 |

### rss_feeds（RSS 订阅源表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| kb_id | UUID, FK | 所属知识库 |
| name | string | 订阅源名称（如「FreeBuf 安全资讯」） |
| url | string | RSS/Atom 订阅地址 |
| feed_type | enum | rss / atom |
| is_active | boolean | 是否启用（默认 true） |
| poll_interval | integer | 轮询间隔（分钟，默认 60） |
| last_fetched_at | datetime | 上次抓取时间 |
| last_fetch_status | enum | success / partial / failed |
| last_error | text | 最近一次错误信息 |
| total_fetched | integer | 累计抓取条目数（反规范化） |
| filter_keywords | string[] | 关键词过滤（包含这些词才摄入，空=不过滤） |
| filter_authors | string[] | 作者过滤（只摄入指定作者，空=不过滤） |
| filter_categories | string[] | 分类过滤（只摄入指定分类，空=不过滤） |
| created_at / updated_at | datetime | 创建/更新时间 |

### rss_entries（RSS 条目记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| feed_id | UUID, FK | 所属订阅源 |
| kb_id | UUID, FK | 所属知识库 |
| guid | string | RSS 条目唯一标识（用于去重） |
| url | string | 文章原文 URL |
| title | string | 文章标题 |
| published_at | datetime | 文章发布时间 |
| source_id | UUID, FK, nullable | 关联的来源文档（Ingest 完成后填充） |
| status | enum | new / ingesting / completed / filtered / failed |
| fetched_at | datetime | 抓取时间 |

### wiki_pages（Wiki 页面表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| kb_id | UUID, FK | 所属知识库 |
| slug | string | URL 友好标识符（同一知识库内唯一） |
| title | string | 页面标题 |
| type | enum | source / entity / concept / comparison / answer |
| content | text | Markdown 内容 |
| frontmatter | JSON | 解析后的 YAML frontmatter |
| source_ids | UUID[] | 关联的来源文档 |
| outgoing_links | string[] | 本页面链接到的 slug |
| incoming_links | string[] | 链接到本页面的 slug（反规范化） |
| created_at / updated_at | datetime | 创建/更新时间 |

### entities（实体表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| kb_id | UUID, FK | 所属知识库 |
| name | string | 实体名称（同一知识库内唯一） |
| type | enum | person / organization / tool / concept / event |
| aliases | string[] | 别名列表 |
| wiki_page_id | UUID, FK | 关联 wiki 页面 |
| created_at / updated_at | datetime | 创建/更新时间 |

### activity_log（活动日志表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| kb_id | UUID, FK | 所属知识库 |
| action | enum | ingest / query / lint / update |
| target | string | 页面 slug 或来源 URL |
| details | JSON | 操作元数据 |
| created_at | datetime | 创建时间 |

### learning（学习表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| user_id | UUID, FK | 用户 ID |
| wiki_page_id | UUID, FK | 关联 wiki 页面 |
| interval | integer | 距下次复习的天数 |
| ease_factor | float | SM-2 算法参数 |
| repetitions | integer | 重复次数 |
| next_review | date | 下次复习日期 |
| last_reviewed | date | 上次复习日期 |

### generated_docs（生成文档表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID, PK | 主键 |
| user_id | UUID, FK | 用户 ID |
| title | string | 文档标题 |
| topic | text | 用户的原始主题要求 |
| content | text | 生成的 Markdown 文档内容 |
| kb_ids | UUID[] | 引用的知识库 ID 列表 |
| referenced_page_ids | UUID[] | 引用的 wiki 页面 ID 列表 |
| status | enum | generating / completed / failed |
| word_count | integer | 文档字数 |
| token_usage | integer | 消耗的 LLM token 数 |
| created_at | datetime | 创建时间 |

---

## API 设计

### 知识库管理
- `POST /api/knowledge-bases` — 创建知识库（名称、描述、图标、颜色）
- `GET /api/knowledge-bases` — 列出所有知识库（含统计摘要）
- `GET /api/knowledge-bases/{kb_slug}` — 获取知识库详情 + 统计
- `PUT /api/knowledge-bases/{kb_slug}` — 更新知识库信息
- `DELETE /api/knowledge-bases/{kb_slug}` — 删除知识库及全部关联数据

### 来源管理（知识库范围内）
- `POST /api/kb/{kb_slug}/sources` — 向指定知识库提交 URL 进行摄入（异步任务）
- `GET /api/kb/{kb_slug}/sources` — 列出该知识库的所有来源（分页）
- `GET /api/kb/{kb_slug}/sources/{id}` — 获取来源详情 + 原始内容
- `DELETE /api/kb/{kb_slug}/sources/{id}` — 删除来源及关联 wiki 页面

### RSS 订阅管理（知识库范围内）
- `POST /api/kb/{kb_slug}/rss` — 添加 RSS/Atom 订阅源（URL、名称、过滤规则）
- `GET /api/kb/{kb_slug}/rss` — 列出该知识库的所有订阅源（含状态统计）
- `GET /api/kb/{kb_slug}/rss/{id}` — 获取订阅源详情 + 最近抓取条目
- `PUT /api/kb/{kb_slug}/rss/{id}` — 更新订阅源配置（过滤规则、轮询间隔、启用/暂停）
- `DELETE /api/kb/{kb_slug}/rss/{id}` — 删除订阅源（不影响已摄入的内容）
- `POST /api/kb/{kb_slug}/rss/{id}/fetch` — 手动触发立即抓取
- `GET /api/kb/{kb_slug}/rss/{id}/entries` — 获取订阅源的抓取历史（分页）

### Wiki 操作（知识库范围内）
- `GET /api/kb/{kb_slug}/wiki` — 列出该知识库的 wiki 页面（可按类型、标签、搜索过滤）
- `GET /api/kb/{kb_slug}/wiki/{slug}` — 获取 wiki 页面内容 + 反向链接
- `GET /api/kb/{kb_slug}/wiki/graph` — 获取该知识库的链接图谱数据
- `POST /api/kb/{kb_slug}/wiki/query` — 在该知识库上下文中提问
- `POST /api/kb/{kb_slug}/wiki/lint` — 触发该知识库的 wiki 健康检查

### 学习系统（知识库范围内）
- `GET /api/kb/{kb_slug}/learn/due` — 获取该知识库今日待复习页面
- `POST /api/kb/{kb_slug}/learn/review` — 提交复习结果（更新 SM-2 调度）
- `GET /api/kb/{kb_slug}/learn/quiz/{slug}` — 为该知识库的 wiki 页面生成测验题
- `GET /api/kb/{kb_slug}/learn/stats` — 该知识库的学习统计

### 知识生成（跨知识库）
- `POST /api/generate` — 提交生成请求（参数：`kb_ids[]` 知识库列表、`topic` 主题要求，异步任务）
- `GET /api/generate/{id}` — 获取生成任务状态 / 生成结果
- `GET /api/generate` — 列出生成历史（分页）
- `DELETE /api/generate/{id}` — 删除已生成文档

### 认证
- `POST /api/auth/register` — 注册
- `POST /api/auth/login` — 登录
- `GET /api/auth/me` — 当前用户信息

---

## LLM 集成

### 当前模型配置

本平台使用智谱 AI 提供的 Anthropic 兼容接口：

| 配置项 | 环境变量 | 说明 |
|--------|----------|------|
| API 地址 | `ANTHROPIC_BASE_URL` | `https://open.bigmodel.cn/api/anthropic` |
| 认证密钥 | `ANTHROPIC_AUTH_TOKEN` | 通过系统环境变量获取，**禁止硬编码** |
| 模型名称 | `ANTHROPIC_MODEL` | `glm-5.1` |

**所有敏感信息（API 密钥、数据库密码、Redis 密码等）必须通过环境变量或 `.env` 文件注入，代码中绝不出现明文。** 详见下方「硬编码禁令」。

### Provider 抽象

通过统一接口支持多个 LLM 提供商：

```python
class LLMProvider(Protocol):
    async def generate(self, prompt: str, system: str = "") -> str: ...
    async def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
```

默认使用智谱 AI 的 `glm-5.1` 模型（通过 Anthropic 兼容接口调用）。

### Token 管理

- 在 Redis 中缓存 wiki 索引（避免每次查询重新读取）
- 实体提取使用结构化输出（JSON mode）以减少 token 消耗
- 向 LLM 输入上下文时批量合并小页面
- 在活动日志中按来源记录 token 使用量

---

## 学习系统（网页端）

### 间隔重复（SM-2 算法）

在 `backend/app/services/learning.py` 中实现：
1. 用户阅读 wiki 页面 → 页面进入复习队列
2. 从页面内容生成测验（多选 + 简答）
3. 用户作答 → 质量评分（0-5）
4. SM-2 计算下次复习日期、难度因子、重复次数
5. `GET /api/learn/due` 返回待复习页面

### 测验生成

LLM 从 wiki 页面生成题目：
- **多选题** — 概念理解
- **填空题** — 关键事实和定义
- **判断题** — 论点验证
- **简答题** — 综合分析

### 网页端学习流程

1. 进入学习页面 → 查看待复习数量和连续打卡
2. 滑动闪卡式复习（左右滑动，上滑"记住了"，下拉"再看看"）
3. 回答测验题（即时反馈 + 正确答案解释）
4. 学习统计图表（复习量趋势、掌握率、连续打卡）

---

## 开发环境

```bash
# 后端
cd backend
uv venv .venv
.venv\Scripts\activate          # Windows
uv pip install -e ".[dev]"

# 数据库（通过 Docker Desktop）
docker compose up -d postgres redis

# 运行数据库迁移
alembic upgrade head

# 启动后端
uvicorn app.main:app --reload --port 8000

# 网页前端
cd web
npm install
npm run dev                     # http://localhost:3000

# 测试
pytest --cov=app tests/
```

---

## Claude Loop 工作流

**注意：始终先处理已有改进再提出新建议。**

1. **提议** — 如果没有已有的 open issue，先写计划
2. **实现** — 编写代码、测试和文档
3. **验证** — `pytest --cov` 必须通过，新代码覆盖率 >= 80%
4. **提交 & 推送** — 描述性提交信息，推送到 GitHub
5. **学习** — 将新约定记录到本文件
6. **循环** — 进入下一个最高优先级功能

### 规则

- **绝不跳过测试。** 每个功能至少一个测试。详见下方「开发规则」。
- **绝不跳过 lint。** 推送前运行 `ruff check` 和 `ruff format`。
- **绝不跳过文档。** 新增或修改组件后，更新 `docs/` 中对应文档。
- **每个提交一个功能。**
- **每个功能完成后推送。** 测试通过后执行 `git push origin main`。
- **发现新约定时更新本文件。**

---

## Git 约定

- **分支：** 在 `main` 分支上开发（单人项目）
- **远程仓库：** `https://github.com/xvgawa-art/knowablePlat`
- **提交格式：** `feat: 描述` — 前缀：`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- **推送：** 每个功能测试通过后推送

---

## 开发规则

### 测试规则

- **实现功能后，必须编写单元测试。** 测试不是可选项。每个新函数、类或工作流节点都需要测试覆盖。
- **修改现有代码后，检查现有测试是否需要更新。** 如果你改变了核心行为，测试必须反映新行为。如果只是重构而未改变行为，现有测试应不变且仍然通过。
- **拿不准是否需要测试时：** 如果代码包含逻辑（条件判断、循环、错误处理、状态转换），就需要测试。

### 组件复用规则

- **实现新功能前，先检查现有组件能力。** 阅读 `docs/` 中相关文档，了解代码中已有哪些能力可用。
- **修改组件后，更新其文档并审计调用方。**
  1. 更新 `docs/` 中对应的文档文件，反映新的接口或行为
  2. 搜索被修改组件的所有调用点，验证它们是否仍然正常工作
  3. 如果某个调用方的行为会因此改变，更新该调用方及其测试

### 文档规则

- **所有文档必须使用中文编写。** `docs/` 目录下的文档、代码注释、README 等，均须使用中文。代码标识符（变量名、函数名、类名）保持英文不变。

### 硬编码禁令

- **代码中绝不出现明文密钥、密码或配置值。** 所有敏感信息和配置项必须通过环境变量或 `.env` 文件注入，通过 `config.py` 统一读取。
- **不信任任何硬编码。** 端口号、API 地址、数据库名、模型名称、轮询间隔 —— 全部走配置。
- **`.env` 只提供 `.env.example` 模板。** 实际 `.env` 文件在 `.gitignore` 中，不进入版本控制。
- **测试代码同样不允许硬编码真实密钥。** 测试使用 mock 或专门的测试环境变量。

---

## 代码风格

### 后端（Python）

- **Python 3.13** 所有函数必须有 type hints
- **格式化：** `ruff format`（行宽 120）
- **Lint：** `ruff check` — 不得无故使用 `# noqa`
- **命名：** 函数/变量用 snake_case，类用 PascalCase，常量用 UPPER_SNAKE
- **导入顺序：** stdlib → 第三方 → 本地，用 `isort` 排序
- **异步：** 所有 I/O 操作使用 `async/await`（数据库、LLM、HTTP）
- **依赖注入：** 使用 FastAPI 的 `Depends()` 模式
- **错误处理：** 在 `app/exceptions.py` 中定义自定义异常类，通过 exception handler 映射到 HTTP 响应
- **日志：** 生产环境使用 `structlog` JSON 输出
- **测试：** pytest + pytest-asyncio，描述性名称：`test_ingest_url_creates_wiki_pages()`
- **不允许 TODO 注释** — 要么实现，要么创建 GitHub issue

### 前端（Next.js / React）

- **TypeScript 严格模式** — 禁止 `any` 类型
- **格式化：** Prettier（printWidth 120, singleQuote, trailingComma all）
- **Lint：** ESLint + Next.js 配置
- **组件：** 函数组件 + hooks，PascalCase 文件名
- **状态管理：** TanStack Query 管理服务端状态，Zustand 管理客户端状态
- **样式：** Tailwind CSS — 使用工具类，避免自定义 CSS
- **API 客户端：** 从 OpenAPI schema 通过 `openapi-typescript` 生成
- **响应式：** 移动端优先设计，断点：sm(640) / md(768) / lg(1024) / xl(1280)

---

## Lint 规则

### 后端

- **ruff：** line-length 120，目标 Python 3.13
- **禁止裸 except** — 必须指定异常类型
- **禁止 print 语句** — 使用 `structlog` 日志
- **所有函数签名必须有 type hints**
- **测试必须是异步的** — 使用 `pytest-asyncio`

### 硬编码禁令（前后端通用）

- **禁止硬编码任何敏感信息** — API 密钥、数据库密码、Redis 密码、JWT 密钥、第三方服务密钥等，一律通过环境变量或 `.env` 文件注入
- **禁止硬编码配置值** — 端口号、主机地址、数据库名、轮询间隔等配置项，必须从 `config.py` / 环境变量读取，不允许在业务代码中直接写死
- **禁止硬编码 URL** — 外部 API 地址（如 Firecrawl、Jina、LLM API）必须通过配置文件管理
- **`.env` 文件不纳入版本控制** — `.env` 加入 `.gitignore`，只提供 `.env.example` 作为模板
- **违反硬编码禁令的代码不予合并** — 任何包含明文密钥、硬编码配置的代码都必须修改后才能提交

### 前端

- **禁止 `any` 类型** — 使用正确的 TypeScript 类型
- **禁止内联样式** — 使用 Tailwind 工具类
- **禁止直接 `fetch`** — 使用 OpenAPI schema 生成的 API 客户端
- **组件不超过 200 行** — 拆分为更小的组件
- **默认使用 Server Components** — 只在需要时添加 `"use client"`

### Wiki 内容

- **每个知识库独立 wiki 空间** — 不同知识库的页面、实体、来源互不干扰，交叉引用只在同一知识库内进行
- **每个页面都有 frontmatter** — title, type, created, updated, sources, tags
- **Wikilinks 是双向的** — 当页面 A 链接到 B 时，B 的 incoming_links 包含 A
- **来源引用必须** — 每个论点都必须能追溯到原始来源
- **不允许孤儿页面** — 每个页面至少有一个入链
- **每次 ingest 必须有日志条目** — 格式：`## [YYYY-MM-DD] ingest | 标题`

---

## 不确定时规则

- **FastAPI 模式：** 不确定依赖注入、中间件或后台任务时，查阅 [FastAPI 文档](https://fastapi.tiangolo.com/) —— 不要猜测 API 签名。
- **LLM 提示词设计：** 不确定 wiki 操作的提示词结构时，参考 [llm-wiki.md](llm-wiki.md) 中的原则 —— wiki 是一个持久的、可复利的产物。
- **SM-2 算法：** 实现间隔重复时，遵循 [SM-2 原始规范](https://super-memory.com/english/ol/sm2.htm) —— 不要自行发明调度逻辑。
- **URL 抓取：** URL 抓取失败时，尝试备用抓取器（Firecrawl → Jina → 原始 HTTP + readability）。记录失败日志以便调试。
- **RSS 解析：** 使用 `feedparser` 库解析 RSS/Atom 订阅源。不同网站的 RSS 格式差异很大，务必处理缺失字段（作者、发布时间、摘要）。
- **RSS 去重：** 使用条目的 `guid` 字段作为唯一标识（而非 URL，因为 URL 可能变化）。如果 `guid` 缺失，回退到 URL。
- **Wiki 一致性：** 当 wiki 增长超过 ~100 页时，考虑添加搜索引擎（qmd 或 pgvector），而不是仅依赖 `index.md`。

---

## 测试链接

用于验证 Ingest 流水线的在线文档链接（见 `test_link.md`）：

1. `https://www.51cto.com/article/842354.html` — 51CTO 技术文章
2. `https://mp.weixin.qq.com/s/XrF8CtUUqu79HYyWXAPiBg` — 微信公众号文章
3. `https://zhuanlan.zhihu.com/p/2033117550712705501` — 知乎专栏文章

**注意：** 微信公众号和知乎文章可能需要特殊抓取策略（反爬机制）。优先使用 Jina Reader（`https://r.jina.ai/`）作为备选方案。

### RSS 订阅源测试链接

用于验证 RSS 订阅流水线的在线订阅源（见 `RSS_test.md`）：

1. `https://www.v2ex.com/feed/tab/hot.xml` — V2EX 热门话题（RSS 2.0）
2. `https://hnrss.org/frontpage` — Hacker News 首页（RSS 2.0）
3. `https://www.ithome.com/rss/` — IT之家资讯（RSS 2.0）

**注意：** 这些订阅源更新频率高、条目多，适合测试 RSS 轮询、去重和批量 Ingest 的稳定性。建议配置过滤规则控制摄入量。

---

## 优先级 & 路线图

### 第一阶段 — 核心 Ingest & Wiki（MVP）
1. 知识库管理（CRUD + 数据库模型）
2. URL 抓取服务（Firecrawl/Jina）
3. 来源存储（数据库 + 文件系统，按知识库隔离）
4. LLM Ingest 流水线（来源 → wiki 页面，限定知识库范围）
5. Wiki 页面 CRUD API（按知识库范围）
6. `index.md` + `log.md` 自动维护（每个知识库独立）
7. 基础网页 UI：知识库切换、提交 URL、浏览 wiki 页面

### 第二阶段 — RSS 订阅 & 自动摄入
8. RSS/Atom 订阅源管理（CRUD + 过滤规则）
9. RSS 定时轮询服务（后台定时任务 + 去重）
10. RSS 条目 → Ingest 流水线对接
11. RSS 管理网页 UI（订阅源列表、抓取历史、手动触发）

### 第三阶段 — 查询、搜索 & 知识生成
12. 对 wiki 的自然语言查询
13. 跨知识库文档生成（多选知识库 + 主题 → 结构化长文）
14. 全文搜索（PostgreSQL tsvector）
15. 向量搜索（pgvector 语义搜索）
16. 图谱可视化（wiki 页面关系）
17. 回答归档（保存优质回答为 wiki 页面）

### 第四阶段 — 学习系统（网页端）
18. SM-2 间隔重复服务
19. 通过 LLM 生成测验/闪卡
20. 闪卡复习界面（滑动交互）
21. 学习统计 & 连续打卡追踪

### 第五阶段 — 完善 & 扩展
22. Wiki 健康检查（lint）自动化
23. 页面间矛盾检测
24. 批量摄入（多个 URL）
25. 浏览器扩展（快速保存文章）
26. Obsidian 兼容导出
27. 多用户支持

---

## 关键参考

- [Karpathy LLM-Wiki 原始模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — 本项目的核心灵感来源
- [Firecrawl API](https://docs.firecrawl.dev/) — URL 转 Markdown
- [Jina Reader API](https://jina.ai/reader/) — 备选 URL 转 Markdown
- [SM-2 间隔重复算法](https://super-memory.com/english/ol/sm2.htm)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Tailwind CSS](https://tailwindcss.com/)
- [feedparser](https://feedparser.readthedocs.io/) — RSS/Atom 解析库
- [APScheduler](https://apscheduler.readthedocs.io/) — Python 定时任务调度

---

## 运维须知

- **原始来源不可变** — 初始抓取后绝不修改 `raw/` 中的文件
- **Wiki 归 LLM 所有** — LLM 编写和维护所有 wiki 内容；用户只负责指导和审阅
- **异步摄入** — URL 处理和 RSS 条目处理都是后台任务（通过 FastAPI BackgroundTasks + APScheduler 定时任务）。前端轮询状态。
- **RSS 轮询** — 后台定时任务按订阅源配置的间隔自动拉取。支持手动触发。轮询失败不阻塞其他订阅源。
- **Token 预算** — 按来源记录 LLM token 使用量。单个来源超过 50K token 时告警。
- **备份** — wiki 就是 Markdown 文件 + 数据库。wiki 文件通过 Git 版本控制提供历史。
