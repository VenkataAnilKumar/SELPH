"""Crisis and surge mode endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.crisis import (
    SurgeStatusResponse,
    CrisisActivateRequest,
    CrisisResolveRequest,
    CrisisTemplateCreateRequest,
    CrisisTemplateResponse,
    CrisisTemplateListResponse,
)
from app.services.crisis import CrisisService


router = APIRouter(tags=["Crisis"])


@router.get("/surge-status", response_model=SurgeStatusResponse)
async def get_surge_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mode = CrisisService.get_twin_mode(db, current_user.id)
    event = CrisisService.get_active_surge_event(db, current_user.id)
    return SurgeStatusResponse(
        mode=mode,
        has_active_event=event is not None,
        trigger_type=event.trigger_type if event else None,
        peak_rate=event.peak_rate if event else None,
        baseline_rate=event.baseline_rate if event else None,
    )


@router.post("/crisis/activate", response_model=SurgeStatusResponse)
async def activate_crisis(
    request: CrisisActivateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        CrisisService.activate_crisis_mode(db, current_user.id, request.trigger_type, request.mode)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    event = CrisisService.get_active_surge_event(db, current_user.id)
    return SurgeStatusResponse(
        mode=request.mode,
        has_active_event=True,
        trigger_type=event.trigger_type if event else request.trigger_type,
        peak_rate=event.peak_rate if event else None,
        baseline_rate=event.baseline_rate if event else None,
    )


@router.post("/crisis/resolve", response_model=SurgeStatusResponse)
async def resolve_crisis(
    request: CrisisResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = CrisisService.resolve_crisis(db, current_user.id, request.resolution_type)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Twin not found")
    return SurgeStatusResponse(mode="normal", has_active_event=False)


@router.get("/crisis/templates", response_model=CrisisTemplateListResponse)
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = CrisisService.list_crisis_templates(db, current_user.id)
    return CrisisTemplateListResponse(total=len(rows), items=[CrisisTemplateResponse.model_validate(r) for r in rows])


@router.post("/crisis/templates", response_model=CrisisTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CrisisTemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        row = CrisisService.create_crisis_template(
            db,
            user_id=current_user.id,
            label=request.label,
            content=request.content,
            template_type=request.template_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CrisisTemplateResponse.model_validate(row)


@router.delete("/crisis/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = CrisisService.delete_crisis_template(db, current_user.id, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
