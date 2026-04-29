"""Twin-to-twin protocol endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.t2t import (
    T2TSessionResponse,
    T2TSessionListResponse,
    T2TApproveRequest,
    T2TRejectRequest,
    T2TExitRequest,
    T2TCreateRequest,
)
from app.services.t2t import T2TService


router = APIRouter(tags=["T2T"])


@router.get("/sessions", response_model=T2TSessionListResponse)
async def list_sessions(
    twin_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = T2TService.list_sessions(db, twin_id)
    return T2TSessionListResponse(total=len(rows), items=[T2TSessionResponse.model_validate(r) for r in rows])


@router.post("/sessions", response_model=T2TSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: T2TCreateRequest,
    initiating_twin: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = T2TService.initiate_session(db, initiating_twin, request.receiving_twin, request.session_type)
    return T2TSessionResponse.model_validate(row)


@router.get("/sessions/{session_id}", response_model=T2TSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = T2TService.get_session(db, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return T2TSessionResponse.model_validate(row)


@router.post("/sessions/{session_id}/approve", response_model=T2TSessionResponse)
async def approve_session(
    session_id: str,
    request: T2TApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = T2TService.record_approval(db, session_id, request.twin_id, request.approved)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return T2TSessionResponse.model_validate(row)


@router.post("/sessions/{session_id}/reject", response_model=T2TSessionResponse)
async def reject_session(
    session_id: str,
    request: T2TRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = T2TService.record_approval(db, session_id, request.twin_id, False)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if request.reason:
        T2TService.add_negotiation_turn(db, session_id, {"event": "reject_reason", "reason": request.reason})
    row = T2TService.get_session(db, session_id)
    return T2TSessionResponse.model_validate(row)


@router.post("/sessions/{session_id}/exit", response_model=T2TSessionResponse)
async def exit_session(
    session_id: str,
    request: T2TExitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = T2TService.exit_session(db, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    T2TService.add_negotiation_turn(db, session_id, {"event": "exit", "twin_id": request.twin_id})
    row = T2TService.get_session(db, session_id)
    return T2TSessionResponse.model_validate(row)
