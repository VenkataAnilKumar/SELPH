"""
Twin endpoints
/v1/twin/*
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.services import TwinService
from app.schemas import (
    TwinResponse,
    TwinStatsResponse,
    TwinQualitySummaryResponse,
    TwinWeeklyDigestResponse,
    TwinPerformanceSummaryResponse,
    UpdateTwinRequest,
)

router = APIRouter(tags=["twin"])


@router.get("/me", response_model=TwinResponse)
async def get_my_twin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's twin profile
    
    Returns: Twin data with domain, tone, vocabulary
    """
    twin = TwinService.get_twin(db, current_user.id)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )
    
    return TwinResponse.model_validate(twin)


@router.post("/pause", response_model=TwinResponse)
async def pause_twin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pause the twin (emergency stop - stops processing messages)
    
    Returns: Updated twin with status=paused
    """
    twin = TwinService.pause_twin(db, current_user.id)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )
    
    return TwinResponse.model_validate(twin)


@router.post("/resume", response_model=TwinResponse)
async def resume_twin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resume the twin after pausing (start processing messages again)
    
    Returns: Updated twin with status=active
    """
    twin = TwinService.resume_twin(db, current_user.id)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )
    
    return TwinResponse.model_validate(twin)


@router.get("/stats", response_model=TwinStatsResponse)
async def get_twin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get twin statistics (message count, draft status, etc.)
    
    Returns: Twin stats including pending/processed drafts
    """
    stats = TwinService.get_twin_stats(db, current_user.id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )
    
    return TwinStatsResponse(**stats)


@router.put("/me", response_model=TwinResponse)
async def update_twin_profile(
    request: UpdateTwinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update twin profile settings
    
    Allows updating domain, tone, vocabulary, response length
    """
    twin = TwinService.update_twin_profile(
        db,
        current_user.id,
        domain=request.domain,
        tone=request.tone,
        vocab=request.vocab,
        avg_response_length=request.avg_response_length,
    )
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )
    
    return TwinResponse.model_validate(twin)


@router.get("/quality-summary", response_model=TwinQualitySummaryResponse)
async def get_twin_quality_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Phase 8 beta quality dashboard summary for the current twin."""
    summary = TwinService.get_quality_summary(db, current_user.id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )

    return TwinQualitySummaryResponse(**summary)


@router.get("/weekly-digest", response_model=TwinWeeklyDigestResponse)
async def get_twin_weekly_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Phase 8 beta weekly digest preview for the current twin."""
    digest = TwinService.get_weekly_digest_summary(db, current_user.id)

    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )

    return TwinWeeklyDigestResponse(**digest)


@router.get("/performance-summary", response_model=TwinPerformanceSummaryResponse)
async def get_twin_performance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Phase 8 performance summary for the <10s draft-generation target."""
    performance = TwinService.get_performance_summary(db, current_user.id)

    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found",
        )

    return TwinPerformanceSummaryResponse(**performance)

