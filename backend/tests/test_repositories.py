import uuid

import pytest

from app.models.knowledge_base import KbType, KnowledgeBase
from app.models.source import SourceStatus
from app.models.wiki_page import WikiPageType
from app.repositories.knowledge_base import KnowledgeBaseRepository
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
