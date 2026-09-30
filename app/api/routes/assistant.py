from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, get_optional_current_user
from app.models.user import User
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationListResponse,
)
from app.schemas.auth import MessageResponse
from app.services.assistant.assistant_service import AssistantService

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive PolicyGPT AI Assistant Chat",
)
def chat_with_assistant(
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Intelligent conversational assistant grounded in PolicyGPT verified platform data.
    
    Capabilities:
    - **Scheme Search & Guidance**: Natural language queries on welfare schemes and benefits
    - **Policy Search**: Find government policies, regulations, and reforms
    - **Eligibility Assessment**: Checks citizen qualifications against scheme criteria
    - **Side-by-Side Comparison**: Compares 2-3 schemes on benefits, eligibility, and process
    - **Help Desk & FAQs**: Answers portal usage, application submission, and support questions
    
    Supports both public citizens and authenticated users with RBAC-aware context.
    """
    return AssistantService.process_chat(db=db, req=chat_req, current_user=current_user)


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List user's active AI conversation sessions",
)
def list_conversations(
    limit: int = Query(20, ge=1, le=100, description="Max conversations to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve list of past conversation sessions for the authenticated user."""
    return AssistantService.list_conversations(db=db, current_user=current_user, limit=limit)


@router.get(
    "/conversations/{id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation session message history",
)
def get_conversation(
    id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Retrieve full chronological message history and sources for a conversation session."""
    return AssistantService.get_conversation_detail(db=db, conversation_id=id, current_user=current_user)


@router.delete(
    "/conversations/{id}",
    response_model=MessageResponse,
    summary="Delete a conversation session",
)
def delete_conversation(
    id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Delete a conversation session and all its associated messages."""
    AssistantService.delete_conversation(db=db, conversation_id=id, current_user=current_user)
    return MessageResponse(message="Conversation session deleted successfully")
