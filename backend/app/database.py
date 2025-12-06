import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/language_tutor"
)

engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:  # type: AsyncSession
        yield session
