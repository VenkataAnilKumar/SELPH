"""
Twin management service
"""

from sqlalchemy.orm import Session
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
            Draft.status.in_(["approved", "sent"])
        ).count()
        pending_drafts = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval"
        ).count()
        
        return {
            "twin_id": twin.id,
            "status": twin.status,
            "domain": twin.domain,
            "tone": twin.tone,
            "total_messages": total_messages,
            "pending_drafts": pending_drafts,
            "processed_drafts": processed_drafts,
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
