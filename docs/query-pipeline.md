# Query 查询流水线文档

## 概述

Query 流水线让用户在知识库的 wiki 上下文中提问，获得带引用的回答。

## 流程

```
用户提问 → LLM 定位相关页面 → 读取页面内容 → 综合回答（带引用）
```

## 详细步骤

### 1. 定位相关页面

- **输入**: 用户问题 + `index.md` 内容
- **方式**: LLM 读取知识库索引，识别与问题相关的页面 slug
- **实现**: `services/query.py` 中的 `page_finder_prompt`

### 2. 读取页面内容

- 从数据库读取相关页面的完整内容
- 每个页面截取前 2000 字符
- 最多读取 5 个相关页面
- 如果没有找到相关页面，使用索引内容作为上下文

### 3. 生成回答

- **提示词**: `prompts/query_answer.md`
- **输入**: 知识库上下文 + 用户问题
- **输出**: 带 [[wikilinks]] 引用的结构化回答
- **返回**: (answer, referenced_page_slugs)

## 与 Generate 的区别

| 维度 | Query | Generate |
|------|-------|----------|
| 范围 | 单知识库 | 跨知识库 |
| 输出 | 短回答 | 长文（完整结构） |
| 引用 | [[wikilinks]] | [来源：知识库名/wiki页面] |
| 流程 | 直接问答 | 检索→大纲→分段→整合 |

## 搜索能力

### 全文搜索 (tsvector)

- 列出 wiki 页面时支持 `?search=` 参数
- 使用 PostgreSQL tsvector 全文搜索
- GIN 索引加速

### 语义搜索 (pgvector)

- `POST /api/kb/{kb_slug}/wiki/semantic-search`
- 使用智谱AI embedding API 生成查询向量
- pgvector 进行向量相似度搜索
- 适合语义理解型查询

## API

```
POST /api/kb/{kb_slug}/wiki/query
Body: { "question": "什么是 XSS？" }
Response: { "answer": "...", "referenced_pages": ["xss-attack", "web-security"] }
```
