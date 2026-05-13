# API 接口文档

## 基础信息

- **Base URL**: `/api`
- **认证方式**: JWT Bearer Token（部分端点可选）
- **内容类型**: `application/json`

## 认证

### POST /api/auth/register
注册新用户。

**请求体**:
```json
{ "email": "user@example.com", "username": "user", "password": "password123" }
```

### POST /api/auth/login
登录获取 JWT。

**请求体**:
```json
{ "email": "user@example.com", "password": "password123" }
```

**响应**:
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### GET /api/auth/me
获取当前用户信息。需要认证。

## 健康检查

### GET /api/health
返回服务状态。

**响应**: `{ "status": "ok" }`

## 知识库管理

### POST /api/knowledge-bases
创建知识库。可选认证（认证后关联用户）。

**请求体**: `{ "name": "知识库名称", "slug": "kb-slug", "description": "描述" }`

### GET /api/knowledge-bases
列出知识库。认证后返回用户可见的知识库。

### GET /api/knowledge-bases/{kb_slug}
获取知识库详情。

### PUT /api/knowledge-bases/{kb_slug}
更新知识库。需要认证 + 所有权。系统内置知识库不可修改。

### DELETE /api/knowledge-bases/{kb_slug}
删除知识库。需要认证 + 所有权。系统内置知识库返回 403。

## 来源管理

### POST /api/kb/{kb_slug}/sources
向知识库提交 URL。后台异步处理。

### POST /api/kb/{kb_slug}/sources/batch
批量提交 URL。自动去重。

**请求体**: `{ "urls": ["url1", "url2"] }`

### GET /api/kb/{kb_slug}/sources
列出来源（分页）。

### GET /api/kb/{kb_slug}/sources/{id}
获取来源详情 + 原始内容。

### DELETE /api/kb/{kb_slug}/sources/{id}
删除来源。

## Wiki 操作

### GET /api/kb/{kb_slug}/wiki
列出 wiki 页面。支持 `?search=` 搜索、`?page_type=` 类型过滤。

### GET /api/kb/{kb_slug}/wiki/{slug}
获取 wiki 页面内容。

### GET /api/kb/{kb_slug}/wiki/graph
获取页面关系图谱数据。

### GET /api/kb/{kb_slug}/wiki/log
获取活动日志。

### GET /api/kb/{kb_slug}/wiki/export
导出 wiki 为 ZIP 文件。

### POST /api/kb/{kb_slug}/wiki/query
在知识库上下文中提问。

**请求体**: `{ "question": "什么是 XSS？" }`

### POST /api/kb/{kb_slug}/wiki/semantic-search
语义向量搜索。

**请求体**: `{ "query": "跨站脚本攻击", "limit": 10 }`

### POST /api/kb/{kb_slug}/wiki/lint
触发 wiki 健康检查。

### DELETE /api/kb/{kb_slug}/wiki/{slug}
删除 wiki 页面（同步清理关联和磁盘文件）。

## RSS 订阅管理

### POST /api/kb/{kb_slug}/rss
添加 RSS 订阅源。

### GET /api/kb/{kb_slug}/rss
列出订阅源。

### GET /api/kb/{kb_slug}/rss/{id}
获取订阅源详情。

### PUT /api/kb/{kb_slug}/rss/{id}
更新订阅源配置。

### DELETE /api/kb/{kb_slug}/rss/{id}
删除订阅源。

### POST /api/kb/{kb_slug}/rss/{id}/fetch
手动触发抓取。

### GET /api/kb/{kb_slug}/rss/{id}/entries
获取抓取历史。

## 知识生成

### POST /api/generate
提交跨知识库文档生成请求（异步）。

**请求体**: `{ "kb_ids": ["uuid1", "uuid2"], "topic": "主题要求" }`

### GET /api/generate
列出生成历史。

### GET /api/generate/{id}
获取生成任务状态/结果。

### DELETE /api/generate/{id}
删除已生成文档。

## 通知

### GET /api/notifications
获取通知列表。支持 `?unread=true`、`?kb_id=` 过滤。

### GET /api/notifications/unread-count
获取未读数量。

### GET /api/notifications/{id}
获取通知详情。

### PUT /api/notifications/{id}/read
标记已读。

### PUT /api/notifications/read-all
全部标记已读。支持 `?kb_id=` 按知识库。
