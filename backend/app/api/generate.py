import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.generated_doc import DocStatus
from app.repositories.generated_doc import GeneratedDocRepository
from app.schemas.generate import GenerateListItem, GenerateRequest, GenerateResponse

router = APIRouter(prefix="/api/generate", tags=["generate"])


async def _run_generate(doc_id: uuid.UUID, kb_ids: list[str], topic: str) -> None:
    """Background task: generate document from cross-KB knowledge."""
    from app.database import async_sessionmaker
    from app.services.generate import generate_document

    try:
        result = await generate_document(kb_ids, topic)
    except Exception as e:
        import structlog

        structlog.get_logger().error("generate_failed", doc_id=str(doc_id), error=str(e))
        async with async_sessionmaker() as session:
            async with session.begin():
                repo = GeneratedDocRepository(session)
                doc = await repo.get_by_id(doc_id)
                if doc:
                    doc.status = DocStatus.failed
        return

    async with async_sessionmaker() as session:
        async with session.begin():
            repo = GeneratedDocRepository(session)
            doc = await repo.get_by_id(doc_id)
            if doc is None:
                return
            doc.title = result["title"]
            doc.content = result["content"]
            doc.word_count = result["word_count"]
            doc.token_usage = result["token_usage"]
            doc.kb_ids = kb_ids
            doc.status = DocStatus.completed


@router.post("", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    data: GenerateRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    if not data.kb_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一个知识库")
    if not data.topic.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入主题")

    repo = GeneratedDocRepository(db)
    doc = await repo.create(
        title=data.topic[:500],
        topic=data.topic,
        status=DocStatus.generating,
        kb_ids=data.kb_ids,
    )

    background_tasks.add_task(_run_generate, doc.id, data.kb_ids, data.topic)
    return doc


@router.get("", response_model=list[GenerateListItem])
async def list_generations(offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    repo = GeneratedDocRepository(db)
    return await repo.list_all(offset=offset, limit=limit)


@router.get("/{doc_id}", response_model=GenerateResponse)
async def get_generation(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = GeneratedDocRepository(db)
    doc = await repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generation(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = GeneratedDocRepository(db)
    doc = await repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    await repo.delete(doc)
