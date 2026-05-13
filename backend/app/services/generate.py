import structlog

from app.prompts.loader import load_prompt
from app.services.llm import generate

logger = structlog.get_logger()

OUTLINE_SYSTEM = load_prompt("generate_outline")
SECTION_SYSTEM = load_prompt("generate_section")
INTEGRATE_SYSTEM = load_prompt("generate_integrate")


async def retrieve_knowledge(kb_ids: list[str], topic: str) -> str:
    """Retrieve relevant wiki pages from selected knowledge bases."""
    from app.database import async_sessionmaker
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.wiki_page import WikiPageRepository

    all_context = []
    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            wiki_repo = WikiPageRepository(session)

            for kb_id in kb_ids:
                try:
                    import uuid

                    kb = await kb_repo.get_by_id(uuid.UUID(kb_id))
                except (ValueError, Exception):
                    continue
                if not kb:
                    continue

                index_page = await wiki_repo.get_by_slug(kb.id, "index")
                if not index_page or not index_page.content:
                    continue

                all_context.append(f"## 知识库：{kb.name}\n\n{index_page.content[:3000]}")

                # Try to find relevant pages by searching index for topic keywords
                pages = await wiki_repo.list_by_kb(kb.id, limit=20)
                for page in pages:
                    if page.content and any(kw in page.title.lower() for kw in topic.lower().split()):
                        all_context.append(f"### {page.title}\n\n{page.content[:1500]}")

    return "\n\n---\n\n".join(all_context) if all_context else f"主题：{topic}"


async def generate_document(kb_ids: list[str], topic: str) -> dict:
    """Generate a structured document from cross-KB knowledge.

    Returns dict with title, content, word_count, token_usage.
    """
    # Step 1: Retrieve knowledge from selected KBs
    knowledge = await retrieve_knowledge(kb_ids, topic)

    # Step 2: Generate outline
    outline_prompt = f"主题要求：{topic}\n\n参考知识：\n{knowledge[:6000]}"
    outline_result = await generate(outline_prompt, system=OUTLINE_SYSTEM)

    import json
    import re

    try:
        json_match = re.search(r"\{[\s\S]*\}", outline_result)
        outline = json.loads(json_match.group()) if json_match else {}
    except json.JSONDecodeError:
        outline = {"title": topic, "sections": [{"heading": topic, "key_points": []}]}
        logger.warning("generate_outline_parse_failed")

    title = outline.get("title", topic)
    sections = outline.get("sections", [])

    # Step 3: Generate each section
    section_contents = []
    for section in sections[:10]:
        heading = section.get("heading", "")
        key_points = section.get("key_points", [])
        section_prompt = (
            f"章节：{heading}\n要点：{json.dumps(key_points, ensure_ascii=False)}\n\n参考知识：\n{knowledge[:4000]}"
        )
        section_content = await generate(section_prompt, system=SECTION_SYSTEM)
        section_contents.append(f"## {heading}\n\n{section_content}")

    # Step 4: Integrate into full document
    combined = f"# {title}\n\n" + "\n\n".join(section_contents)
    integrate_prompt = f"文档标题：{title}\n\n以下是需要整合的各章节内容：\n\n{combined[:12000]}"
    final_content = await generate(integrate_prompt, system=INTEGRATE_SYSTEM)

    word_count = len(final_content)

    return {
        "title": title,
        "content": final_content,
        "word_count": word_count,
        "token_usage": 0,
    }
