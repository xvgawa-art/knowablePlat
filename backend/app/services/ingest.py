import json
import re
import uuid
from datetime import UTC, datetime

import structlog

from app.models.entity import EntityType
from app.models.log import ActionEnum
from app.models.notification import TriggerType
from app.models.wiki_page import WikiPage, WikiPageType
from app.prompts.loader import load_prompt
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.entity import EntityRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.notification import NotificationRepository
from app.repositories.source import SourceRepository
from app.repositories.wiki_page import WikiPageRepository
from app.services.filesystem import save_wiki_index, save_wiki_log, save_wiki_page
from app.services.llm import generate

logger = structlog.get_logger()

EXTRACT_SYSTEM = load_prompt("ingest_extract")
SYNTHESIZE_SYSTEM = load_prompt("ingest_synthesize")
CROSSREF_SYSTEM = load_prompt("ingest_crossref")


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200].strip("-") or "untitled"


async def _extract(source_content: str) -> dict:
    """Extract structured information from source content."""
    prompt = f"请分析以下文章内容并提取关键信息：\n\n{source_content[:8000]}"
    result = await generate(prompt, system=EXTRACT_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        logger.warning("extract_json_parse_failed", result=result[:200])
    return {"title": "未知标题", "summary": result[:200], "key_points": [], "entities": [], "topics": []}


async def _synthesize_wiki_page(
    kb_slug: str,
    source_title: str,
    source_summary: str,
    extract_result: dict,
    existing_pages: list[dict] | None = None,
) -> str:
    """Generate wiki page content from extracted source information."""
    extract_str = json.dumps(extract_result, ensure_ascii=False)
    context = f"知识库：{kb_slug}\n来源标题：{source_title}\n来源摘要：{source_summary}\n提取信息：{extract_str[:4000]}"
    if existing_pages:
        page_list = "\n".join(f"- {p['title']} ({p['slug']})" for p in existing_pages[:20])
        context += f"\n\n已有 wiki 页面：\n{page_list}"

    result = await generate(context, system=SYNTHESIZE_SYSTEM)
    return result


async def _find_cross_references(
    kb_slug: str, new_page_title: str, new_page_content: str, existing_pages: list[dict]
) -> list[str]:
    """Find existing wiki pages that should link to/from the new page."""
    if not existing_pages:
        return []

    page_list = "\n".join(f"- {p['title']} ({p['slug']})" for p in existing_pages[:30])
    prompt = (
        f"基于以下新页面和已有页面列表，找出应该互相链接的页面。\n\n"
        f"新页面：{new_page_title}\n新页面内容摘要：{new_page_content[:2000]}\n\n"
        f"已有页面：\n{page_list}"
    )

    result = await generate(prompt, system=CROSSREF_SYSTEM)
    try:
        json_match = re.search(r"\[[\s\S]*\]", result)
        if json_match:
            slugs = json.loads(json_match.group())
            if isinstance(slugs, list):
                return [s for s in slugs if isinstance(s, str)]
    except json.JSONDecodeError:
        logger.warning("crossref_json_parse_failed", result=result[:200])
    return []


async def _build_index_content(pages: list[WikiPage]) -> str:
    """Generate index.md content for a knowledge base."""
    lines = ["# 知识库目录\n"]
    by_type: dict[str, list[WikiPage]] = {}
    for page in pages:
        by_type.setdefault(page.page_type, []).append(page)

    type_labels = {
        WikiPageType.source: "来源摘要",
        WikiPageType.entity: "实体",
        WikiPageType.concept: "概念",
        WikiPageType.comparison: "对比分析",
        WikiPageType.tool: "工具",
        WikiPageType.tool_category: "工具分类",
    }

    for ptype, label in type_labels.items():
        group = by_type.get(ptype, [])
        if not group:
            continue
        lines.append(f"\n## {label}\n")
        for p in sorted(group, key=lambda x: x.title):
            lines.append(f"- [[{p.slug}|{p.title}]]")

    return "\n".join(lines)


async def run_ingest_pipeline(source_id: uuid.UUID, kb_slug: str) -> None:
    """Full ingest pipeline: fetch -> extract -> synthesize -> create wiki pages -> cross-ref -> update index/log."""
    from app.database import async_sessionmaker

    async with async_sessionmaker() as session:
        async with session.begin():
            source_repo = SourceRepository(session)
            kb_repo = KnowledgeBaseRepository(session)
            wiki_repo = WikiPageRepository(session)
            entity_repo = EntityRepository(session)
            log_repo = ActivityLogRepository(session)
            notif_repo = NotificationRepository(session)

            source = await source_repo.get_by_id(source_id)
            if source is None:
                logger.warning("ingest_source_not_found", source_id=str(source_id))
                return

            kb = await kb_repo.get_by_slug(kb_slug)
            if kb is None:
                logger.warning("ingest_kb_not_found", kb_slug=kb_slug)
                return

            if not source.raw_content:
                logger.warning("ingest_no_content", source_id=str(source_id))
                from app.models.source import SourceStatus

                source.status = SourceStatus.failed
                return

            try:
                # Step 1: Extract structured info from source content
                logger.info("ingest_extract_start", source_id=str(source_id))
                extracted = await _extract(source.raw_content)

                title = extracted.get("title", source.title or "未知标题")
                source.title = title

                # Step 2: Create source summary wiki page
                source_slug = _slugify(title) + f"-{str(source_id)[:8]}"
                existing_pages = await wiki_repo.list_by_kb(kb.id, limit=100)
                existing_dicts = [{"title": p.title, "slug": p.slug} for p in existing_pages]

                wiki_content = await _synthesize_wiki_page(
                    kb_slug, title, extracted.get("summary", ""), extracted, existing_dicts
                )

                wiki_page = await wiki_repo.create(
                    kb_id=kb.id,
                    slug=source_slug,
                    title=title,
                    page_type=WikiPageType.source,
                    content=wiki_content,
                    source_ids=[str(source.id)],
                    outgoing_links=[],
                    incoming_links=[],
                )
                save_wiki_page(kb_slug, source_slug, wiki_content)

                # Step 3: Create/update entities
                entities_data = extracted.get("entities", [])
                entity_type_map = {
                    "person": EntityType.person,
                    "organization": EntityType.organization,
                    "tool": EntityType.tool,
                    "topic": EntityType.topic,
                    "event": EntityType.event,
                }
                for entity_data in entities_data:
                    name = entity_data.get("name", "").strip()
                    etype_str = entity_data.get("type", "topic")
                    etype = entity_type_map.get(etype_str, EntityType.topic)
                    if not name:
                        continue

                    existing_entity = await entity_repo.get_by_name(kb.id, name)
                    if existing_entity:
                        continue

                    entity_slug = _slugify(name)
                    entity_page = await wiki_repo.create(
                        kb_id=kb.id,
                        slug=entity_slug,
                        title=name,
                        page_type=WikiPageType.entity,
                        content=f"# {name}\n\n## 概要\n\n（待补充）\n\n## 相关\n\n- [[{source_slug}]]",
                        source_ids=[str(source.id)],
                        outgoing_links=[source_slug],
                        incoming_links=[],
                    )
                    save_wiki_page(kb_slug, entity_slug, entity_page.content)
                    await entity_repo.create(
                        kb_id=kb.id,
                        name=name,
                        entity_type=etype,
                        aliases=[],
                        wiki_page_id=entity_page.id,
                    )

                # Step 4: Cross-reference with existing pages
                cross_ref_slugs = await _find_cross_references(kb_slug, title, wiki_content[:2000], existing_dicts)
                if cross_ref_slugs:
                    outgoing = list(set((wiki_page.outgoing_links or []) + cross_ref_slugs))
                    await wiki_repo.update(wiki_page, outgoing_links=outgoing)

                    for ref_slug in cross_ref_slugs:
                        ref_page = await wiki_repo.get_by_slug(kb.id, ref_slug)
                        if ref_page:
                            ref_incoming = list(set((ref_page.incoming_links or []) + [source_slug]))
                            await wiki_repo.update(ref_page, incoming_links=ref_incoming)

                # Step 5: Create concept pages for topics
                for topic in extracted.get("topics", []):
                    topic = topic.strip()
                    if not topic:
                        continue
                    topic_slug = _slugify(topic)
                    existing_topic = await wiki_repo.get_by_slug(kb.id, topic_slug)
                    if existing_topic:
                        incoming = list(set((existing_topic.incoming_links or []) + [source_slug]))
                        await wiki_repo.update(existing_topic, incoming_links=incoming)
                    else:
                        concept_content = f"# {topic}\n\n## 概要\n\n（待补充）\n\n## 相关\n\n- [[{source_slug}]]"
                        await wiki_repo.create(
                            kb_id=kb.id,
                            slug=topic_slug,
                            title=topic,
                            page_type=WikiPageType.concept,
                            content=concept_content,
                            source_ids=[str(source.id)],
                            outgoing_links=[source_slug],
                            incoming_links=[],
                        )
                        save_wiki_page(kb_slug, topic_slug, concept_content)

                # Step 6: Update index
                all_pages = await wiki_repo.list_by_kb(kb.id, limit=500)
                index_content = await _build_index_content(all_pages)
                index_page = await wiki_repo.get_by_slug(kb.id, "index")
                if index_page:
                    await wiki_repo.update(index_page, content=index_content)
                else:
                    await wiki_repo.create(
                        kb_id=kb.id,
                        slug="index",
                        title="知识库目录",
                        page_type=WikiPageType.concept,
                        content=index_content,
                        source_ids=[],
                        outgoing_links=[],
                        incoming_links=[],
                    )
                save_wiki_index(kb_slug, index_content)

                # Step 7: Log activity
                await log_repo.create(
                    kb_id=kb.id,
                    action=ActionEnum.ingest,
                    target=source_slug,
                    details={"title": title, "source_url": source.url},
                )
                log_entry = f"## [{datetime.now(UTC).strftime('%Y-%m-%d')}] ingest | {title}"
                save_wiki_log(kb_slug, log_entry)

                # Step 8: Create notification with LLM-generated summary and related points
                from app.services.notification import generate_ingest_notification

                wiki_page_list = [{"title": p.title, "slug": p.slug} for p in existing_pages if p.slug != source_slug][
                    :20
                ]
                notif_content = await generate_ingest_notification(title, extracted.get("summary", ""), wiki_page_list)
                await notif_repo.create(
                    kb_id=kb.id,
                    source_id=source.id,
                    trigger_type=TriggerType.manual,
                    title=f"新知识入库：{title}",
                    summary=notif_content["summary"],
                    related_points=notif_content["related_points"],
                )

                # Mark source as completed
                from app.models.source import SourceStatus

                source.status = SourceStatus.completed
                source.fetched_at = datetime.now(UTC).replace(tzinfo=None)

                logger.info("ingest_completed", source_id=str(source_id), title=title)

            except Exception as e:
                from app.models.source import SourceStatus

                source.status = SourceStatus.failed
                logger.error("ingest_failed", source_id=str(source_id), error=str(e))
                raise
