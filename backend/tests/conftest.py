import uuid

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.knowledge_base import KnowledgeBase
from app.models.user import User

TEST_DATABASE_URL = "postgresql+asyncpg://knowableplat:knowableplat@localhost:5432/knowableplat"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def kb(db_session: AsyncSession) -> KnowledgeBase:
    kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=f"test-kb-{uuid.uuid4().hex[:8]}",
        slug=f"test-kb-{uuid.uuid4().hex[:8]}",
        description="test knowledge base",
    )
    db_session.add(kb)
    await db_session.commit()
    return kb


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        username=f"testuser-{uuid.uuid4().hex[:8]}",
        hashed_password="hashed_foo",
    )
    db_session.add(u)
    await db_session.commit()
    return u
