"""Privacy processing mode endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.models import DeletionCertificate
from app.routers.auth import _client_ip, _enforce_auth_rate_limit
from app.schemas.privacy import (
    AccountDeletionRequest,
    DeletionCertificateResponse,
    PrivacySettingsResponse,
    PrivacySettingsUpdateRequest,
    PrivacyCapabilityRequest,
    PrivacyCapabilityResponse,
)
from app.security import verify_password
from app.services import erasure
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


DELETE_CONFIRMATION = "DELETE MY ACCOUNT"


def _certificate_response(cert: DeletionCertificate) -> DeletionCertificateResponse:
    return DeletionCertificateResponse(
        certificate_id=cert.id,
        subject_hash=cert.subject_hash,
        completed_at=cert.completed_at,
        summary=cert.summary,
        signature=cert.signature,
        valid=erasure.verify_certificate(cert),
    )


@router.get("/export")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Right to portability: everything SELPH stores about you as JSON (secrets excluded)."""
    return erasure.export_user_data(db, current_user.id)


@router.delete("/account", response_model=DeletionCertificateResponse)
async def delete_my_account(
    request: AccountDeletionRequest,
    client_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Right to erasure: permanently delete the account and all of its data.

    Irreversible. Requires the account password and the exact confirmation phrase so a stolen
    session token alone cannot erase an account. Returns a signed deletion certificate; keep it,
    it is the only record that this happened and it can be verified at
    GET /v1/privacy/deletion-certificates/{certificate_id}.
    """
    _enforce_auth_rate_limit("account_delete", _client_ip(client_request))

    if request.confirm != DELETE_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'confirm must be exactly "{DELETE_CONFIRMATION}"',
        )
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password is incorrect")

    cert = erasure.erase_user(db, current_user.id)
    return _certificate_response(cert)


@router.get("/deletion-certificates/{certificate_id}", response_model=DeletionCertificateResponse)
async def verify_deletion_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Public: check that a deletion certificate is genuine (signature recomputed server-side)."""
    cert = db.query(DeletionCertificate).filter(DeletionCertificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deletion certificate not found")
    return _certificate_response(cert)
