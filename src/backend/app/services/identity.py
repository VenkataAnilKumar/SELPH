"""
Identity profile management service
"""

from datetime import datetime, UTC

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import IdentityProfile, Topic, Twin, Consent


class IdentityService:
    """Service for managing twin identity profiles"""

    @staticmethod
    def _replace_topics(db: Session, user_id: str, topic_type: str, topics: list) -> None:
        """Replace all topics of a given type with the provided list."""
        cleaned = []
        for topic in topics:
            normalized = topic.strip()
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)

        db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic_type == topic_type,
            )
        ).delete(synchronize_session=False)

        for topic in cleaned:
            db.add(Topic(
                user_id=user_id,
                topic=topic,
                topic_type=topic_type,
            ))
    
    @staticmethod
    def get_identity_profile(db: Session, user_id: str) -> IdentityProfile:
        """Get identity profile for a user"""
        return db.query(IdentityProfile).filter(IdentityProfile.user_id == user_id).first()
    
    @staticmethod
    def create_identity_profile(
        db: Session,
        user_id: str,
        vocabulary_description: str = None,
        communication_style: str = None,
        topics_known: list = None,
        topics_avoided: list = None,
    ) -> IdentityProfile:
        """
        Create or update identity profile
        
        Args:
            user_id: User ID
            vocabulary_description: How the twin speaks (e.g., "professional, formal")
            communication_style: Style description
            topics_known: List of topics twin is comfortable discussing
            topics_avoided: List of topics twin should avoid
        """
        profile = IdentityService.get_identity_profile(db, user_id)
        
        if not profile:
            profile = IdentityProfile(user_id=user_id)
        
        if vocabulary_description is not None:
            profile.vocabulary_description = vocabulary_description
        if communication_style is not None:
            profile.communication_style = communication_style
        if topics_known is not None:
            profile.topics_known_text = ", ".join(topics_known)
        if topics_avoided is not None:
            profile.topics_avoided_text = ", ".join(topics_avoided)
        
        db.add(profile)
        db.flush()
        
        # Replace topics table rows only for provided fields.
        if topics_known is not None:
            IdentityService._replace_topics(db, user_id, "known", topics_known)

        if topics_avoided is not None:
            IdentityService._replace_topics(db, user_id, "avoided", topics_avoided)
        
        db.commit()
        db.refresh(profile)
        return profile
    
    @staticmethod
    def get_topics_known(db: Session, user_id: str) -> list:
        """Get topics the twin is comfortable discussing"""
        topics = db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic_type == "known",
            )
        ).all()
        return [t.topic for t in topics]
    
    @staticmethod
    def get_topics_avoided(db: Session, user_id: str) -> list:
        """Get topics the twin should avoid"""
        topics = db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic_type == "avoided",
            )
        ).all()
        return [t.topic for t in topics]
    
    @staticmethod
    def add_known_topic(db: Session, user_id: str, topic: str, context: str = None) -> Topic:
        """Add a topic the twin can discuss"""
        existing = db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic == topic,
                Topic.topic_type == "known",
            )
        ).first()
        
        if existing:
            existing.frequency += 1
            db.commit()
            db.refresh(existing)
            return existing
        
        new_topic = Topic(
            user_id=user_id,
            topic=topic,
            topic_type="known",
            context=context,
        )
        db.add(new_topic)
        db.commit()
        db.refresh(new_topic)
        return new_topic
    
    @staticmethod
    def add_avoided_topic(db: Session, user_id: str, topic: str, context: str = None) -> Topic:
        """Add a topic the twin should avoid"""
        existing = db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic == topic,
                Topic.topic_type == "avoided",
            )
        ).first()
        
        if existing:
            existing.frequency += 1
            db.commit()
            db.refresh(existing)
            return existing
        
        new_topic = Topic(
            user_id=user_id,
            topic=topic,
            topic_type="avoided",
            context=context,
        )
        db.add(new_topic)
        db.commit()
        db.refresh(new_topic)
        return new_topic
    
    @staticmethod
    def get_identity_summary(db: Session, user_id: str) -> dict:
        """Get full identity profile summary"""
        profile = IdentityService.get_identity_profile(db, user_id)

        if not profile:
            return None

        topics_known = IdentityService.get_topics_known(db, user_id)
        topics_avoided = IdentityService.get_topics_avoided(db, user_id)

        return {
            "vocabulary_description": profile.vocabulary_description,
            "communication_style": profile.communication_style,
            "topics_known": topics_known,
            "topics_avoided": topics_avoided,
        }

    @staticmethod
    def patch_identity_profile(
        db: Session,
        user_id: str,
        vocabulary_description: str = None,
        communication_style: str = None,
        topics_known: list = None,
        topics_avoided: list = None,
    ) -> IdentityProfile:
        """Patch (partial update) an existing identity profile"""
        return IdentityService.create_identity_profile(
            db,
            user_id=user_id,
            vocabulary_description=vocabulary_description,
            communication_style=communication_style,
            topics_known=topics_known,
            topics_avoided=topics_avoided,
        )

    @staticmethod
    def delete_topic(db: Session, user_id: str, topic: str, topic_type: str) -> bool:
        """Delete a topic by name and type. Returns True if deleted, False if not found."""
        existing = db.query(Topic).filter(
            and_(
                Topic.user_id == user_id,
                Topic.topic == topic,
                Topic.topic_type == topic_type,
            )
        ).first()

        if not existing:
            return False

        db.delete(existing)
        db.commit()
        return True

    @staticmethod
    def get_confidence_score(db: Session, user_id: str) -> dict:
        """
        Stub: compute a confidence score based on profile completeness.
        Phase 2 will replace this with an embedding-based similarity score.
        """
        profile = IdentityService.get_identity_profile(db, user_id)
        topics_known = IdentityService.get_topics_known(db, user_id)
        topics_avoided = IdentityService.get_topics_avoided(db, user_id)

        TOTAL_FIELDS = 4
        filled = sum([
            bool(profile and profile.vocabulary_description),
            bool(profile and profile.communication_style),
            bool(topics_known),
            bool(topics_avoided),
        ])

        score = round(filled / TOTAL_FIELDS, 2)

        if score >= 0.75:
            label = "high"
            message = "Your twin has a strong identity profile."
        elif score >= 0.5:
            label = "medium"
            message = "Your twin has a partial identity profile. Add more details to improve drafts."
        else:
            label = "low"
            message = "Complete your identity profile so your twin can draft accurate responses."

        return {
            "score": score,
            "label": label,
            "fields_complete": filled,
            "total_fields": TOTAL_FIELDS,
            "message": message,
        }

    @staticmethod
    def get_voice_consent(db: Session, user_id: str) -> Consent | None:
        """Return voice clone consent row if present."""
        return db.query(Consent).filter(
            Consent.user_id == user_id,
            Consent.consent_type == "voice_clone",
        ).first()

    @staticmethod
    def set_voice_consent(db: Session, user_id: str, granted: bool) -> Consent:
        """Create or update voice clone consent state."""
        consent = IdentityService.get_voice_consent(db, user_id)
        if not consent:
            consent = Consent(user_id=user_id, consent_type="voice_clone")

        consent.granted = granted
        consent.granted_at = datetime.now(UTC).replace(tzinfo=None) if granted else None
        if not granted:
            consent.expires_at = None

        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def is_voice_consent_granted(db: Session, user_id: str) -> bool:
        """Check whether voice clone consent is currently granted."""
        consent = IdentityService.get_voice_consent(db, user_id)
        if not consent or not consent.granted:
            return False
        if consent.expires_at and consent.expires_at <= datetime.now(UTC).replace(tzinfo=None):
            return False
        return True

    @staticmethod
    def enroll_voice_profile(
        db: Session,
        user_id: str,
        voice_provider: str,
        voice_model_id: str | None,
        voice_sample_url: str | None,
    ) -> IdentityProfile:
        """Persist voice profile metadata in identity profile."""
        profile = IdentityService.get_identity_profile(db, user_id)
        if not profile:
            profile = IdentityProfile(user_id=user_id)

        profile.voice_provider = voice_provider
        profile.voice_model_id = voice_model_id
        profile.voice_sample_url = voice_sample_url

        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def clear_voice_profile(db: Session, user_id: str) -> IdentityProfile:
        """Remove enrolled voice metadata for the user."""
        profile = IdentityService.get_identity_profile(db, user_id)
        if not profile:
            profile = IdentityProfile(user_id=user_id)

        profile.voice_model_id = None
        profile.voice_sample_url = None

        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
