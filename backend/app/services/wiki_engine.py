import structlog

from app.services.llm import generate

logger = structlog.get_logger()

LINT_SYSTEM = """你是一个 Wiki 健康检查助手。分析以下 Wiki 页面内容，找出以下问题：

1. **矛盾** — 不同页面间存在互相矛盾的说法
2. **过时内容** — 可能已经被新知识取代的内容
3. **孤儿页面** — 没有被其他页面链接的页面
4. **缺失概念** — 被提及但没有独立页面的重要概念
5. **缺失交叉引用** — 应该互相关联但尚未链接的页面

请以 JSON 格式返回，包含以下字段：
- contradictions: 矛盾列表，每项包含 {pages, description}
- outdated: 过时内容列表，每项包含 {page, description}
- orphan_pages: 孤儿页面 slug 列表
- missing_concepts: 缺失概念名称列表
- missing_crossrefs: 缺失交叉引用列表，每项包含 {from_page, to_page, reason}
- suggestions: 改进建议列表"""


async def lint_wiki(kb_id: str, kb_slug: str, db) -> dict:
    """Run health check on a knowledge base's wiki.

    Returns a dict with issues found and suggestions.
    """
    from app.repositories.wiki_page import WikiPageRepository

    wiki_repo = WikiPageRepository(db)
    pages = await wiki_repo.list_by_kb(kb_id, limit=500)

    if not pages:
        return {"status": "empty", "issues": [], "suggestions": []}

    # Structural checks (no LLM needed)
    slug_set = {p.slug for p in pages}
    issues = []

    # Check orphan pages (no incoming links, not the index page)
    orphans = [p.slug for p in pages if p.slug != "index" and (not p.incoming_links or len(p.incoming_links) == 0)]
    if orphans:
        issues.append({"type": "orphan_pages", "pages": orphans, "description": "这些页面没有被其他页面链接"})

    # Check broken wikilinks (outgoing links to non-existent pages)
    broken = []
    for page in pages:
        for link in page.outgoing_links or []:
            if link not in slug_set:
                broken.append({"page": page.slug, "broken_link": link})
    if broken:
        issues.append({"type": "broken_links", "items": broken, "description": "以下链接指向不存在的页面"})

    # Check pages with no content
    empty_pages = [p.slug for p in pages if not p.content or len(p.content.strip()) < 50]
    if empty_pages:
        issues.append({"type": "empty_pages", "pages": empty_pages, "description": "这些页面内容过少"})

    # LLM-based checks for contradictions and suggestions
    page_summaries = []
    for page in pages[:30]:
        content_preview = (page.content or "")[:500]
        page_summaries.append(f"## {page.title} (slug: {page.slug})\n{content_preview}")

    wiki_text = "\n\n---\n\n".join(page_summaries)
    llm_prompt = f"知识库 slug: {kb_slug}\n页面数量: {len(pages)}\n\n{wiki_text[:8000]}"

    try:
        import json
        import re

        llm_result = await generate(llm_prompt, system=LINT_SYSTEM)
        json_match = re.search(r"\{[\s\S]*\}", llm_result)
        if json_match:
            llm_issues = json.loads(json_match.group())
            return {
                "status": "checked",
                "page_count": len(pages),
                "structural_issues": issues,
                "llm_analysis": llm_issues,
            }
    except Exception as e:
        logger.warning("wiki_lint_llm_failed", error=str(e))

    return {
        "status": "checked",
        "page_count": len(pages),
        "structural_issues": issues,
        "llm_analysis": None,
    }
