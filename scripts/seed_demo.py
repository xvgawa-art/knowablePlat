"""填充演示数据脚本。

用法：cd backend && python -m scripts.seed_demo
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import async_sessionmaker
from app.models.knowledge_base import KbType, KnowledgeBase
from app.models.notification import Notification, TriggerType
from app.models.source import Source, SourceStatus
from app.models.wiki_page import WikiPage, WikiPageType


async def seed() -> None:
    async with async_sessionmaker() as session:
        async with session.begin():
            # 知识库
            kb = KnowledgeBase(
                name="Web 安全入门",
                slug="web-security",
                description="Web 安全基础知识库，涵盖 XSS、CSRF、SQL 注入等常见漏洞",
                kb_type=KbType.knowledge,
                is_system=False,
                is_public=True,
            )
            session.add(kb)
            await session.flush()

            # 来源
            sources = [
                Source(
                    kb_id=kb.id,
                    url="https://example.com/xss-guide",
                    title="XSS 攻击全面指南",
                    raw_content="# XSS 攻击全面指南\n\n跨站脚本攻击（XSS）是一种常见的 Web 安全漏洞...",
                    status=SourceStatus.completed,
                ),
                Source(
                    kb_id=kb.id,
                    url="https://example.com/csrf-explained",
                    title="CSRF 攻击原理与防御",
                    raw_content="# CSRF 攻击原理与防御\n\n跨站请求伪造（CSRF）是一种利用用户已登录身份发起恶意请求的攻击方式...",
                    status=SourceStatus.completed,
                ),
                Source(
                    kb_id=kb.id,
                    url="https://example.com/sql-injection",
                    title="SQL 注入攻击与防御",
                    raw_content="# SQL 注入攻击与防御\n\nSQL 注入是通过在输入中嵌入恶意 SQL 代码来攻击数据库的技术...",
                    status=SourceStatus.completed,
                ),
            ]
            for s in sources:
                session.add(s)
            await session.flush()

            # Wiki 页面
            pages = [
                WikiPage(
                    kb_id=kb.id,
                    slug="xss-attack-guide",
                    title="XSS 攻击全面指南",
                    page_type=WikiPageType.source,
                    content=(
                        "# XSS 攻击全面指南\n\n"
                        "## 概要\n\n"
                        "跨站脚本攻击（XSS）是一种常见的 Web 安全漏洞，攻击者通过在网页中注入恶意脚本来攻击用户。\n\n"
                        "## 关键要点\n\n"
                        "- 反射型 XSS：恶意脚本通过 URL 参数注入\n"
                        "- 存储型 XSS：恶意脚本存储在服务器数据库中\n"
                        "- DOM 型 XSS：通过 DOM 操作注入\n\n"
                        "## 相关\n\n"
                        "- [[csrf-explained|CSRF 攻击原理]]\n"
                        "- [[web-security-overview|Web 安全概览]]\n"
                    ),
                    source_ids=[str(sources[0].id)],
                    outgoing_links=["csrf-explained", "web-security-overview"],
                    incoming_links=[],
                ),
                WikiPage(
                    kb_id=kb.id,
                    slug="csrf-explained",
                    title="CSRF 攻击原理与防御",
                    page_type=WikiPageType.source,
                    content=(
                        "# CSRF 攻击原理与防御\n\n"
                        "## 概要\n\n"
                        "跨站请求伪造（CSRF）利用用户已登录的身份发起恶意请求。\n\n"
                        "## 防御措施\n\n"
                        "- CSRF Token\n"
                        "- SameSite Cookie\n"
                        "- 验证 Referer 头\n\n"
                        "## 相关\n\n"
                        "- [[xss-attack-guide|XSS 攻击指南]]\n"
                    ),
                    source_ids=[str(sources[1].id)],
                    outgoing_links=["xss-attack-guide"],
                    incoming_links=["xss-attack-guide"],
                ),
                WikiPage(
                    kb_id=kb.id,
                    slug="web-security-overview",
                    title="Web 安全概览",
                    page_type=WikiPageType.concept,
                    content=(
                        "# Web 安全概览\n\n"
                        "## 概要\n\n"
                        "Web 安全是保护 Web 应用免受恶意攻击的实践。\n\n"
                        "## 常见威胁\n\n"
                        "- [[xss-attack-guide|XSS]]\n"
                        "- [[csrf-explained|CSRF]]\n"
                        "- SQL 注入\n"
                    ),
                    source_ids=[str(sources[0].id), str(sources[1].id)],
                    outgoing_links=["xss-attack-guide", "csrf-explained"],
                    incoming_links=["xss-attack-guide"],
                ),
                WikiPage(
                    kb_id=kb.id,
                    slug="index",
                    title="Web 安全入门 目录",
                    page_type=WikiPageType.concept,
                    content=(
                        "# Web 安全入门\n\n"
                        "## 来源摘要\n\n"
                        "- [[xss-attack-guide|XSS 攻击全面指南]]\n"
                        "- [[csrf-explained|CSRF 攻击原理与防御]]\n\n"
                        "## 概念\n\n"
                        "- [[web-security-overview|Web 安全概览]]\n"
                    ),
                    source_ids=[],
                    outgoing_links=[],
                    incoming_links=[],
                ),
            ]
            for p in pages:
                session.add(p)
            await session.flush()

            # 通知
            notifications = [
                Notification(
                    kb_id=kb.id,
                    source_id=sources[0].id,
                    trigger_type=TriggerType.manual,
                    title="新知识入库：XSS 攻击全面指南",
                    summary="本文全面介绍了 XSS 攻击的三种类型：反射型、存储型和 DOM 型，以及相应的防御措施。",
                    related_points=[
                        {
                            "wiki_page_slug": "web-security-overview",
                            "title": "Web 安全概览",
                            "relation_desc": "XSS 是 Web 安全的核心主题之一",
                        }
                    ],
                    is_read=False,
                ),
                Notification(
                    kb_id=kb.id,
                    source_id=sources[1].id,
                    trigger_type=TriggerType.manual,
                    title="新知识入库：CSRF 攻击原理与防御",
                    summary="本文详细讲解了 CSRF 攻击的原理和三种主要防御手段。",
                    related_points=[
                        {
                            "wiki_page_slug": "xss-attack-guide",
                            "title": "XSS 攻击全面指南",
                            "relation_desc": "CSRF 和 XSS 经常一起出现，需要同时防御",
                        }
                    ],
                    is_read=False,
                ),
            ]
            for n in notifications:
                session.add(n)

    print("演示数据已填充完毕：")
    print(f"  知识库: {kb.name} ({kb.slug})")
    print(f"  来源: {len(sources)} 条")
    print(f"  Wiki 页面: {len(pages)} 个")
    print(f"  通知: {len(notifications)} 条")


if __name__ == "__main__":
    asyncio.run(seed())
