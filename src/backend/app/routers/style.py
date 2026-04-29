"""Style evolution endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.style import (
    StyleCheckpointListResponse,
    StyleCheckpointResponse,
    StyleDecisionRequest,
    StyleRefreshResponse,
)
from app.services.style_evolution import StyleEvolutionService


router = APIRouter(tags=["Style"])


@router.get("/style/checkpoints", response_model=StyleCheckpointListResponse)
async def list_checkpoints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = StyleEvolutionService.get_pending_checkpoints(db, current_user.id)
    return StyleCheckpointListResponse(total=len(rows), items=[StyleCheckpointResponse.model_validate(r) for r in rows])


@router.get("/style/checkpoints/{checkpoint_id}", response_model=StyleCheckpointResponse)
async def get_checkpoint(
    checkpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = StyleEvolutionService.get_checkpoint(db, current_user.id, checkpoint_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")
    return StyleCheckpointResponse.model_validate(row)


@router.post("/style/checkpoints/{checkpoint_id}/decide", response_model=StyleCheckpointResponse)
async def decide_checkpoint(
    checkpoint_id: str,
    request: StyleDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = StyleEvolutionService.apply_checkpoint_decision(
        db,
        user_id=current_user.id,
        checkpoint_id=checkpoint_id,
        decision=request.decision,
        updated_dimensions=request.updated_dimensions,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")
    return StyleCheckpointResponse.model_validate(row)


@router.post("/style/refresh", response_model=StyleRefreshResponse)
async def refresh_style(
    profile_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = StyleEvolutionService.create_checkpoint(db, current_user.id, profile_id, "manual")
    return StyleRefreshResponse(checkpoint_id=row.id, divergence_score=row.divergence_score)
