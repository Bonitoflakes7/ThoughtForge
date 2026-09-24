from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.models import Base
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.thoughts import models as _thought_models  # noqa: F401
from app.modules.moderation import models as _moderation_models  # noqa: F401
from app.modules.chat import models as _chat_models  # noqa: F401
from app.modules.notifications import models as _notification_models  # noqa: F401

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


async def initialize_database() -> None:
    """Create local development tables; production will use Alembic migrations."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
