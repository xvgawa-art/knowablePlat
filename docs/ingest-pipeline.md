# Ingest 流水线文档

## 概述

Ingest 流水线将原始来源文档转化为结构化的 wiki 页面。这是平台的核心功能。

## 流程图

```
URL 提交 → 抓取 → 存储原始内容 → LLM 提取 → 撰写 Wiki 页面
                                         ↓
                              创建实体页 → 创建概念页 → 交叉引用
                                                        ↓
                                          更新索引 → 追加日志 → 生成通知
```

## 详细步骤

### 1. 抓取 (Fetch)

- **入口**: `POST /api/kb/{kb_slug}/sources`
- **实现**: `services/fetcher.py`
- **方式**: Jina Reader (`https://r.jina.ai/`)
- **输出**: 干净的 Markdown 文本
- **存储**: `raw/{kb_slug}/{source_id}.md`

### 2. 提取 (Extract)

- **提示词**: `prompts/ingest_extract.md`
- **输入**: 原始 Markdown（截取前 8000 字符）
- **输出**: JSON 格式的结构化信息：
  - `title`: 文章标题
  - `summary`: 摘要
  - `key_points`: 关键要点列表
  - `entities`: 实体列表（名称 + 类型）
  - `topics`: 主题标签

### 3. 撰写摘要页

- **提示词**: `prompts/ingest_synthesize.md`
- **输入**: 提取结果 + 已有页面列表（用于上下文关联）
- **输出**: 结构化 Markdown wiki 页面
- **存储**: `wiki/{kb_slug}/{source_slug}.md`
- **类型**: `WikiPageType.source`

### 4. 创建实体页

- 从提取结果中的 `entities` 列表创建实体
- 每个实体创建对应的 wiki 页面（`WikiPageType.entity`）
- 同时在 `entities` 表中记录实体信息

### 5. 创建概念页

- 从提取结果中的 `topics` 列表创建概念页
- 如果概念已存在，更新其 incoming_links
- **类型**: `WikiPageType.concept`

### 6. 交叉引用

- **提示词**: `prompts/ingest_crossref.md`
- **输入**: 新页面内容 + 已有页面列表
- **输出**: 应该互相链接的页面 slug 列表
- **操作**: 更新 outgoing_links 和 incoming_links（双向）

### 7. 更新索引

- 重新生成 `wiki/{kb_slug}/index.md`
- 按页面类型分组列出所有页面
- 同时更新数据库中的 index 页面

### 8. 追加日志

- 向 `wiki/{kb_slug}/log.md` 追加条目
- 格式: `## [YYYY-MM-DD] ingest | 文章标题`

### 9. 生成通知

- **提示词**: `prompts/ingest_notify.md`
- **输出**: 文档知识总结 + 关联知识点列表
- **存储**: `notifications` 表

## 工具装备库专用流程

当知识库类型为 `tool_arsenal` 时，使用专用工具提取流程：

1. **工具信息提取** — `prompts/tool_extract.md`
2. **工具分类** — `prompts/tool_categorize.md`
3. **工具页面生成** — `prompts/tool_recommend.md`
4. **分类页面创建/更新**
5. **同类工具交叉引用**

详见 CLAUDE.md 中的 Tool Arsenal 流水线章节。

## 文件系统持久化

Ingest 流水线中的每一步都会同步写入磁盘：

| 数据 | 文件路径 | 说明 |
|------|----------|------|
| 原始内容 | `raw/{kb_slug}/{source_id}.md` | 不可变 |
| Wiki 页面 | `wiki/{kb_slug}/{slug}.md` | LLM 可修改 |
| 知识库索引 | `wiki/{kb_slug}/index.md` | 每次更新 |
| 活动日志 | `wiki/{kb_slug}/log.md` | 只追加 |

## 异步处理

Ingest 流程通过 FastAPI BackgroundTasks 异步执行：

1. API 端点创建 source 记录，状态设为 `processing`
2. BackgroundTask 执行 `_ingest_source()`
3. 完成后状态更新为 `completed` 或 `failed`

前端可通过 `GET /api/kb/{kb_slug}/sources/{id}` 轮询状态。
