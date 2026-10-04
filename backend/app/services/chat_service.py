from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate


def create_session(
    db: Session, user_id: int, session_in: ChatSessionCreate
) -> ChatSession:
    """Create a new conversational health assistant session."""
    title = session_in.title or "Health Assessment Consultation"
    db_session = ChatSession(
        user_id=user_id,
        title=title,
        language=session_in.language or "en",
        is_active=True,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_user_sessions(
    db: Session, user_id: int, skip: int = 0, limit: int = 50
) -> List[ChatSession]:
    """Retrieve all chat sessions for an authenticated user, newest first."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_session_by_id(
    db: Session, user_id: int, session_id: int
) -> Optional[ChatSession]:
    """Fetch a specific chat session ensuring user ownership."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )


def delete_session(db: Session, user_id: int, session_id: int) -> bool:
    """Delete a chat session and all its child messages."""
    session = get_session_by_id(db, user_id, session_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


def add_message(
    db: Session, session: ChatSession, message_in: ChatMessageCreate
) -> ChatMessage:
    """Append a message to a session and update session's updated_at timestamp."""
    db_message = ChatMessage(
        session_id=session.id,
        sender=message_in.sender,
        content=message_in.content,
        extra_metadata=message_in.extra_metadata or {},
        created_at=datetime.now(timezone.utc),
    )
    session.updated_at = datetime.now(timezone.utc)

    # If title is default and user sent first message, update title concisely
    if session.title == "Health Assessment Consultation" and message_in.sender == "user":
        first_few = message_in.content.strip()[:40]
        if first_few:
            session.title = f"Consultation: {first_few}..."

    db.add(db_message)
    db.add(session)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_session_messages(
    db: Session, user_id: int, session_id: int
) -> Optional[List[ChatMessage]]:
    """Fetch all messages for a session in ascending chronological order."""
    session = get_session_by_id(db, user_id, session_id)
    if not session:
        return None
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
