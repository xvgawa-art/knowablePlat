# 部署运维文档

## 开发环境

### 前置条件

- Docker Desktop（用于 PostgreSQL 和 Redis）
- Python 3.13 + uv
- Node.js 18+

### 启动步骤

```bash
# 1. 启动数据库和缓存
docker compose up -d postgres redis

# 2. 后端设置
cd backend
uv venv .venv
.venv\Scripts\activate          # Windows
uv pip install -e ".[dev]"

# 3. 运行数据库迁移
alembic upgrade head

# 4. 启动后端
uvicorn app.main:app --reload --port 8000

# 5. 前端设置（另一个终端）
cd web
npm install
npm run dev                     # http://localhost:5173
```

### 环境变量

在项目根目录创建 `.env` 文件：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://knowableplat:knowableplat@localhost:5432/knowableplat

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM（智谱AI）
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
ANTHROPIC_AUTH_TOKEN=your-token-here
ANTHROPIC_MODEL=glm-5.1

# JWT
JWT_SECRET=your-secret-key-here

# URL 抓取
JINA_READER_URL=https://r.jina.ai/
```

## Docker 部署

### docker-compose.yml

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: knowableplat
      POSTGRES_USER: knowableplat
      POSTGRES_PASSWORD: knowableplat
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 生产部署

### 构建

```bash
# 前端构建
cd web && npm run build    # 输出到 web/dist/

# 后端由 FastAPI 托管前端静态文件
# /api/* 走 API，其余走 SPA
```

### 运行

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回退一步
alembic downgrade -1
```

## 测试

```bash
# 运行全部测试
pytest --cov=app tests/

# 运行特定测试
pytest tests/test_filesystem.py -v

# 代码检查
ruff check app/ tests/
ruff format app/ tests/
```

## 日志

生产环境使用 structlog JSON 输出：

```json
{"event": "ingest_completed", "source_id": "...", "title": "...", "level": "info", "timestamp": "..."}
```

## 备份策略

### Wiki 文件

- `wiki/` 和 `raw/` 目录下的 Markdown 文件通过 Git 版本控制
- 每次提交自动保存历史

### 数据库

- PostgreSQL 定期备份（pg_dump）
- 建议每日备份，保留 7 天

## 监控指标

- 来源处理状态（pending / processing / completed / failed）
- Token 使用量（per source, per generated doc）
- RSS 抓取成功率
- Wiki 页面数量和健康度

## 故障处理

### URL 抓取失败

1. 检查网络连通性
2. 尝试备用抓取器（Jina Reader）
3. 查看 source 记录中的 status 和错误信息

### LLM 调用失败

1. 检查 ANTHROPIC_AUTH_TOKEN 是否有效
2. 检查 API 额度
3. 查看 token_usage 记录是否超限

### 数据库连接失败

1. 检查 PostgreSQL 容器状态：`docker compose ps`
2. 检查 DATABASE_URL 配置
3. 检查连接池状态
