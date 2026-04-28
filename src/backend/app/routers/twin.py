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
from app.schemas import TwinResponse, TwinStatsResponse, UpdateTwinRequest

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

