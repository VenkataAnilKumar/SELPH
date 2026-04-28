"""
Draft endpoints
/v1/drafts/*
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.services import DraftService
from app.services.identity import IdentityService
from app.schemas import (
    DraftResponse,
    DraftApprovalRequest,
    DraftVoiceGenerateRequest,
    DraftVoiceGenerateResponse,
    DraftVoiceStatusResponse,
)
from app.config import get_settings
from app.tasks.voice_synthesis import synthesize_voice
from typing import List

router = APIRouter(tags=["drafts"])


@router.get("/pending", response_model=List[DraftResponse])
async def list_pending_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List pending drafts awaiting user approval
    
    Query Parameters:
    - skip: Number to skip (default 0)
    - limit: Number to return (default 20, max 100)
    
    Returns: List of drafts with status=pending_approval ordered by most recent
    """
    drafts = DraftService.get_pending_drafts(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
    )
    
    return [DraftResponse.model_validate(d) for d in drafts]


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific draft
    
    Returns: Draft details including content, confidence score, moderation status
    """
    draft = DraftService.get_draft(db, draft_id)
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Draft belongs to different user",
        )
    
    return DraftResponse.model_validate(draft)


@router.post("/{draft_id}/approve", response_model=DraftResponse)
async def process_draft_action(
    draft_id: str,
    request: DraftApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    User action on a draft: approve, edit, reject, or skip
    
    Request body:
    - action: "approve" | "reject" | "edit" | "skip"
    - edited_content: Required if action="edit", the modified response
    
    Returns: Updated draft with new status
    
    Action descriptions:
    - approve: Send draft as-is
    - edit: Use edited_content and mark as edited
    - reject: Discard draft, mark as rejected
    - skip: Don't send and don't learn from it
    """
    draft = DraftService.get_draft(db, draft_id)
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Draft belongs to different user",
        )
    
    if draft.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process draft with status={draft.status}. Must be pending_approval.",
        )
    
    try:
        if request.action == "approve":
            updated_draft = DraftService.approve_draft(db, draft_id, current_user.id)
        elif request.action == "reject":
            updated_draft = DraftService.reject_draft(db, draft_id, current_user.id)
        elif request.action == "edit":
            if not request.edited_content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="edited_content required when action=edit",
                )
            updated_draft = DraftService.edit_draft(db, draft_id, current_user.id, request.edited_content)
        elif request.action == "skip":
            updated_draft = DraftService.skip_draft(db, draft_id, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}. Must be approve|reject|edit|skip",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    
    return DraftResponse.model_validate(updated_draft)


@router.post("/{draft_id}/voice/generate", response_model=DraftVoiceGenerateResponse)
async def generate_draft_voice(
    draft_id: str,
    request: DraftVoiceGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Queue voice synthesis for an approved/edited draft."""
    settings = get_settings()
    if not settings.feature_voice_clone:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice clone feature is disabled",
        )

    draft = DraftService.get_draft(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Draft belongs to different user",
        )

    if draft.status not in ("approved", "edited"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Draft must be approved or edited before voice generation",
        )

    if not IdentityService.is_voice_consent_granted(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voice clone consent is required before generation",
        )

    text = draft.edited_content or draft.content

    updated = DraftService.set_voice_status(
        db,
        draft_id=draft.id,
        voice_status="queued",
        voice_audio_url=None,
        voice_provider=None,
        voice_model_id=request.voice_model_id,
        voice_error=None,
    )

    task_result = synthesize_voice.delay(
        draft_id=draft.id,
        user_id=current_user.id,
        text=text,
        voice_profile_id=request.voice_model_id,
    )

    return DraftVoiceGenerateResponse(
        draft_id=draft.id,
        queued=True,
        voice_status=updated.voice_status,
        task_id=str(task_result.id) if task_result else None,
    )


@router.get("/{draft_id}/voice", response_model=DraftVoiceStatusResponse)
async def get_draft_voice_status(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get voice synthesis status and delivery URL for a draft."""
    draft = DraftService.get_draft(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Draft belongs to different user",
        )

    return DraftVoiceStatusResponse(
        draft_id=draft.id,
        voice_status=draft.voice_status,
        voice_audio_url=draft.voice_audio_url,
        voice_provider=draft.voice_provider,
        voice_model_id=draft.voice_model_id,
        voice_error=draft.voice_error,
    )

