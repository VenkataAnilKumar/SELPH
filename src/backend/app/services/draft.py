"""
Draft management service for approval workflow
"""

from sqlalchemy.orm import Session
from app.models import Draft, Message, Twin, AuditLog
from app.services.twin_learning import TwinLearningService


class DraftService:
    """Service for managing draft responses"""

    @staticmethod
    def _build_audit_details(draft: Draft) -> dict:
        """Build consistent audit payload for draft lifecycle actions."""
        return {
            "confidence_score": draft.confidence_score,
            "generation_source": draft.generation_source,
            "llm_model": draft.llm_model,
            "fallback_reason": draft.fallback_reason,
            "estimated_total_tokens": draft.estimated_total_tokens,
            "estimated_cost_usd": draft.estimated_cost_usd,
            "status": draft.status,
            "user_action": draft.user_action,
        }
    
    @staticmethod
    def get_draft(db: Session, draft_id: str) -> Draft:
        """Get a draft by ID"""
        return db.query(Draft).filter(Draft.id == draft_id).first()
    
    @staticmethod
    def get_pending_drafts(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list:
        """Get pending drafts for a user"""
        return db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval",
        ).order_by(Draft.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_pending_drafts(db: Session, user_id: str) -> int:
        """Count pending drafts for a user"""
        return db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval",
        ).count()
    
    @staticmethod
    def create_draft(
        db: Session,
        message_id: str,
        user_id: str,
        twin_id: str,
        content: str,
        confidence_score: float = 0.5,
        confidence_label: str = "Medium",
        confidence_reasoning: str = None,
        moderation_passed: bool = False,
        moderation_flags: list = None,
        generation_source: str = None,
        llm_model: str = None,
        fallback_reason: str = None,
        llm_calls: int = None,
        parse_retry_count: int = None,
        llm_latency_ms: int = None,
        pipeline_latency_ms: int = None,
        estimated_input_tokens: int = None,
        estimated_output_tokens: int = None,
        estimated_total_tokens: int = None,
        estimated_cost_usd: float = None,
    ) -> Draft:
        """
        Create a new draft response
        
        Args:
            message_id: ID of the message this draft responds to
            user_id: User ID
            twin_id: Twin ID
            content: Generated response content
            confidence_score: Confidence 0.0-1.0
            confidence_label: High/Medium/Low
            confidence_reasoning: Why this confidence level
            moderation_passed: Whether content passed safety checks
            moderation_flags: List of safety flags if any
        """
        draft = Draft(
            message_id=message_id,
            user_id=user_id,
            twin_id=twin_id,
            content=content,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            confidence_reasoning=confidence_reasoning,
            moderation_passed=moderation_passed,
            moderation_flags=moderation_flags or [],
            generation_source=generation_source,
            llm_model=llm_model,
            fallback_reason=fallback_reason,
            llm_calls=llm_calls,
            parse_retry_count=parse_retry_count,
            llm_latency_ms=llm_latency_ms,
            pipeline_latency_ms=pipeline_latency_ms,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            estimated_total_tokens=estimated_total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            status="pending_approval",
        )
        
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft
    
    @staticmethod
    def approve_draft(db: Session, draft_id: str, user_id: str) -> Draft:
        """Approve a draft (user action: approve)"""
        draft = DraftService.get_draft(db, draft_id)
        
        if not draft:
            return None
        
        if draft.user_id != user_id:
            raise ValueError("Unauthorized: Draft belongs to different user")
        
        draft.status = "approved"
        draft.user_action = "approve"
        
        # Log action
        audit = AuditLog(
            user_id=user_id,
            action="approve_draft",
            resource_type="Draft",
            resource_id=draft_id,
            details=DraftService._build_audit_details(draft),
        )
        db.add(audit)
        db.commit()
        db.refresh(draft)

        # Phase 3.4: reinforce twin profile from approved draft
        TwinLearningService.learn_from_approval(db, draft.twin_id, draft.content)

        return draft
    
    @staticmethod
    def reject_draft(db: Session, draft_id: str, user_id: str) -> Draft:
        """Reject a draft (user action: reject)"""
        draft = DraftService.get_draft(db, draft_id)
        
        if not draft:
            return None
        
        if draft.user_id != user_id:
            raise ValueError("Unauthorized: Draft belongs to different user")
        
        draft.status = "rejected"
        draft.user_action = "reject"
        
        # Log action
        audit = AuditLog(
            user_id=user_id,
            action="reject_draft",
            resource_type="Draft",
            resource_id=draft_id,
            details=DraftService._build_audit_details(draft),
        )
        db.add(audit)
        db.commit()
        db.refresh(draft)
        return draft
    
    @staticmethod
    def edit_draft(
        db: Session,
        draft_id: str,
        user_id: str,
        edited_content: str,
    ) -> Draft:
        """Edit and approve a draft (user action: edit)"""
        draft = DraftService.get_draft(db, draft_id)
        
        if not draft:
            return None
        
        if draft.user_id != user_id:
            raise ValueError("Unauthorized: Draft belongs to different user")
        
        original_content = draft.content
        draft.edited_content = edited_content
        draft.status = "edited"
        draft.user_action = "edit"
        
        # Log action
        audit = AuditLog(
            user_id=user_id,
            action="edit_draft",
            resource_type="Draft",
            resource_id=draft_id,
            details=DraftService._build_audit_details(draft),
        )
        db.add(audit)
        db.commit()
        db.refresh(draft)

        # Phase 3.4: adapt twin profile from user's edit
        TwinLearningService.learn_from_edit(db, draft.twin_id, original_content, edited_content)

        return draft
    
    @staticmethod
    def skip_draft(db: Session, draft_id: str, user_id: str) -> Draft:
        """Skip a draft (user action: skip)"""
        draft = DraftService.get_draft(db, draft_id)
        
        if not draft:
            return None
        
        if draft.user_id != user_id:
            raise ValueError("Unauthorized: Draft belongs to different user")
        
        draft.status = "rejected"  # Treat as rejected
        draft.user_action = "skip"
        
        # Log action
        audit = AuditLog(
            user_id=user_id,
            action="skip_draft",
            resource_type="Draft",
            resource_id=draft_id,
            details=DraftService._build_audit_details(draft),
        )
        db.add(audit)
        db.commit()
        db.refresh(draft)
        return draft
    
    @staticmethod
    def mark_as_sent(db: Session, draft_id: str) -> Draft:
        """Mark draft as sent (post-approval, when response is delivered)"""
        draft = DraftService.get_draft(db, draft_id)
        
        if draft:
            draft.status = "sent"
            db.commit()
            db.refresh(draft)
        
        return draft
    
    @staticmethod
    def get_draft_summary(db: Session, user_id: str) -> dict:
        """Get summary of drafts for a user"""
        total = db.query(Draft).filter(Draft.user_id == user_id).count()
        pending = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval",
        ).count()
        approved = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "approved",
        ).count()
        rejected = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status.in_(["rejected"]),
        ).count()
        sent = db.query(Draft).filter(
            Draft.user_id == user_id,
            Draft.status == "sent",
        ).count()
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "sent": sent,
        }

    @staticmethod
    def set_voice_status(
        db: Session,
        draft_id: str,
        voice_status: str,
        voice_audio_url: str = None,
        voice_provider: str = None,
        voice_model_id: str = None,
        voice_error: str = None,
    ) -> Draft:
        """Update voice synthesis fields on a draft."""
        draft = DraftService.get_draft(db, draft_id)
        if not draft:
            return None

        draft.voice_status = voice_status
        draft.voice_audio_url = voice_audio_url
        draft.voice_provider = voice_provider
        draft.voice_model_id = voice_model_id
        draft.voice_error = voice_error

        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def set_avatar_status(
        db: Session,
        draft_id: str,
        avatar_status: str,
        avatar_video_url: str = None,
        avatar_provider: str = None,
        avatar_model_id: str = None,
        avatar_error: str = None,
    ) -> Draft:
        """Update avatar generation fields on a draft."""
        draft = DraftService.get_draft(db, draft_id)
        if not draft:
            return None

        draft.avatar_status = avatar_status
        draft.avatar_video_url = avatar_video_url
        draft.avatar_provider = avatar_provider
        draft.avatar_model_id = avatar_model_id
        draft.avatar_error = avatar_error

        db.commit()
        db.refresh(draft)
        return draft
