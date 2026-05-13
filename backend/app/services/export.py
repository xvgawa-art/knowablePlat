import io
import zipfile

from app.repositories.wiki_page import WikiPageRepository


async def export_kb_as_zip(kb_id: str, db) -> bytes:
    """Export all wiki pages of a knowledge base as a ZIP of Markdown files.

    Each page becomes a .md file named by its slug, with frontmatter intact.
    Wikilinks use [[slug]] format compatible with Obsidian.
    """
    wiki_repo = WikiPageRepository(db)
    pages = await wiki_repo.list_by_kb(kb_id, limit=2000)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for page in pages:
            lines = []
            lines.append("---")
            lines.append(f"title: {page.title}")
            lines.append(f"type: {page.page_type}")
            if page.source_ids:
                ids = ", ".join(str(s) for s in page.source_ids)
                lines.append(f"sources: [{ids}]")
            lines.append("---")
            lines.append("")
            if page.content:
                lines.append(page.content)
            zf.writestr(f"{page.slug}.md", "\n".join(lines))

    return buf.getvalue()
