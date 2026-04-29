"""Twin verification public and private endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.verification import (
    CertificateResponse,
    VerificationResultResponse,
    CertificateMetadataResponse,
    CertificateRevokeRequest,
)
from app.services.verification import VerificationService


router = APIRouter(tags=["Verification"])


@router.get("/verify/{twin_id}", response_model=CertificateMetadataResponse)
async def get_public_certificate(
    twin_id: str,
    db: Session = Depends(get_db),
):
    cert = VerificationService.get_certificate_by_twin_id(db, twin_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    return CertificateMetadataResponse(
        twin_public_id=cert.twin_public_id,
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        revoked_at=cert.revoked_at,
    )


@router.get("/verify/{twin_id}/{message_hash}", response_model=VerificationResultResponse)
async def verify_message(
    twin_id: str,
    message_hash: str,
    signature: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = VerificationService.verify_message(db, twin_id, message_hash, signature)
    return VerificationResultResponse(twin_id=twin_id, message_hash=message_hash, valid=result["valid"], reason=result["reason"])


@router.get("/v1/twin/certificate", response_model=CertificateResponse)
async def get_my_certificate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cert = VerificationService.get_certificate(db, current_user.id)
    if not cert:
        cert = VerificationService.issue_certificate(db, current_user.id)
    return CertificateResponse(
        twin_public_id=cert.twin_public_id,
        public_key=cert.public_key,
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        revoked_at=cert.revoked_at,
    )


@router.post("/v1/twin/certificate/revoke", response_model=CertificateResponse)
async def revoke_my_certificate(
    request: CertificateRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cert = VerificationService.revoke_certificate(db, current_user.id, request.reason)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return CertificateResponse(
        twin_public_id=cert.twin_public_id,
        public_key=cert.public_key,
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        revoked_at=cert.revoked_at,
    )
