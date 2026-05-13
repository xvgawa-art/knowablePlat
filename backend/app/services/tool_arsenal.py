import json
import re
import uuid
from datetime import UTC, datetime

import structlog

from app.models.entity import EntityType
from app.models.log import ActionEnum
from app.models.notification import TriggerType
from app.models.wiki_page import WikiPageType
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.entity import EntityRepository
from app.repositories.notification import NotificationRepository
from app.repositories.wiki_page import WikiPageRepository
from app.services.llm import generate

logger = structlog.get_logger()

TOOL_EXTRACT_SYSTEM = """你是一个安全工具信息提取助手。阅读以下工具介绍页面，提取结构化工具信息。

请以 JSON 格式返回，包含以下字段：
- name: 工具名称
- description: 一句话简介
- purpose: 核心用途（解决什么问题）
- advantages: 相比同类工具的优势列表
- scenarios: 典型使用场景列表
- category: 所属分类（如：漏洞扫描、信息收集、逆向工程、Web安全、密码破解、无线安全、取证分析、社工、绕过防护）
- homepage: 官方主页 URL（如有）
- download_url: 下载链接（如有）
- license: 许可证类型（如：MIT、GPL、商业、免费开源）
- platforms: 支持平台列表（如：Windows、Linux、macOS）
- tags: 标签列表（最多5个）"""

TOOL_PAGE_SYSTEM = """你是一个工具 wiki 页面撰写助手。根据提取的工具信息，生成结构化的工具页面。

格式要求：
- 使用 Markdown 格式
- 必须包含以下章节：简介、用途、优势、使用场景、快速上手、同类工具、来源
- 使用 [[wikilinks]] 链接到同类工具和分类页面
- 内容准确、实用"""

CATEGORY_SYSTEM = """你是一个工具分类助手。根据工具信息，判断它属于哪个分类。

返回 JSON，包含：
- category: 分类名称（如：漏洞扫描、信息收集、逆向工程、Web安全、密码破解等）
- category_slug: 分类的英文 slug（如：vuln-scanning、info-gathering、reverse-engineering）
- scenario_recommendations: 场景推荐列表，每项包含 scenario（场景）和 recommended（推荐工具名）"""


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


async def _generate_tool_page(tool_info: dict, existing_tools: list[dict]) -> str:
    """Generate tool wiki page content."""
    tool_str = json.dumps(tool_info, ensure_ascii=False)[:3000]
    context = f"工具信息：\n{tool_str}"
    if existing_tools:
        tool_list = "\n".join(f"- {t['title']} ({t['slug']})" for t in existing_tools[:20])
        context += f"\n\n已有同类工具：\n{tool_list}"

    return await generate(context, system=TOOL_PAGE_SYSTEM)


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
                # Step 1: Extract tool info
                logger.info("tool_ingest_extract_start", source_id=str(source_id))
                tool_info = await _extract_tool_info(source.raw_content)

                tool_name = tool_info.get("name", "未知工具")
                source.title = tool_name
                tool_slug = _slugify(tool_name) + f"-{str(source_id)[:8]}"

                # Step 2: Categorize
                category_result = await _categorize_tool(tool_info)
                category_name = category_result.get("category", "其他")
                category_slug = category_result.get("category_slug", "other")
                recommendations = category_result.get("scenario_recommendations", [])

                # Step 3: Generate tool page
                existing_tools = await wiki_repo.list_by_kb(kb.id, page_type=WikiPageType.tool, limit=50)
                existing_tool_dicts = [{"title": p.title, "slug": p.slug} for p in existing_tools]
                tool_content = await _generate_tool_page(tool_info, existing_tool_dicts)

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

                # Step 8: Log activity
                await log_repo.create(
                    kb_id=kb.id,
                    action=ActionEnum.ingest,
                    target=tool_slug,
                    details={"title": tool_name, "category": category_name, "source_url": source.url},
                )

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
                source.fetched_at = datetime.now(UTC).replace(tzinfo=None)
                logger.info("tool_ingest_completed", source_id=str(source_id), tool=tool_name, category=category_name)

            except Exception as e:
                source.status = SourceStatus.failed
                logger.error("tool_ingest_failed", source_id=str(source_id), error=str(e))
                raise
