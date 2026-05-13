import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity, EntityType
from app.models.knowledge_base import KbType, KnowledgeBase
from app.models.log import ActionEnum, ActivityLog
from app.models.notification import Notification, TriggerType
from app.models.source import Source, SourceStatus
from app.models.wiki_page import WikiPage, WikiPageType


async def test_create_knowledge_base(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    result = await db_session.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb.id))
    found = result.scalar_one()
    assert found.name == kb.name
    assert found.slug == kb.slug
    assert found.kb_type == KbType.knowledge
    assert found.is_system is False
    assert found.source_count == 0
    assert found.wiki_page_count == 0


async def test_create_tool_arsenal_kb(db_session: AsyncSession) -> None:
    kb_id = uuid.uuid4()
    kb = KnowledgeBase(
        id=kb_id,
        name=f"工具装备-{uuid.uuid4().hex[:4]}",
        slug=f"tool-arsenal-{uuid.uuid4().hex[:8]}",
        kb_type=KbType.tool_arsenal,
        is_system=True,
    )
    db_session.add(kb)
    await db_session.commit()

    result = await db_session.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    found = result.scalar_one()
    assert found.kb_type == KbType.tool_arsenal
    assert found.is_system is True


async def test_create_source(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    source = Source(
        id=uuid.uuid4(),
        kb_id=kb.id,
        url="https://example.com/article",
        title="Test Article",
    )
    db_session.add(source)
    await db_session.commit()

    result = await db_session.execute(select(Source).where(Source.id == source.id))
    found = result.scalar_one()
    assert found.url == "https://example.com/article"
    assert found.status == SourceStatus.pending
    assert found.token_usage == 0


async def test_create_wiki_page(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    page = WikiPage(
        id=uuid.uuid4(),
        kb_id=kb.id,
        slug="test-page",
        title="Test Page",
        page_type=WikiPageType.concept,
        content="# Hello\nWorld",
        frontmatter={"tags": ["test"]},
        outgoing_links=["other-page"],
        incoming_links=[],
    )
    db_session.add(page)
    await db_session.commit()

    result = await db_session.execute(select(WikiPage).where(WikiPage.id == page.id))
    found = result.scalar_one()
    assert found.slug == "test-page"
    assert found.page_type == WikiPageType.concept
    assert found.frontmatter["tags"] == ["test"]
    assert found.outgoing_links == ["other-page"]


async def test_create_entity(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    page = WikiPage(
        id=uuid.uuid4(),
        kb_id=kb.id,
        slug="entity-page",
        title="Entity Page",
        page_type=WikiPageType.entity,
    )
    db_session.add(page)
    await db_session.commit()

    entity = Entity(
        id=uuid.uuid4(),
        kb_id=kb.id,
        name="Test Person",
        entity_type=EntityType.person,
        aliases=["TP"],
        wiki_page_id=page.id,
    )
    db_session.add(entity)
    await db_session.commit()

    result = await db_session.execute(select(Entity).where(Entity.id == entity.id))
    found = result.scalar_one()
    assert found.name == "Test Person"
    assert found.entity_type == EntityType.person
    assert found.aliases == ["TP"]
    assert found.wiki_page_id == page.id


async def test_create_activity_log(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    log = ActivityLog(
        id=uuid.uuid4(),
        kb_id=kb.id,
        action=ActionEnum.ingest,
        target="test-page",
        details={"source_url": "https://example.com"},
    )
    db_session.add(log)
    await db_session.commit()

    result = await db_session.execute(select(ActivityLog).where(ActivityLog.id == log.id))
    found = result.scalar_one()
    assert found.action == ActionEnum.ingest
    assert found.target == "test-page"
    assert found.details["source_url"] == "https://example.com"


async def test_create_notification(db_session: AsyncSession, kb: KnowledgeBase) -> None:
    source = Source(
        id=uuid.uuid4(),
        kb_id=kb.id,
        url="https://example.com/notif-test",
        title="Notif Test",
    )
    db_session.add(source)
    await db_session.commit()

    notif = Notification(
        id=uuid.uuid4(),
        kb_id=kb.id,
        source_id=source.id,
        trigger_type=TriggerType.manual,
        title="新知识已添加",
        summary="添加了一篇关于测试的文章",
        related_points=[{"title": "测试概念", "slug": "test-concept"}],
    )
    db_session.add(notif)
    await db_session.commit()

    result = await db_session.execute(select(Notification).where(Notification.id == notif.id))
    found = result.scalar_one()
    assert found.trigger_type == TriggerType.manual
    assert found.is_read is False
    assert len(found.related_points) == 1


def test_wiki_page_types() -> None:
    assert WikiPageType.tool.value == "tool"
    assert WikiPageType.tool_category.value == "tool_category"


def test_entity_types() -> None:
    assert EntityType.organization.value == "organization"
    assert EntityType.event.value == "event"


async def test_source_status_values() -> None:
    assert SourceStatus.pending.value == "pending"
    assert SourceStatus.processing.value == "processing"
    assert SourceStatus.completed.value == "completed"
    assert SourceStatus.failed.value == "failed"
