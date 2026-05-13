import uuid

import pytest

from app.models.entity import Entity, EntityType
from app.models.knowledge_base import KbType, KnowledgeBase
from app.models.notification import Notification, TriggerType
from app.models.rss_entry import EntryStatus, RssEntry
from app.models.rss_feed import FeedType, RssFeed
from app.models.source import SourceStatus
from app.models.wiki_page import WikiPageType
from app.repositories.entity import EntityRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.notification import NotificationRepository
from app.repositories.rss_entry import RssEntryRepository
from app.repositories.rss_feed import RssFeedRepository
from app.repositories.source import SourceRepository
from app.repositories.wiki_page import WikiPageRepository


@pytest.fixture
async def kb_repo(db_session):
    return KnowledgeBaseRepository(db_session)


@pytest.fixture
async def source_repo(db_session):
    return SourceRepository(db_session)


@pytest.fixture
async def wiki_repo(db_session):
    return WikiPageRepository(db_session)


@pytest.fixture
async def entity_repo(db_session):
    return EntityRepository(db_session)


@pytest.fixture
async def notification_repo(db_session):
    return NotificationRepository(db_session)


@pytest.fixture
async def rss_feed_repo(db_session):
    return RssFeedRepository(db_session)


@pytest.fixture
async def rss_entry_repo(db_session):
    return RssEntryRepository(db_session)


@pytest.fixture
async def test_kb(db_session):
    kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=f"repo-test-{uuid.uuid4().hex[:8]}",
        slug=f"repo-test-{uuid.uuid4().hex[:8]}",
        description="repo test kb",
    )
    db_session.add(kb)
    await db_session.commit()
    return kb


# ── KnowledgeBaseRepository ──


async def test_kb_get_by_slug(kb_repo, test_kb):
    found = await kb_repo.get_by_slug(test_kb.slug)
    assert found is not None
    assert found.id == test_kb.id


async def test_kb_get_by_slug_not_found(kb_repo):
    found = await kb_repo.get_by_slug("nonexistent-slug")
    assert found is None


async def test_kb_ensure_tool_arsenal_creates(kb_repo, db_session):
    kb = await kb_repo.ensure_tool_arsenal()
    await db_session.commit()
    assert kb.slug == "tool-arsenal"
    assert kb.kb_type == KbType.tool_arsenal
    assert kb.is_system is True


async def test_kb_ensure_tool_arsenal_idempotent(kb_repo, db_session):
    kb1 = await kb_repo.ensure_tool_arsenal()
    await db_session.commit()
    kb2 = await kb_repo.ensure_tool_arsenal()
    assert kb1.id == kb2.id


async def test_kb_list_all_returns_records(kb_repo):
    kbs = await kb_repo.list_all()
    assert isinstance(kbs, list)
    assert len(kbs) > 0


async def test_kb_list_by_user(kb_repo, db_session, user):
    kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=f"user-kb-{uuid.uuid4().hex[:8]}",
        slug=f"user-kb-{uuid.uuid4().hex[:8]}",
        user_id=user.id,
    )
    db_session.add(kb)
    await db_session.commit()

    result = await kb_repo.list_by_user(user.id)
    assert isinstance(result, list)
    assert any(k.is_system for k in result)


async def test_kb_refresh_counts(kb_repo, source_repo, wiki_repo, test_kb, db_session):
    await source_repo.create(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        url=f"https://example.com/refresh-{uuid.uuid4().hex[:6]}",
        title="S1", status=SourceStatus.pending,
    )
    await wiki_repo.create(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        slug=f"refresh-wiki-{uuid.uuid4().hex[:6]}", title="W1",
        page_type=WikiPageType.concept, content="c",
    )
    await db_session.commit()

    await kb_repo.refresh_counts(str(test_kb.id))
    await db_session.commit()

    kb = await kb_repo.get_by_id(str(test_kb.id))
    assert kb is not None
    assert kb.source_count >= 1
    assert kb.wiki_page_count >= 1


# ── SourceRepository ──


async def test_source_create_and_get(source_repo, test_kb, db_session):
    source = await source_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        url="https://example.com/test-article",
        title="Test Article",
        status=SourceStatus.pending,
    )
    await db_session.commit()

    found = await source_repo.get_by_id(source.id)
    assert found is not None
    assert found.title == "Test Article"
    assert found.url == "https://example.com/test-article"


async def test_source_get_by_url(source_repo, test_kb, db_session):
    url = "https://example.com/unique-url"
    await source_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        url=url,
        title="Article",
        status=SourceStatus.pending,
    )
    await db_session.commit()

    found = await source_repo.get_by_url(test_kb.id, url)
    assert found is not None
    assert found.url == url


async def test_source_get_by_url_not_found(source_repo, test_kb):
    found = await source_repo.get_by_url(test_kb.id, "https://nope.example.com")
    assert found is None


async def test_source_list_by_kb(source_repo, test_kb, db_session):
    for i in range(3):
        await source_repo.create(
            id=uuid.uuid4(),
            kb_id=str(test_kb.id),
            url=f"https://example.com/article-{i}",
            title=f"Article {i}",
            status=SourceStatus.pending,
        )
    await db_session.commit()

    sources = await source_repo.list_by_kb(test_kb.id)
    assert len(sources) >= 3


# ── WikiPageRepository ──


async def test_wiki_create_and_get(wiki_repo, test_kb, db_session):
    page = await wiki_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        slug="test-wiki-page",
        title="Test Wiki Page",
        page_type=WikiPageType.concept,
        content="Some content here",
    )
    await db_session.commit()

    found = await wiki_repo.get_by_id(page.id)
    assert found is not None
    assert found.title == "Test Wiki Page"
    assert found.slug == "test-wiki-page"


async def test_wiki_get_by_slug(wiki_repo, test_kb, db_session):
    await wiki_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        slug="unique-slug",
        title="Unique Slug Page",
        page_type=WikiPageType.entity,
        content="Content",
    )
    await db_session.commit()

    found = await wiki_repo.get_by_slug(test_kb.id, "unique-slug")
    assert found is not None
    assert found.title == "Unique Slug Page"


async def test_wiki_list_by_kb_with_type_filter(wiki_repo, test_kb, db_session):
    await wiki_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        slug="concept-1",
        title="Concept Page",
        page_type=WikiPageType.concept,
        content="content",
    )
    await wiki_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        slug="entity-1",
        title="Entity Page",
        page_type=WikiPageType.entity,
        content="content",
    )
    await db_session.commit()

    concepts = await wiki_repo.list_by_kb(test_kb.id, page_type=WikiPageType.concept)
    assert all(p.page_type == WikiPageType.concept for p in concepts)
    assert len(concepts) >= 1

    entities = await wiki_repo.list_by_kb(test_kb.id, page_type=WikiPageType.entity)
    assert all(p.page_type == WikiPageType.entity for p in entities)


async def test_wiki_update(wiki_repo, test_kb, db_session):
    page = await wiki_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        slug="update-test",
        title="Original Title",
        page_type=WikiPageType.concept,
        content="original content",
    )
    await db_session.commit()

    await wiki_repo.update(page, title="Updated Title", content="new content")
    await db_session.commit()

    found = await wiki_repo.get_by_id(page.id)
    assert found is not None
    assert found.title == "Updated Title"


# ── EntityRepository ──


async def test_entity_get_by_name(entity_repo, test_kb, db_session):
    entity = Entity(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        name=f"test-entity-{uuid.uuid4().hex[:6]}", entity_type=EntityType.person,
    )
    db_session.add(entity)
    await db_session.commit()

    found = await entity_repo.get_by_name(test_kb.id, entity.name)
    assert found is not None
    assert found.entity_type == EntityType.person


async def test_entity_get_by_name_not_found(entity_repo, test_kb):
    found = await entity_repo.get_by_name(test_kb.id, "nonexistent-entity")
    assert found is None


async def test_entity_list_by_kb(entity_repo, test_kb, db_session):
    for i in range(3):
        db_session.add(Entity(
            id=uuid.uuid4(), kb_id=str(test_kb.id),
            name=f"list-entity-{uuid.uuid4().hex[:6]}-{i}", entity_type=EntityType.topic,
        ))
    await db_session.commit()

    entities = await entity_repo.list_by_kb(test_kb.id)
    assert len(entities) >= 3


# ── NotificationRepository ──


async def _create_source_for_notification(source_repo, test_kb, db_session):
    source = await source_repo.create(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        url=f"https://example.com/notif-{uuid.uuid4().hex[:6]}",
        title="Notif Source", status=SourceStatus.completed,
    )
    await db_session.commit()
    return source


async def test_notification_list_by_kb(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.manual, title="Test Notif",
    ))
    await db_session.commit()

    notifs = await notification_repo.list_by_kb(test_kb.id)
    assert len(notifs) >= 1


async def test_notification_list_by_kb_unread_only(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.rss, title="Unread Notif", is_read=False,
    ))
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.rss, title="Read Notif", is_read=True,
    ))
    await db_session.commit()

    unread = await notification_repo.list_by_kb(test_kb.id, unread_only=True)
    assert all(n.is_read is False for n in unread)


async def test_notification_mark_read(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    notif = Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.manual, title="Mark Read Test", is_read=False,
    )
    db_session.add(notif)
    await db_session.commit()

    await notification_repo.mark_read(notif.id)
    await db_session.commit()

    found = await notification_repo.get_by_id(notif.id)
    assert found is not None
    assert found.is_read is True


async def test_notification_count_unread(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.manual, title="Unread 1", is_read=False,
    ))
    await db_session.commit()

    count = await notification_repo.count_unread(test_kb.id)
    assert count >= 1


async def test_notification_count_unread_global(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.manual, title="Global Unread", is_read=False,
    ))
    await db_session.commit()

    count = await notification_repo.count_unread()
    assert count >= 1


async def test_notification_mark_all_read(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    for i in range(3):
        db_session.add(Notification(
            id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
            trigger_type=TriggerType.manual, title=f"Bulk {i}", is_read=False,
        ))
    await db_session.commit()

    await notification_repo.mark_all_read(test_kb.id)
    await db_session.commit()

    unread = await notification_repo.list_by_kb(test_kb.id, unread_only=True)
    assert len(unread) == 0


async def test_notification_list_all(notification_repo, source_repo, test_kb, db_session):
    source = await _create_source_for_notification(source_repo, test_kb, db_session)
    db_session.add(Notification(
        id=uuid.uuid4(), kb_id=str(test_kb.id), source_id=str(source.id),
        trigger_type=TriggerType.manual, title="List All Test",
    ))
    await db_session.commit()

    all_notifs = await notification_repo.list_all()
    assert isinstance(all_notifs, list)
    assert len(all_notifs) >= 1


# ── RssFeedRepository ──


async def test_rss_feed_list_by_kb(rss_feed_repo, test_kb, db_session):
    feed = RssFeed(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        name=f"test-feed-{uuid.uuid4().hex[:6]}",
        url="https://example.com/feed.xml", feed_type=FeedType.rss,
    )
    db_session.add(feed)
    await db_session.commit()

    feeds = await rss_feed_repo.list_by_kb(test_kb.id)
    assert len(feeds) >= 1


async def test_rss_feed_list_active(rss_feed_repo, test_kb, db_session):
    feed = RssFeed(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        name=f"active-feed-{uuid.uuid4().hex[:6]}",
        url="https://example.com/active-feed.xml", feed_type=FeedType.rss,
        is_active=True,
    )
    db_session.add(feed)
    await db_session.commit()

    active = await rss_feed_repo.list_active()
    assert any(f.name == feed.name for f in active)


# ── RssEntryRepository ──


async def _create_feed_for_entry(rss_feed_repo, test_kb, db_session):
    feed = RssFeed(
        id=uuid.uuid4(), kb_id=str(test_kb.id),
        name=f"entry-feed-{uuid.uuid4().hex[:6]}",
        url="https://example.com/entry-feed.xml", feed_type=FeedType.rss,
    )
    db_session.add(feed)
    await db_session.commit()
    return feed


async def test_rss_entry_get_by_guid(rss_entry_repo, test_kb, db_session):
    feed = await _create_feed_for_entry(rss_entry_repo, test_kb, db_session)
    entry = RssEntry(
        id=uuid.uuid4(), feed_id=str(feed.id), kb_id=str(test_kb.id),
        guid=f"guid-{uuid.uuid4().hex[:8]}",
        url="https://example.com/article-1", title="Article 1",
        status=EntryStatus.new,
    )
    db_session.add(entry)
    await db_session.commit()

    found = await rss_entry_repo.get_by_guid(feed.id, entry.guid)
    assert found is not None
    assert found.title == "Article 1"


async def test_rss_entry_get_by_guid_not_found(rss_entry_repo, test_kb, db_session):
    feed = await _create_feed_for_entry(rss_entry_repo, test_kb, db_session)
    found = await rss_entry_repo.get_by_guid(feed.id, "nonexistent-guid")
    assert found is None


async def test_rss_entry_list_by_feed(rss_entry_repo, test_kb, db_session):
    feed = await _create_feed_for_entry(rss_entry_repo, test_kb, db_session)
    for i in range(3):
        db_session.add(RssEntry(
            id=uuid.uuid4(), feed_id=str(feed.id), kb_id=str(test_kb.id),
            guid=f"list-guid-{uuid.uuid4().hex[:8]}-{i}",
            url=f"https://example.com/list-article-{i}", title=f"List Article {i}",
            status=EntryStatus.new,
        ))
    await db_session.commit()

    entries = await rss_entry_repo.list_by_feed(feed.id)
    assert len(entries) >= 3


# ── BaseRepository delete ──


async def test_base_delete(source_repo, test_kb, db_session):
    source = await source_repo.create(
        id=uuid.uuid4(),
        kb_id=str(test_kb.id),
        url="https://example.com/to-delete",
        title="To Delete",
        status=SourceStatus.pending,
    )
    await db_session.commit()

    sid = source.id
    await source_repo.delete(source)
    await db_session.commit()

    assert await source_repo.get_by_id(sid) is None
