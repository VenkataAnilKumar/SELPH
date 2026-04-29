"""Proactive twin endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.proactive import (
    ProactiveSuggestionListResponse,
    ProactiveSuggestionResponse,
    SuggestionActRequest,
    ProactivePreferenceResponse,
    ProactivePreferenceUpdateRequest,
    ProactiveScanResponse,
)
from app.services.proactive import ProactiveService


router = APIRouter(tags=["Proactive"])


@router.get("/suggestions", response_model=ProactiveSuggestionListResponse)
async def list_suggestions(
    status_filter: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = ProactiveService.list_suggestions(db, current_user.id, status_filter, limit)
    return ProactiveSuggestionListResponse(total=len(rows), items=[ProactiveSuggestionResponse.model_validate(r) for r in rows])


@router.post("/suggestions/{suggestion_id}/act", response_model=ProactiveSuggestionResponse)
async def act_on_suggestion(
    suggestion_id: str,
    request: SuggestionActRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        row = ProactiveService.act_on_suggestion(
            db,
            suggestion_id=suggestion_id,
            user_id=current_user.id,
            action=request.action,
            edited_message=request.edited_message,
            snooze_days=request.snooze_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    return ProactiveSuggestionResponse.model_validate(row)


@router.get("/preferences", response_model=ProactivePreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = ProactiveService.get_or_create_preferences(db, current_user.id)
    return ProactivePreferenceResponse(
        enabled=prefs.enabled,
        enabled_types=prefs.enabled_types,
        cold_threshold_days=prefs.cold_threshold_days,
        open_thread_hours=prefs.open_thread_hours,
        max_suggestions_per_day=prefs.max_suggestions_per_day,
    )


@router.patch("/preferences", response_model=ProactivePreferenceResponse)
async def patch_preferences(
    request: ProactivePreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = ProactiveService.update_preferences(db, current_user.id, request.model_dump())
    return ProactivePreferenceResponse(
        enabled=prefs.enabled,
        enabled_types=prefs.enabled_types,
        cold_threshold_days=prefs.cold_threshold_days,
        open_thread_hours=prefs.open_thread_hours,
        max_suggestions_per_day=prefs.max_suggestions_per_day,
    )


@router.post("/scan", response_model=ProactiveScanResponse)
async def run_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = ProactiveService.scan_signals(db, current_user.id)
    return ProactiveScanResponse(created=len(rows))
