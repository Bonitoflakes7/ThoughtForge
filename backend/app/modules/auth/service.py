from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import RegisterRequest


async def create_user(session: AsyncSession, request: RegisterRequest) -> User:
    user = User(
        username=request.username.lower(),
        email=str(request.email).lower(),
        password_hash=hash_password(request.password),
        display_name=request.display_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await session.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(user: User) -> dict[str, str]:
    subject = str(user.id)
    return {"access_token": create_access_token(subject), "refresh_token": create_refresh_token(subject)}
