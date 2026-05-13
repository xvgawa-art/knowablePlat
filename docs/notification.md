# 知识新增通知文档

## 概述

每当知识库有新知识入库（手动提交 URL 或 RSS 推送），系统自动生成知识新增通知。

## 触发时机

- **手动提交 URL**: Ingest 流水线完成后自动触发
- **RSS 推送**: RSS 条目走完 Ingest 流水线后自动触发

## 通知内容

通知包含两部分：

1. **知识总结** — LLM 对新入库文档核心内容的精炼总结（3-5 句话）
2. **关联知识点** — 与已有 wiki 页面的关联，每项附带可跳转链接

```json
{
  "title": "新知识入库：文章标题",
  "summary": "本文主要讲述了...",
  "related_points": [
    {
      "wiki_page_slug": "xss-attack",
      "title": "XSS 攻击防护",
      "relation_desc": "本文提到的新型 XSS 变种与已有知识互补"
    }
  ]
}
```

## 生成流程

### 1. 收集上下文

- 读取新来源的标题和摘要
- 收集知识库中已有 wiki 页面列表（最多 20 个）

### 2. LLM 生成

- **提示词**: `prompts/ingest_notify.md`
- **输入**: 来源标题 + 摘要 + 已有页面列表
- **输出**: JSON 格式的通知内容

### 3. 存储

- 写入 `notifications` 表
- 关联 `kb_id` 和 `source_id`
- `is_read = false`

## API

### 获取通知列表
```
GET /api/notifications?unread=true&kb_id=uuid&offset=0&limit=20
```

### 获取未读数量
```
GET /api/notifications/unread-count
Response: { "unread_count": 5 }
```

### 标记已读
```
PUT /api/notifications/{id}/read
```

### 全部标记已读
```
PUT /api/notifications/read-all?kb_id=uuid
```

## 前端展示

- **顶栏**: NotificationBadge 组件显示未读数红色角标
- **侧边栏**: 通知链接显示未读数量
- **通知中心页面**: `/notifications` — 完整通知列表
- **通知详情**: 查看完整总结 + 关联知识点（带跳转链接）

## 自动轮询

前端通过 TanStack Query 每 30 秒轮询 `GET /api/notifications/unread-count`，更新角标显示。多个组件共享同一 queryKey，TanStack Query 自动去重。
