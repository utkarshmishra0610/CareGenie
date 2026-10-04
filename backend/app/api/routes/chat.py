from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
    FinalizedAssessmentResponse,
)
from app.services import chat_service
from app.schemas.ai import AIHealthResponse
from app.ai.service import process_chat_turn
from app.services.assessment_integration import finalize_session_assessment

router = APIRouter()


@router.post(
    "/sessions",
    response_model=ChatSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
    description="Initializes a new conversational health assessment session."
)
def create_session(
    session_in: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ChatSessionRead:
    """Start a new chat session."""
    db_session = chat_service.create_session(
        db=db, user_id=current_user.id, session_in=session_in
    )
    return ChatSessionRead(
        id=db_session.id,
        user_id=db_session.user_id,
        title=db_session.title,
        language=db_session.language,
        is_active=db_session.is_active,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        message_count=0,
    )


@router.get(
    "/sessions",
    response_model=List[ChatSessionRead],
    status_code=status.HTTP_200_OK,
    summary="List chat sessions",
    description="Returns all chat sessions for the authenticated user, ordered by recent activity."
)
def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ChatSessionRead]:
    """List authenticated user's chat sessions."""
    sessions = chat_service.get_user_sessions(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return [
        ChatSessionRead(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            language=s.language,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get chat session details",
    description="Fetches a specific chat session with its full message history."
)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ChatSessionDetail:
    """Fetch session details with message history."""
    session = chat_service.get_session_by_id(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )
    return ChatSessionDetail(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        language=session.language,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages),
        messages=session.messages,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session",
    description="Permanently deletes a chat session and all its messages."
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a chat session."""
    success = chat_service.delete_session(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )
    return None


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageRead],
    status_code=status.HTTP_200_OK,
    summary="Get session messages",
    description="Returns message history for a specific chat session in chronological order."
)
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ChatMessageRead]:
    """Fetch chronological messages for a session."""
    messages = chat_service.get_session_messages(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )
    return messages


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in a session",
    description="Appends a message to the conversation session."
)
def post_message(
    session_id: int,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ChatMessageRead:
    """Send and record a message within a chat session."""
    session = chat_service.get_session_by_id(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )

    msg = chat_service.add_message(db=db, session=session, message_in=message_in)
    return msg


@router.post(
    "/sessions/{session_id}/interact",
    response_model=AIHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive AI health turn",
    description="Analyzes patient message, extracts symptoms, checks emergencies, and generates AI health guidance."
)
def interact_with_ai(
    session_id: int,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AIHealthResponse:
    """Send patient message, run clinical AI extraction, and return structured guidance."""
    session = chat_service.get_session_by_id(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )

    ai_response = process_chat_turn(
        db=db, session=session, user_message_text=message_in.content
    )
    return ai_response


@router.post(
    "/sessions/{session_id}/finalize-assessment",
    response_model=FinalizedAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize assessment and save to history",
    description="Gathers all conversation symptoms, executes ML disease risk prediction, persists the assessment to user history, and closes the session.",
)
def finalize_assessment(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FinalizedAssessmentResponse:
    """Finalize conversational consultation into structured patient health assessment."""
    session = chat_service.get_session_by_id(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    result = finalize_session_assessment(db=db, session=session, user_id=current_user.id)
    return result

