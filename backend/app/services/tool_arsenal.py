import json
import re
import uuid
from datetime import UTC, datetime

import structlog

from app.models.entity import EntityType
from app.models.log import ActionEnum
from app.models.notification import TriggerType
from app.models.wiki_page import WikiPageType
from app.prompts.loader import load_prompt
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.entity import EntityRepository
from app.repositories.notification import NotificationRepository
from app.repositories.wiki_page import WikiPageRepository
from app.services.filesystem import save_wiki_index, save_wiki_log, save_wiki_page
from app.services.llm import embed, generate, generate_with_usage

logger = structlog.get_logger()

TOOL_EXTRACT_SYSTEM = load_prompt("tool_extract")
TOOL_PAGE_SYSTEM = load_prompt("tool_recommend")
CATEGORY_SYSTEM = load_prompt("tool_categorize")


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200].strip("-") or "untitled"


async def _extract_tool_info(source_content: str) -> dict:
    """Extract structured tool information from source content."""
    prompt = f"请分析以下工具介绍页面并提取工具信息：\n\n{source_content[:8000]}"
    result = await generate(prompt, system=TOOL_EXTRACT_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        logger.warning("tool_extract_json_parse_failed", result=result[:200])
    return {
        "name": "未知工具",
        "description": result[:200],
        "purpose": "",
        "category": "其他",
        "tags": [],
    }


async def _extract_tool_info_with_usage(source_content: str) -> tuple[dict, int]:
    """Extract structured tool information. Returns (tool_info, tokens_used)."""
    prompt = f"请分析以下工具介绍页面并提取工具信息：\n\n{source_content[:8000]}"
    resp = await generate_with_usage(prompt, system=TOOL_EXTRACT_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", resp.text)
        if json_match:
            return json.loads(json_match.group()), resp.total_tokens
    except json.JSONDecodeError:
        logger.warning("tool_extract_json_parse_failed", result=resp.text[:200])
    fallback = {
        "name": "未知工具",
        "description": resp.text[:200],
        "purpose": "",
        "category": "其他",
        "tags": [],
    }
    return fallback, resp.total_tokens


async def _categorize_tool(tool_info: dict) -> dict:
    """Determine tool category using LLM."""
    tool_str = json.dumps(tool_info, ensure_ascii=False)[:2000]
    prompt = f"请判断以下工具的分类：\n\n{tool_str}"
    result = await generate(prompt, system=CATEGORY_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        logger.warning("tool_category_parse_failed", result=result[:200])
    return {"category": "其他", "category_slug": "other", "scenario_recommendations": []}


async def _categorize_tool_with_usage(tool_info: dict) -> tuple[dict, int]:
    """Determine tool category. Returns (category_result, tokens_used)."""
    tool_str = json.dumps(tool_info, ensure_ascii=False)[:2000]
    prompt = f"请判断以下工具的分类：\n\n{tool_str}"
    resp = await generate_with_usage(prompt, system=CATEGORY_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", resp.text)
        if json_match:
            return json.loads(json_match.group()), resp.total_tokens
    except json.JSONDecodeError:
        logger.warning("tool_category_parse_failed", result=resp.text[:200])
    return {"category": "其他", "category_slug": "other", "scenario_recommendations": []}, resp.total_tokens


async def _generate_tool_page(tool_info: dict, existing_tools: list[dict]) -> str:
    """Generate tool wiki page content."""
    tool_str = json.dumps(tool_info, ensure_ascii=False)[:3000]
    context = f"工具信息：\n{tool_str}"
    if existing_tools:
        tool_list = "\n".join(f"- {t['title']} ({t['slug']})" for t in existing_tools[:20])
        context += f"\n\n已有同类工具：\n{tool_list}"

    return await generate(context, system=TOOL_PAGE_SYSTEM)


async def _generate_tool_page_with_usage(tool_info: dict, existing_tools: list[dict]) -> tuple[str, int]:
    """Generate tool wiki page content. Returns (content, tokens_used)."""
    tool_str = json.dumps(tool_info, ensure_ascii=False)[:3000]
    context = f"工具信息：\n{tool_str}"
    if existing_tools:
        tool_list = "\n".join(f"- {t['title']} ({t['slug']})" for t in existing_tools[:20])
        context += f"\n\n已有同类工具：\n{tool_list}"

    resp = await generate_with_usage(context, system=TOOL_PAGE_SYSTEM)
    return resp.text, resp.total_tokens


async def _embed_wiki_page(wiki_repo: WikiPageRepository, page) -> None:
    """Generate and store embedding for a wiki page. Non-blocking failure."""
    try:
        text = f"{page.title}\n{page.content[:2000]}"
        embedding = await embed(text)
        await wiki_repo.update_embedding(page, embedding)
    except Exception:
        logger.warning("embed_failed", slug=page.slug)


async def _generate_category_page(
    category_name: str, category_slug: str, tools: list[dict], recommendations: list[dict]
) -> str:
    """Generate or update category page content."""
    tool_links = "\n".join(f"- [[{t['slug']}|{t['title']}]]" for t in tools)
    rec_lines = []
    for rec in recommendations:
        scenario = rec.get("scenario", "")
        recommended = rec.get("recommended", "")
        if scenario and recommended:
            rec_lines.append(f"- **{scenario}** → [[{_slugify(recommended)}]]")

    rec_section = "\n".join(rec_lines) if rec_lines else "（暂无推荐）"

    return (
        f"# {category_name}\n\n"
        f"## 概述\n\n{category_name}相关的安全工具集合。\n\n"
        f"## 工具列表\n\n{tool_links}\n\n"
        f"## 场景推荐\n\n{rec_section}\n"
    )


async def run_tool_arsenal_pipeline(source_id: uuid.UUID, kb_slug: str) -> None:
    """Tool Arsenal specialized ingest: extract tool info → create tool page → categorize → cross-ref."""
    from app.database import async_sessionmaker
    from app.models.source import SourceStatus

    from .ingest import _build_index_content

    async with async_sessionmaker() as session:
        async with session.begin():
            from app.repositories.knowledge_base import KnowledgeBaseRepository
            from app.repositories.source import SourceRepository

            source_repo = SourceRepository(session)
            kb_repo = KnowledgeBaseRepository(session)
            wiki_repo = WikiPageRepository(session)
            entity_repo = EntityRepository(session)
            log_repo = ActivityLogRepository(session)
            notif_repo = NotificationRepository(session)

            source = await source_repo.get_by_id(source_id)
            if source is None:
                logger.warning("tool_ingest_source_not_found", source_id=str(source_id))
                return

            kb = await kb_repo.get_by_slug(kb_slug)
            if kb is None:
                return

            if not source.raw_content:
                source.status = SourceStatus.failed
                return

            try:
                total_tokens = 0

                # Step 1: Extract tool info
                logger.info("tool_ingest_extract_start", source_id=str(source_id))
                tool_info, tokens = await _extract_tool_info_with_usage(source.raw_content)
                total_tokens += tokens

                tool_name = tool_info.get("name", "未知工具")
                source.title = tool_name
                tool_slug = _slugify(tool_name) + f"-{str(source_id)[:8]}"

                # Step 2: Categorize
                category_result, tokens = await _categorize_tool_with_usage(tool_info)
                total_tokens += tokens
                category_name = category_result.get("category", "其他")
                category_slug = category_result.get("category_slug", "other")
                recommendations = category_result.get("scenario_recommendations", [])

                # Step 3: Generate tool page
                existing_tools = await wiki_repo.list_by_kb(kb.id, page_type=WikiPageType.tool, limit=50)
                existing_tool_dicts = [{"title": p.title, "slug": p.slug} for p in existing_tools]
                tool_content, tokens = await _generate_tool_page_with_usage(tool_info, existing_tool_dicts)
                total_tokens += tokens

                tool_page = await wiki_repo.create(
                    kb_id=kb.id,
                    slug=tool_slug,
                    title=tool_name,
                    page_type=WikiPageType.tool,
                    content=tool_content,
                    source_ids=[str(source.id)],
                    outgoing_links=[],
                    incoming_links=[],
                )
                save_wiki_page(kb_slug, tool_slug, tool_content)
                await _embed_wiki_page(wiki_repo, tool_page)

                # Step 4: Create entity for the tool
                await entity_repo.create(
                    kb_id=kb.id,
                    name=tool_name,
                    entity_type=EntityType.tool,
                    aliases=[],
                    wiki_page_id=tool_page.id,
                )

                # Step 5: Create or update category page
                existing_category = await wiki_repo.get_by_slug(kb.id, category_slug)
                category_tools = [{"title": p.title, "slug": p.slug} for p in existing_tools if p.slug != tool_slug]
                category_tools.append({"title": tool_name, "slug": tool_slug})

                category_content = await _generate_category_page(
                    category_name, category_slug, category_tools, recommendations
                )

                if existing_category:
                    await wiki_repo.update(existing_category, content=category_content)
                    incoming = list(set((existing_category.incoming_links or []) + [tool_slug]))
                    await wiki_repo.update(existing_category, incoming_links=incoming)
                else:
                    await wiki_repo.create(
                        kb_id=kb.id,
                        slug=category_slug,
                        title=f"{category_name}工具",
                        page_type=WikiPageType.tool_category,
                        content=category_content,
                        source_ids=[str(source.id)],
                        outgoing_links=[tool_slug],
                        incoming_links=[],
                    )
                save_wiki_page(kb_slug, category_slug, category_content)
                if existing_category:
                    await _embed_wiki_page(wiki_repo, existing_category)

                # Step 6: Cross-reference with similar tools
                tool_page_outgoing = [category_slug]
                for other_tool in existing_tools[:10]:
                    tool_page_outgoing.append(other_tool.slug)
                    other_incoming = list(set((other_tool.incoming_links or []) + [tool_slug]))
                    await wiki_repo.update(other_tool, incoming_links=other_incoming)

                await wiki_repo.update(tool_page, outgoing_links=list(set(tool_page_outgoing)))

                # Step 7: Update index
                all_pages = await wiki_repo.list_by_kb(kb.id, limit=500)
                index_content = await _build_index_content(all_pages)
                index_page = await wiki_repo.get_by_slug(kb.id, "index")
                if index_page:
                    await wiki_repo.update(index_page, content=index_content)
                else:
                    await wiki_repo.create(
                        kb_id=kb.id,
                        slug="index",
                        title="工具装备库目录",
                        page_type=WikiPageType.concept,
                        content=index_content,
                        source_ids=[],
                        outgoing_links=[],
                        incoming_links=[],
                    )
                save_wiki_index(kb_slug, index_content)

                # Step 8: Log activity
                await log_repo.create(
                    kb_id=kb.id,
                    action=ActionEnum.ingest,
                    target=tool_slug,
                    details={"title": tool_name, "category": category_name, "source_url": source.url},
                )
                log_entry = f"## [{datetime.now(UTC).strftime('%Y-%m-%d')}] ingest | {tool_name} ({category_name})"
                save_wiki_log(kb_slug, log_entry)

                # Step 9: Create notification with LLM summary
                from app.services.notification import generate_ingest_notification

                tool_page_list = [{"title": p.title, "slug": p.slug} for p in existing_tools][:20]
                tool_page_list.append({"title": f"{category_name}工具", "slug": category_slug})
                notif_content = await generate_ingest_notification(
                    tool_name, tool_info.get("description", ""), tool_page_list
                )
                await notif_repo.create(
                    kb_id=kb.id,
                    source_id=source.id,
                    trigger_type=TriggerType.manual,
                    title=f"新工具入库：{tool_name}",
                    summary=notif_content["summary"],
                    related_points=notif_content["related_points"],
                )

                source.status = SourceStatus.completed
                source.token_usage = total_tokens
                source.fetched_at = datetime.now(UTC).replace(tzinfo=None)
                logger.info("tool_ingest_completed", source_id=str(source_id), tool=tool_name, category=category_name)
                await kb_repo.refresh_counts(str(kb.id))

            except Exception as e:
                source.status = SourceStatus.failed
                logger.error("tool_ingest_failed", source_id=str(source_id), error=str(e))
