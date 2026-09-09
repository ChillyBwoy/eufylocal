from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eufylocal.config import settings

engine = create_async_engine(str(settings.db_url), echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
