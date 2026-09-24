from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession, require_roles
from app.modules.auth.models import User, UserRole
from app.modules.moderation.models import (
    ModerationAction,
    ModerationLog,
    Report,
    ReportStatus,
    ReportTarget,
)
from app.modules.moderation.schemas import (
    AccountStatusUpdateRequest,
    ReportCreateRequest,
    ReportQueueResponse,
    ReportResolutionRequest,
    ReportResponse,
    RoleUpdateRequest,
)
from app.modules.auth.schemas import UserResponse
from app.modules.thoughts.models import Comment, Thought

router = APIRouter(tags=["moderation"])
Moderator = Annotated[User, Depends(require_roles(UserRole.MODERATOR, UserRole.ADMIN))]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def report_response(report: Report) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        reporter_id=report.reporter_id,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        resolution_note=report.resolution_note,
        created_at=report.created_at,
        resolved_by_id=report.resolved_by_id,
    )


@router.post("/thoughts/{thought_id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report_thought(
    thought_id: UUID, request: ReportCreateRequest, user: CurrentUser, session: DbSession
) -> ReportResponse:
    thought = await session.scalar(select(Thought).where(Thought.id == thought_id))
    if thought is None:
        raise HTTPException(status_code=404, detail="Thought not found")
    existing = await session.scalar(
        select(Report).where(
            Report.reporter_id == user.id, Report.target_type == ReportTarget.THOUGHT, Report.target_id == thought_id
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already reported this thought")
    report = Report(
        reporter_id=user.id, target_type=ReportTarget.THOUGHT, target_id=thought_id,
        reason=request.reason, details=request.details,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report_response(report)


@router.post("/thoughts/comments/{comment_id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report_comment(
    comment_id: UUID, request: ReportCreateRequest, user: CurrentUser, session: DbSession
) -> ReportResponse:
    comment = await session.scalar(select(Comment).where(Comment.id == comment_id))
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    existing = await session.scalar(
        select(Report).where(
            Report.reporter_id == user.id, Report.target_type == ReportTarget.COMMENT, Report.target_id == comment_id
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already reported this comment")
    report = Report(
        reporter_id=user.id, target_type=ReportTarget.COMMENT, target_id=comment_id,
        reason=request.reason, details=request.details,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report_response(report)


@router.get("/moderation/reports", response_model=ReportQueueResponse)
async def list_reports(
    user: Moderator,
    session: DbSession,
    report_status: ReportStatus = Query(default=ReportStatus.OPEN, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
) -> ReportQueueResponse:
    reports = (await session.scalars(
        select(Report).where(Report.status == report_status).order_by(Report.created_at).limit(limit)
    )).all()
    open_count = await session.scalar(select(func.count(Report.id)).where(Report.status == ReportStatus.OPEN))
    return ReportQueueResponse(reports=[report_response(item) for item in reports], open_count=open_count or 0)


@router.patch("/moderation/reports/{report_id}", response_model=ReportResponse)
async def resolve_report(
    report_id: UUID, request: ReportResolutionRequest, user: Moderator, session: DbSession
) -> ReportResponse:
    report = await session.scalar(select(Report).where(Report.id == report_id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.OPEN:
        raise HTTPException(status_code=409, detail="Report is already resolved")
    if request.action == ModerationAction.DEACTIVATE_USER and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can deactivate users")

    target_author_id: UUID | None = None
    if report.target_type == ReportTarget.THOUGHT:
        target = await session.get(Thought, report.target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Reported thought no longer exists")
        target_author_id = target.author_id
        if request.action in (ModerationAction.HIDE, ModerationAction.RESTORE):
            target.is_deleted = request.action == ModerationAction.HIDE
    else:
        target = await session.get(Comment, report.target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Reported comment no longer exists")
        target_author_id = target.author_id
        if request.action in (ModerationAction.HIDE, ModerationAction.RESTORE):
            target.is_deleted = request.action == ModerationAction.HIDE

    if request.action == ModerationAction.DEACTIVATE_USER and target_author_id:
        target_user = await session.get(User, target_author_id)
        if target_user:
            target_user.is_active = False

    report.status = ReportStatus.DISMISSED if request.action == ModerationAction.DISMISS else ReportStatus.RESOLVED
    report.resolution_note = request.note
    report.resolved_by_id = user.id
    session.add(ModerationLog(
        moderator_id=user.id, action=request.action, target_type=report.target_type,
        target_id=report.target_id, note=request.note,
    ))
    await session.commit()
    await session.refresh(report)
    return report_response(report)


@router.get("/moderation/logs")
async def list_moderation_logs(user: Moderator, session: DbSession, limit: int = Query(default=100, ge=1, le=200)):
    logs = (await session.scalars(select(ModerationLog).order_by(ModerationLog.created_at.desc()).limit(limit))).all()
    return [{
        "id": log.id, "moderator_id": log.moderator_id, "action": log.action,
        "target_type": log.target_type, "target_id": log.target_id,
        "note": log.note, "created_at": log.created_at,
    } for log in logs]


@router.get("/admin/users", response_model=list[UserResponse])
async def list_users(user: Admin, session: DbSession, limit: int = Query(default=100, ge=1, le=200)):
    users = (await session.scalars(select(User).order_by(User.created_at.desc()).limit(limit))).all()
    return users


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID, request: RoleUpdateRequest, user: Admin, session: DbSession
) -> User:
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id and request.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
    target.role = request.role
    await session.commit()
    await session.refresh(target)
    return target


@router.patch("/admin/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: UUID, request: AccountStatusUpdateRequest, user: Admin, session: DbSession
) -> User:
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id and not request.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    target.is_active = request.is_active
    await session.commit()
    await session.refresh(target)
    return target
