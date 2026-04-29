"""Privacy processing mode endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.privacy import (
    PrivacySettingsResponse,
    PrivacySettingsUpdateRequest,
    PrivacyCapabilityRequest,
    PrivacyCapabilityResponse,
)
from app.services.privacy import PrivacyService


router = APIRouter(tags=["Privacy"])


@router.get("/settings", response_model=PrivacySettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = PrivacyService.get_or_create_settings(db, current_user.id)
    return PrivacySettingsResponse(
        processing_mode=row.processing_mode,
        on_device_capable=row.on_device_capable,
        voice_clone_enabled=row.voice_clone_enabled,
        avatar_enabled=row.avatar_enabled,
        cloud_sync_scope=row.cloud_sync_scope,
    )


@router.patch("/settings", response_model=PrivacySettingsResponse)
async def patch_settings(
    request: PrivacySettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        row = PrivacyService.update_settings(db, current_user.id, request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return PrivacySettingsResponse(
        processing_mode=row.processing_mode,
        on_device_capable=row.on_device_capable,
        voice_clone_enabled=row.voice_clone_enabled,
        avatar_enabled=row.avatar_enabled,
        cloud_sync_scope=row.cloud_sync_scope,
    )


@router.post("/capability-check", response_model=PrivacyCapabilityResponse)
async def capability_check(
    request: PrivacyCapabilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PrivacyService.set_capability(db, current_user.id, request.on_device_capable)
    return PrivacyCapabilityResponse(updated=True)
