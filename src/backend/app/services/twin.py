"""
Twin management service
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Twin, User


class TwinService:
    """Service for managing digital twin profiles"""
    
    @staticmethod
    def get_twin(db: Session, user_id: str) -> Twin:
        """Get twin for a user"""
        return db.query(Twin).filter(Twin.user_id == user_id).first()
    
    @staticmethod
    def pause_twin(db: Session, user_id: str) -> Twin:
        """Pause a twin (stop processing messages)"""
        twin = TwinService.get_twin(db, user_id)
        if twin:
            twin.status = "paused"
            db.commit()
            db.refresh(twin)
        return twin
    
    @staticmethod
    def resume_twin(db: Session, user_id: str) -> Twin:
        """Resume a twin (start processing messages)"""
        twin = TwinService.get_twin(db, user_id)
        if twin:
            twin.status = "active"
            db.commit()
            db.refresh(twin)
        return twin
    
    @staticmethod
    def get_twin_stats(db: Session, user_id: str) -> dict:
        """
        Get statistics for a twin
        Returns: Dictionary with counts and status
        """
        from app.models import Message, Draft
        
        twin = TwinService.get_twin(db, user_id)
        
        if not twin:
            return None
        
        # Query statistics
        total_messages = db.query(Message).filter(Message.user_id == user_id).count()
        processed_drafts = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status.in_(["approved", "edited", "sent"])
        ).count()
        pending_drafts = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval"
        ).count()

        total_drafts = db.query(Draft).filter(Draft.user_id == user_id).count()
        fallback_count = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.generation_source == "deterministic",
        ).count()

        total_tokens = db.query(func.coalesce(func.sum(Draft.estimated_total_tokens), 0)).filter(
            Draft.user_id == user_id,
        ).scalar() or 0

        total_cost = db.query(func.coalesce(func.sum(Draft.estimated_cost_usd), 0.0)).filter(
            Draft.user_id == user_id,
        ).scalar() or 0.0

        fallback_rate = round((fallback_count / total_drafts), 4) if total_drafts > 0 else 0.0

        # Approval rate = (approved + edited) / (approved + edited + rejected)
        approved_count = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status.in_(["approved", "edited"]),
        ).count()
        rejected_count = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "rejected",
        ).count()
        decided_count = approved_count + rejected_count
        approval_rate = round(approved_count / decided_count, 4) if decided_count > 0 else 0.0

        generation_source_breakdown = {}
        for source, count in db.query(Draft.generation_source, func.count(Draft.id)).filter(
            Draft.user_id == user_id,
        ).group_by(Draft.generation_source).all():
            generation_source_breakdown[source or "unknown"] = count

        model_breakdown = {}
        for model, count in db.query(Draft.llm_model, func.count(Draft.id)).filter(
            Draft.user_id == user_id,
        ).group_by(Draft.llm_model).all():
            model_breakdown[model or "unknown"] = count

        fallback_reason_breakdown = {}
        for reason, count in db.query(Draft.fallback_reason, func.count(Draft.id)).filter(
            Draft.user_id == user_id,
            Draft.fallback_reason.is_not(None),
        ).group_by(Draft.fallback_reason).all():
            fallback_reason_breakdown[reason] = count
        
        return {
            "twin_id": twin.id,
            "status": twin.status,
            "domain": twin.domain,
            "tone": twin.tone,
            "total_messages": total_messages,
            "pending_drafts": pending_drafts,
            "processed_drafts": processed_drafts,
            "total_estimated_tokens": int(total_tokens),
            "total_estimated_cost_usd": float(round(total_cost, 8)),
            "fallback_rate": fallback_rate,
            "approval_rate": approval_rate,
            "generation_source_breakdown": generation_source_breakdown,
            "model_breakdown": model_breakdown,
            "fallback_reason_breakdown": fallback_reason_breakdown,
        }
    
    @staticmethod
    def update_twin_profile(
        db: Session,
        user_id: str,
        domain: str = None,
        tone: str = None,
        vocab: list = None,
        avg_response_length: int = None,
    ) -> Twin:
        """Update twin profile settings"""
        twin = TwinService.get_twin(db, user_id)
        
        if not twin:
            return None
        
        if domain:
            twin.domain = domain
        if tone:
            twin.tone = tone
        if vocab:
            twin.vocab = vocab
        if avg_response_length:
            twin.avg_response_length = avg_response_length
        
        db.commit()
        db.refresh(twin)
        return twin
