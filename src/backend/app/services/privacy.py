"""Privacy processing mode service."""

from sqlalchemy.orm import Session
from app.models import UserPrivacySettings


class PrivacyService:
    @staticmethod
    def get_or_create_settings(db: Session, user_id: str) -> UserPrivacySettings:
        row = db.query(UserPrivacySettings).filter(UserPrivacySettings.user_id == user_id).first()
        if row:
            return row
        row = UserPrivacySettings(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update_settings(db: Session, user_id: str, updates: dict) -> UserPrivacySettings:
        row = PrivacyService.get_or_create_settings(db, user_id)
        for key, value in updates.items():
            if value is not None:
                setattr(row, key, value)

        if row.processing_mode == "on_device" and not row.on_device_capable:
            raise ValueError("on_device mode is not available for this account")

        if row.processing_mode in {"on_device", "hybrid"}:
            row.voice_clone_enabled = False
            row.avatar_enabled = False

        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def set_capability(db: Session, user_id: str, on_device_capable: bool) -> UserPrivacySettings:
        row = PrivacyService.get_or_create_settings(db, user_id)
        row.on_device_capable = on_device_capable
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
