import jwt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from uuid import UUID

from app.core.dependencies import CurrentUser, DbSession
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import authenticate_user, create_user, issue_tokens

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, session: DbSession) -> User:
    existing = await session.scalar(
        select(User).where(or_(User.email == str(request.email).lower(), User.username == request.username.lower()))
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username is already in use")
    return await create_user(session, request)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: DbSession) -> dict[str, str]:
    user = await authenticate_user(session, str(request.email), request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, session: DbSession) -> dict[str, str]:
    try:
        payload = decode_token(request.refresh_token, expected_type="refresh")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    user = await session.get(User, UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or unavailable")
    return {"access_token": create_access_token(str(user.id)), "refresh_token": create_refresh_token(str(user.id))}


@router.get("/me", response_model=UserResponse)
async def current_user(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserResponse)
async def update_profile(request: ProfileUpdateRequest, user: CurrentUser, session: DbSession) -> User:
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user
