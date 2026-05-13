import json
import re

import structlog

from app.prompts.loader import load_prompt
from app.services.llm import generate

logger = structlog.get_logger()

NOTIFY_SYSTEM = load_prompt("ingest_notify")


async def generate_ingest_notification(
    source_title: str,
    source_summary: str,
    wiki_pages: list[dict],
) -> dict:
    """Generate notification content with LLM.

    Args:
        source_title: Title of the ingested source.
        source_summary: Summary of the source content.
        wiki_pages: List of related wiki pages with title and slug.

    Returns:
        Dict with summary and related_points fields.
    """
    wiki_list = ""
    if wiki_pages:
        wiki_list = "\n\n已有相关 wiki 页面：\n" + "\n".join(
            f"- {p['title']} (slug: {p['slug']})" for p in wiki_pages[:20]
        )

    prompt = f"新入库文档标题：{source_title}\n文档摘要：{source_summary[:2000]}{wiki_list}"

    result = await generate(prompt, system=NOTIFY_SYSTEM)
    try:
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "summary": parsed.get("summary", source_summary[:500]),
                "related_points": parsed.get("related_points", []),
            }
    except json.JSONDecodeError:
        logger.warning("notification_json_parse_failed", result=result[:200])

    return {"summary": source_summary[:500], "related_points": []}
