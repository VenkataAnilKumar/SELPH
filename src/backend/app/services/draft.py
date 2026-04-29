"""
Draft management service for approval workflow
"""

from sqlalchemy.orm import Session
from app.models import Draft, Message, Twin, AuditLog
from app.models import MessageCluster, BatchSend
from app.services.twin_learning import TwinLearningService
from datetime import datetime, UTC


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
        force_review: bool = False,
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
            force_review=force_review,
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

        from app.services.verification import VerificationService
        cert = VerificationService.issue_certificate(db, user_id)
        content_hash = DraftService._hash_payload(draft.content)
        draft.selph_twin_id = cert.twin_public_id
        draft.selph_signature = VerificationService.sign_message(cert.private_key_ref, content_hash)
        
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

        from app.services.verification import VerificationService
        cert = VerificationService.issue_certificate(db, user_id)
        content_hash = DraftService._hash_payload(edited_content)
        draft.selph_twin_id = cert.twin_public_id
        draft.selph_signature = VerificationService.sign_message(cert.private_key_ref, content_hash)
        
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

    @staticmethod
    def _fingerprint_message(content: str) -> tuple[str, str]:
        """Create a deterministic fingerprint and human label from message text."""
        stopwords = {
            "the", "and", "for", "with", "this", "that", "from", "your", "you", "are", "about",
            "what", "when", "where", "how", "can", "please", "just", "have", "been", "into",
        }
        cleaned = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in content)
        tokens = [t for t in cleaned.split() if len(t) >= 3 and t not in stopwords]
        if not tokens:
            return "misc", "General questions"
        # Use the first two salient tokens for stable, high-recall grouping.
        key_tokens = tokens[:2]
        fingerprint = "|".join(sorted(set(key_tokens)))
        label = " ".join(tokens[:3]).strip()
        return fingerprint, label.title() if label else "General questions"

    @staticmethod
    def _hash_payload(text: str) -> str:
        import hashlib

        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    @staticmethod
    def _pending_drafts_for_batch(db: Session, user_id: str, channel: str | None = None) -> list[Draft]:
        query = db.query(Draft).join(Message, Draft.message_id == Message.id).filter(
            Draft.user_id == user_id,
            Draft.status == "pending_approval",
        )
        if channel:
            query = query.filter(Message.channel == channel)

        # Skip drafts already added to any batch send row.
        used_draft_ids = {row.draft_id for row in db.query(BatchSend).filter(BatchSend.draft_id.isnot(None)).all()}
        rows = query.order_by(Draft.created_at.desc()).all()
        return [row for row in rows if row.id not in used_draft_ids]

    @staticmethod
    def create_message_clusters(
        db: Session,
        user_id: str,
        min_cluster_size: int = 2,
        channel: str | None = None,
    ) -> list[MessageCluster]:
        """Create pending clusters from unbatched pending drafts using deterministic grouping."""
        min_cluster_size = max(2, min_cluster_size)
        pending = DraftService._pending_drafts_for_batch(db, user_id, channel)

        buckets: dict[str, list[Draft]] = {}
        labels: dict[str, str] = {}
        for draft in pending:
            if not draft.message:
                continue
            key, label = DraftService._fingerprint_message(draft.message.content)
            buckets.setdefault(key, []).append(draft)
            labels.setdefault(key, label)

        created_clusters: list[MessageCluster] = []
        for key, members in buckets.items():
            if len(members) < min_cluster_size:
                continue

            message_ids = [m.message_id for m in members]
            template_draft = members[0].content
            summary = f"{len(members)} messages asking similar question"

            cluster = MessageCluster(
                user_id=user_id,
                cluster_label=labels.get(key, "General questions"),
                cluster_summary=summary,
                message_ids=message_ids,
                message_count=len(message_ids),
                template_draft=template_draft,
                status="pending",
            )
            db.add(cluster)
            db.flush()

            for member in members:
                db.add(BatchSend(
                    cluster_id=cluster.id,
                    message_id=member.message_id,
                    draft_id=member.id,
                    sender_id=member.message.sender_id if member.message else "unknown",
                    personalized_text=member.content,
                    status="queued",
                ))

            created_clusters.append(cluster)

        db.commit()
        for cluster in created_clusters:
            db.refresh(cluster)
        return created_clusters

    @staticmethod
    def list_message_clusters(db: Session, user_id: str, status: str | None = None) -> list[MessageCluster]:
        query = db.query(MessageCluster).filter(MessageCluster.user_id == user_id)
        if status:
            query = query.filter(MessageCluster.status == status)
        return query.order_by(MessageCluster.created_at.desc()).all()

    @staticmethod
    def get_message_cluster(db: Session, cluster_id: str) -> MessageCluster | None:
        return db.query(MessageCluster).filter(MessageCluster.id == cluster_id).first()

    @staticmethod
    def _render_template(template: str, message: "Message") -> str:
        """Substitute per-recipient placeholders in a batch template.

        Supported placeholders:
          {sender_name}   – display name of the message sender
          {their_question} – first 120 chars of the original message (trimmed)
          {context_note}  – first 50 chars of the original message (short context)
          {platform}      – channel identifier (e.g. instagram_dm, gmail)
        """
        sender_name = (message.sender_name or "").strip() or "there"
        raw = (message.content or "").strip()
        their_question = (raw[:120] + "…") if len(raw) > 120 else raw
        context_note = (raw[:50] + "…") if len(raw) > 50 else raw
        platform = (message.channel or "").strip()

        return (
            template
            .replace("{sender_name}", sender_name)
            .replace("{their_question}", their_question)
            .replace("{context_note}", context_note)
            .replace("{platform}", platform)
        )

    @staticmethod
    def _populate_batch_sends(db: Session, cluster: "MessageCluster") -> None:
        """Re-render personalized_text for all BatchSend rows using the approved template."""
        sends = db.query(BatchSend).filter(BatchSend.cluster_id == cluster.id).all()
        template = cluster.template_approved or cluster.template_draft or ""
        for send in sends:
            msg = db.query(Message).filter(Message.id == send.message_id).first()
            if msg:
                send.personalized_text = DraftService._render_template(template, msg)
        db.flush()

    @staticmethod
    def approve_cluster_template(
        db: Session,
        cluster_id: str,
        user_id: str,
        template_approved: str | None = None,
    ) -> MessageCluster | None:
        cluster = DraftService.get_message_cluster(db, cluster_id)
        if not cluster:
            return None
        if cluster.user_id != user_id:
            raise ValueError("Unauthorized: Cluster belongs to different user")

        cluster.template_approved = (template_approved or cluster.template_draft).strip()
        cluster.status = "approved"
        cluster.approved_at = datetime.now(UTC).replace(tzinfo=None)
        db.add(cluster)
        db.flush()

        # Render per-recipient personalized text immediately on approval.
        DraftService._populate_batch_sends(db, cluster)

        db.commit()
        db.refresh(cluster)
        return cluster

    @staticmethod
    def list_batch_sends(db: Session, cluster_id: str) -> list["BatchSend"]:
        """Return all BatchSend rows for a cluster, ordered by created_at."""
        return (
            db.query(BatchSend)
            .filter(BatchSend.cluster_id == cluster_id)
            .order_by(BatchSend.created_at)
            .all()
        )
