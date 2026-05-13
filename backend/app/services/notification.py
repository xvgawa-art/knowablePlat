import json
import re

import structlog

from app.services.llm import generate

logger = structlog.get_logger()

NOTIFY_SYSTEM = """你是一个知识通知生成助手。根据新入库文档的内容和相关 wiki 页面，生成一份知识新增通知。

请以 JSON 格式返回，包含以下字段：
- summary: 当前文档知识内容总结（3-5句话，精炼核心要点）
- related_points: 关联知识点列表，每项包含：
  - wiki_page_slug: 相关 wiki 页面的 slug
  - title: wiki 页面标题
  - relation_desc: 关联描述（一句话说明这个页面与新内容的关联）

如果没有相关 wiki 页面，related_points 返回空数组。"""


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
