"""
Message endpoints
/v1/messages/*
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.services import MessageService
from app.schemas import MessageResponse
from typing import List

router = APIRouter(tags=["messages"])


@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List incoming messages for current user (paginated)
    
    Query Parameters:
    - skip: Number of messages to skip (default 0)
    - limit: Number of messages to return (default 20, max 100)
    - status: Filter by status (received, processed, draft_ready) [optional]
    
    Returns: List of messages ordered by most recent
    """
    messages = MessageService.get_user_messages(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        status=status,
    )
    
    return [MessageResponse.model_validate(m) for m in messages]


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific message
    
    Returns: Message details including sender, content, channel
    """
    message = MessageService.get_message(db, message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Message belongs to different user",
        )
    
    return MessageResponse.model_validate(message)

