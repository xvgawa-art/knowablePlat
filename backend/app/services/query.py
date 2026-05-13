import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts.loader import load_prompt
from app.repositories.wiki_page import WikiPageRepository
from app.services.llm import generate

logger = structlog.get_logger()

QUERY_SYSTEM = load_prompt("query_answer")
TOOL_RECOMMEND_SYSTEM = load_prompt("tool_recommend")

TOOL_ARSENAL_SLUG = "tool-arsenal"


async def answer_question(
    kb_id: uuid.UUID, kb_slug: str, question: str, index_content: str, db: AsyncSession
) -> tuple[str, list[str]]:
    """Answer a question using wiki content. Returns (answer, referenced_page_slugs)."""
    wiki_repo = WikiPageRepository(db)

    # Step 1: Use LLM to identify relevant pages from the index
    page_finder_prompt = (
        f"以下是知识库的目录索引：\n\n{index_content[:4000]}\n\n"
        f"用户问题：{question}\n\n"
        f"请列出与问题最相关的页面 slug（每行一个，只返回 slug）"
    )
    relevant_slugs_raw = await generate(page_finder_prompt)
    potential_slugs = [line.strip().strip("- ").strip() for line in relevant_slugs_raw.split("\n") if line.strip()]

    # Step 2: Read relevant page content
    context_parts = []
    referenced = []
    for slug in potential_slugs[:5]:
        page = await wiki_repo.get_by_slug(kb_id, slug)
        if page and page.content:
            context_parts.append(f"## {page.title} ({page.slug})\n\n{page.content[:2000]}")
            referenced.append(page.slug)

    # For tool arsenal, also include category pages for better recommendations
    if kb_slug == TOOL_ARSENAL_SLUG and not context_parts:
        category_pages = await wiki_repo.list_by_kb(kb_id, limit=10)
        for page in category_pages[:3]:
            if page.content:
                context_parts.append(f"## {page.title} ({page.slug})\n\n{page.content[:1500]}")
                if page.slug not in referenced:
                    referenced.append(page.slug)

    if not context_parts:
        context = index_content[:3000]
    else:
        context = "\n\n---\n\n".join(context_parts)

    # Step 3: Generate answer with appropriate system prompt
    system_prompt = TOOL_RECOMMEND_SYSTEM if kb_slug == TOOL_ARSENAL_SLUG else QUERY_SYSTEM
    prompt = f"知识库：{kb_slug}\n\n以下是与问题相关的 wiki 内容：\n\n{context}\n\n用户问题：{question}"
    answer = await generate(prompt, system=system_prompt)

    return answer, referenced
