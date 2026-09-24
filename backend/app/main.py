from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.database import initialize_database
from app.modules.auth.follow_router import router as follow_router
from app.modules.auth.router import router as auth_router
from app.modules.thoughts.router import router as thoughts_router
from app.modules.moderation.router import router as moderation_router

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "test":
        await initialize_database()
    yield


app = FastAPI(
    title=settings.app_name, version="0.1.0", description="API for the ThoughtForge social thinking platform.", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(follow_router, prefix=settings.api_prefix)
app.include_router(thoughts_router, prefix=settings.api_prefix)
app.include_router(moderation_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
