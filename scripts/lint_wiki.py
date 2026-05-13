"""Wiki 健康检查脚本。

用法：cd backend && python -m scripts.lint_wiki <kb_slug>
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import async_sessionmaker
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.wiki_page import WikiPageRepository


async def check_kb(kb_slug: str) -> None:
    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            wiki_repo = WikiPageRepository(session)

            kb = await kb_repo.get_by_slug(kb_slug)
            if not kb:
                print(f"知识库 '{kb_slug}' 不存在")
                return

            pages = await wiki_repo.list_by_kb(str(kb.id), limit=1000)
            slug_set = {p.slug for p in pages}

            print(f"\n=== Wiki 健康检查：{kb.name} ===\n")
            print(f"总页面数: {len(pages)}")

            # 统计页面类型
            by_type: dict[str, int] = {}
            for p in pages:
                by_type[p.page_type] = by_type.get(p.page_type, 0) + 1
            print("\n按类型统计:")
            for ptype, count in sorted(by_type.items()):
                print(f"  {ptype}: {count}")

            # 孤儿页面检查
            orphans = [p for p in pages if p.slug != "index" and (not p.incoming_links or len(p.incoming_links) == 0)]
            if orphans:
                print(f"\n孤儿页面 ({len(orphans)} 个):")
                for p in orphans:
                    print(f"  - {p.slug} ({p.title})")
            else:
                print("\n孤儿页面: 无")

            # 断链检查
            broken = []
            for page in pages:
                for link in page.outgoing_links or []:
                    if link not in slug_set:
                        broken.append((page.slug, link))
            if broken:
                print(f"\n断链 ({len(broken)} 个):")
                for src, target in broken:
                    print(f"  - {src} → {target} (不存在)")
            else:
                print("\n断链: 无")

            # 空内容页面
            empty = [p for p in pages if not p.content or len(p.content.strip()) < 50]
            if empty:
                print(f"\n空内容页面 ({len(empty)} 个):")
                for p in empty:
                    print(f"  - {p.slug} ({p.title}): {len(p.content.strip()) if p.content else 0} 字符")
            else:
                print("\n空内容页面: 无")

            # 双向链接一致性
            inconsistencies = []
            for page in pages:
                for target_slug in page.outgoing_links or []:
                    target = await wiki_repo.get_by_slug(kb.id, target_slug)
                    if target and page.slug not in (target.incoming_links or []):
                        inconsistencies.append((page.slug, target_slug, "incoming_links 缺少反向引用"))
            if inconsistencies:
                print(f"\n链接一致性 ({len(inconsistencies)} 个问题):")
                for src, target, desc in inconsistencies[:10]:
                    print(f"  - {src} → {target}: {desc}")
            else:
                print("\n链接一致性: 通过")

            # 健康评分
            issues = len(orphans) + len(broken) + len(empty) + len(inconsistencies)
            score = max(0, 100 - issues * 5)
            print(f"\n健康评分: {score}/100")

            if score >= 90:
                print("状态: 优秀")
            elif score >= 70:
                print("状态: 良好")
            elif score >= 50:
                print("状态: 需要改进")
            else:
                print("状态: 需要立即修复")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m scripts.lint_wiki <kb_slug>")
        sys.exit(1)
    asyncio.run(check_kb(sys.argv[1]))
