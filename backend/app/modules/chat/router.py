from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DbSession
from app.modules.auth.models import User
from app.modules.chat.models import Conversation, ConversationMember, ConversationType, Message, MessageRead
from app.modules.chat.schemas import (
    ConversationMemberResponse,
    ConversationResponse,
    GroupCreateRequest,
    MessageCreateRequest,
    MessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_member(session: DbSession, conversation_id: UUID, user_id: UUID) -> ConversationMember:
    member = await session.scalar(select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user_id
    ))
    if member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this conversation")
    return member


def conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id, type=conversation.type, name=conversation.name,
        members=[ConversationMemberResponse(
            id=item.user.id, username=item.user.username, display_name=item.user.display_name,
            is_admin=item.is_admin, last_read_at=item.last_read_at,
        ) for item in conversation.members], last_message_at=conversation.last_message_at,
    )


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id, conversation_id=message.conversation_id, sender_id=message.sender_id,
        sender_username=message.sender.username, sender_display_name=message.sender.display_name,
        body=message.body, created_at=message.created_at, edited_at=message.edited_at,
        is_deleted=message.is_deleted, read_by_count=len(message.__dict__.get("reads", [])),
    )


async def load_conversation(session: DbSession, conversation_id: UUID) -> Conversation:
    conversation = await session.scalar(select(Conversation).options(selectinload(Conversation.members).joinedload(ConversationMember.user)).where(Conversation.id == conversation_id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/direct/{username}", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_direct(username: str, user: CurrentUser, session: DbSession) -> ConversationResponse:
    target = await session.scalar(select(User).where(User.username == username.lower(), User.is_active.is_(True)))
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="You cannot message yourself")
    conversation = Conversation(type=ConversationType.DIRECT, created_by_id=user.id)
    session.add(conversation)
    await session.flush()
    session.add_all([
        ConversationMember(conversation_id=conversation.id, user_id=user.id, is_admin=True),
        ConversationMember(conversation_id=conversation.id, user_id=target.id),
    ])
    await session.commit()
    return conversation_response(await load_conversation(session, conversation.id))


@router.post("/groups", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_group(request: GroupCreateRequest, user: CurrentUser, session: DbSession) -> ConversationResponse:
    usernames = {item.lower() for item in request.usernames if item.lower() != user.username.lower()}
    users = (await session.scalars(select(User).where(User.username.in_(usernames), User.is_active.is_(True)))).all()
    if len(users) != len(usernames):
        raise HTTPException(status_code=404, detail="One or more users were not found")
    conversation = Conversation(type=ConversationType.GROUP, name=request.name, created_by_id=user.id)
    session.add(conversation)
    await session.flush()
    session.add(ConversationMember(conversation_id=conversation.id, user_id=user.id, is_admin=True))
    session.add_all([ConversationMember(conversation_id=conversation.id, user_id=item.id) for item in users])
    await session.commit()
    return conversation_response(await load_conversation(session, conversation.id))


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(user: CurrentUser, session: DbSession) -> list[ConversationResponse]:
    conversations = (await session.scalars(
        select(Conversation).join(ConversationMember).where(ConversationMember.user_id == user.id)
        .options(selectinload(Conversation.members).joinedload(ConversationMember.user))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
    )).unique().all()
    return [conversation_response(item) for item in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(conversation_id: UUID, user: CurrentUser, session: DbSession, limit: int = 100) -> list[MessageResponse]:
    await get_member(session, conversation_id, user.id)
    messages = (await session.scalars(
        select(Message).where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.reads))
        .order_by(Message.created_at.desc()).limit(min(limit, 200))
    )).all()
    return [message_response(item) for item in reversed(messages)]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(conversation_id: UUID, request: MessageCreateRequest, user: CurrentUser, session: DbSession) -> MessageResponse:
    await get_member(session, conversation_id, user.id)
    message = Message(conversation_id=conversation_id, sender_id=user.id, body=request.body)
    session.add(message)
    conversation = await session.get(Conversation, conversation_id)
    conversation.last_message_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(message)
    message.sender = user
    return message_response(message)


@router.post("/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(conversation_id: UUID, user: CurrentUser, session: DbSession) -> None:
    member = await get_member(session, conversation_id, user.id)
    now = datetime.now(timezone.utc)
    member.last_read_at = now
    messages = (await session.scalars(select(Message).where(Message.conversation_id == conversation_id, Message.sender_id != user.id))).all()
    existing = set((await session.scalars(select(MessageRead.message_id).where(MessageRead.user_id == user.id, MessageRead.message_id.in_([item.id for item in messages])))).all()) if messages else set()
    session.add_all([MessageRead(message_id=item.id, user_id=user.id) for item in messages if item.id not in existing])
    await session.commit()
