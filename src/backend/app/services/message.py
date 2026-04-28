"""
Message management service
"""

from sqlalchemy.orm import Session
from app.models import Message, Draft


class MessageService:
    """Service for managing incoming messages"""
    
    @staticmethod
    def get_message(db: Session, message_id: str) -> Message:
        """Get a message by ID"""
        return db.query(Message).filter(Message.id == message_id).first()
    
    @staticmethod
    def get_user_messages(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: str = None,
    ) -> list:
        """
        Get paginated messages for a user
        
        Args:
            user_id: User ID
            skip: Number of messages to skip (pagination)
            limit: Number of messages to return
            status: Filter by status (received, processed, draft_ready)
        """
        query = db.query(Message).filter(Message.user_id == user_id)
        
        if status:
            query = query.filter(Message.status == status)
        
        return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_messages_by_channel(
        db: Session,
        user_id: str,
        channel: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list:
        """Get messages from a specific channel"""
        return db.query(Message).filter(
            Message.user_id == user_id,
            Message.channel == channel,
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_messages(
        db: Session,
        user_id: str,
        status: str = None,
    ) -> int:
        """Count messages for a user"""
        query = db.query(Message).filter(Message.user_id == user_id)
        
        if status:
            query = query.filter(Message.status == status)
        
        return query.count()
    
    @staticmethod
    def create_message(
        db: Session,
        user_id: str,
        channel: str,
        sender_id: str,
        sender_name: str,
        content: str,
        channel_metadata: dict = None,
    ) -> Message:
        """
        Create a new incoming message
        
        Args:
            user_id: User ID
            channel: Channel name (instagram_dm, gmail, etc.)
            sender_id: External sender ID from channel
            sender_name: Sender's display name
            content: Message content
            channel_metadata: Channel-specific metadata (msg ID, timestamp, etc.)
        """
        message = Message(
            user_id=user_id,
            channel=channel,
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            status="received",
            channel_metadata=channel_metadata or {},
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def mark_as_processed(db: Session, message_id: str) -> Message:
        """Mark message as processed"""
        message = MessageService.get_message(db, message_id)
        if message:
            message.status = "processed"
            db.commit()
            db.refresh(message)
        return message
    
    @staticmethod
    def mark_as_draft_ready(db: Session, message_id: str) -> Message:
        """Mark message as draft ready"""
        message = MessageService.get_message(db, message_id)
        if message:
            message.status = "draft_ready"
            db.commit()
            db.refresh(message)
        return message
    
    @staticmethod
    def delete_message(db: Session, message_id: str) -> bool:
        """Delete a message and its associated draft"""
        message = MessageService.get_message(db, message_id)
        
        if not message:
            return False
        
        # Delete associated draft if exists
        draft = db.query(Draft).filter(Draft.message_id == message_id).first()
        if draft:
            db.delete(draft)
        
        db.delete(message)
        db.commit()
        return True
