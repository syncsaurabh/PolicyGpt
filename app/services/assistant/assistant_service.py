import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.user import User, UserRole
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationListItem,
    ConversationListResponse,
    ConversationMessageRead,
    SourceCitation,
)
from app.services.assistant.llm_service import LLMService
from app.services.assistant.prompt_service import PromptService
from app.services.assistant.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class AssistantService:
    @staticmethod
    def _generate_suggestions(intent: str, sources: List[SourceCitation]) -> List[str]:
        if intent == "scheme_search":
            return [
                "Am I eligible for this scheme?",
                "What documents are required to apply?",
                "Compare this scheme with another scheme",
            ]
        elif intent == "policy_search":
            return [
                "Which schemes are linked to this policy?",
                "What are the major objectives of this policy?",
            ]
        elif intent == "eligibility":
            return [
                "How do I submit an application for this scheme?",
                "Where can I upload supporting eligibility documents?",
            ]
        elif intent == "comparison":
            return [
                "Which scheme offers higher financial benefits?",
                "Check my eligibility for these schemes",
            ]
        elif intent == "faq_support":
            return [
                "How do I submit a support ticket?",
                "How can I track my submitted applications?",
            ]
        return [
            "Find schemes for students",
            "Check my scheme eligibility",
            "Show policies in Gujarat",
        ]

    @classmethod
    def process_chat(
        cls,
        db: Session,
        req: ChatRequest,
        current_user: Optional[User] = None,
    ) -> ChatResponse:
        user_id = current_user.id if current_user else None

        # 1. Retrieve or create Conversation
        conversation = None
        if req.conversation_id:
            conversation = (
                db.query(AssistantConversation)
                .filter(AssistantConversation.id == req.conversation_id)
                .first()
            )
            # If authenticated, enforce ownership isolation
            if conversation and conversation.user_id and (not current_user or conversation.user_id != current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access conversation session belonging to another user",
                )

        if not conversation:
            conv_id = req.conversation_id or str(uuid.uuid4())
            # Truncate message for title
            clean_title = req.message[:50] + ("..." if len(req.message) > 50 else "")
            conversation = AssistantConversation(
                id=conv_id,
                user_id=user_id,
                title=clean_title,
            )
            db.add(conversation)
            db.flush()

        # 2. Extract recent conversation history
        past_messages = (
            db.query(AssistantMessage)
            .filter(AssistantMessage.conversation_id == conversation.id)
            .order_by(AssistantMessage.created_at.asc())
            .limit(10)
            .all()
        )
        history_dicts = []
        for m in past_messages:
            parsed_src = []
            if m.sources_json:
                try:
                    parsed_src = json.loads(m.sources_json)
                except Exception:
                    pass
            history_dicts.append({
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "sources": parsed_src,
            })

        # 3. Security & Data Privacy Isolation Gate
        rejection = RetrievalService.validate_security_and_privacy(req.message, current_user)
        if rejection:
            rejection_text, rej_intent, rej_citations = rejection
            user_msg = AssistantMessage(
                conversation_id=conversation.id,
                role="user",
                content=req.message,
                intent=rej_intent,
            )
            assistant_msg = AssistantMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=rejection_text,
                sources_json=None,
                intent=rej_intent,
            )
            db.add(user_msg)
            db.add(assistant_msg)
            conversation.updated_at = datetime.now(timezone.utc)
            db.commit()
            return ChatResponse(
                answer=rejection_text,
                conversation_id=conversation.id,
                intent=rej_intent,
                sources=[],
                suggested_questions=[
                    "Find government schemes for students",
                    "Check scheme eligibility",
                    "How do I contact support?",
                ],
                created_at=assistant_msg.created_at,
            )

        # 4. Identify intent & retrieve verified platform facts (strictly user-isolated)
        intent = RetrievalService.identify_intent(req.message, conversation_history=history_dicts)
        citations: List[SourceCitation] = []
        retrieved_context: Dict[str, Any] = {}

        if intent == "user_applications":
            retrieved_context, citations = RetrievalService.retrieve_user_applications(
                db=db, current_user=current_user
            )
        elif intent == "user_saved_policies":
            retrieved_context, citations = RetrievalService.retrieve_user_saved_policies(
                db=db, current_user=current_user
            )
        elif intent == "user_notifications":
            retrieved_context, citations = RetrievalService.retrieve_user_notifications(
                db=db, current_user=current_user
            )
        elif intent == "user_feedback":
            retrieved_context, citations = RetrievalService.retrieve_user_feedback(
                db=db, current_user=current_user
            )
        elif intent == "user_profile":
            retrieved_context, citations = RetrievalService.retrieve_user_profile(
                db=db, current_user=current_user
            )
        elif intent == "application_guidance":
            retrieved_context, citations = RetrievalService.retrieve_application_guidance(
                db=db, query=req.message, conversation_history=history_dicts, current_user=current_user
            )
        elif intent == "comparison":
            retrieved_context, citations = RetrievalService.compare_schemes_context(
                db=db, query=req.message, conversation_history=history_dicts, current_user=current_user
            )
        elif intent == "eligibility":
            retrieved_context, citations = RetrievalService.check_user_eligibility_context(
                db=db, query=req.message, profile_context=req.profile_context, conversation_history=history_dicts, current_user=current_user
            )
        elif intent == "faq_support":
            faqs, citations = RetrievalService.retrieve_faqs(db=db, query=req.message, limit=4)
            retrieved_context = {"faqs": faqs}
        elif intent == "policy_search":
            policies, citations = RetrievalService.retrieve_policies(
                db=db, query=req.message, current_user=current_user, limit=5
            )
            retrieved_context = {"policies": policies}
        else:
            schemes, citations = RetrievalService.retrieve_schemes(
                db=db, query=req.message, current_user=current_user, limit=5
            )
            retrieved_context = {"schemes": schemes}

        # 5. Construct grounded prompts and execute LLM generation
        system_prompt = PromptService.get_system_prompt(current_user=current_user)
        user_prompt = PromptService.build_user_prompt(
            query=req.message,
            retrieved_context=retrieved_context,
            intent=intent,
            conversation_history=history_dicts,
        )

        answer = LLMService.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
            retrieved_context=retrieved_context,
        )

        # 6. Persist user and assistant messages
        sources_json = json.dumps([c.model_dump() for c in citations]) if citations else None

        user_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="user",
            content=req.message,
            intent=intent,
        )
        assistant_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources_json=sources_json,
            intent=intent,
        )
        db.add(user_msg)
        db.add(assistant_msg)
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 7. Suggested follow-ups
        suggestions = cls._generate_suggestions(intent, citations)

        return ChatResponse(
            answer=answer,
            conversation_id=conversation.id,
            intent=intent,
            sources=citations,
            suggested_questions=suggestions,
            created_at=assistant_msg.created_at,
        )

    @staticmethod
    def list_conversations(
        db: Session,
        current_user: User,
        limit: int = 20,
    ) -> ConversationListResponse:
        """List active conversation sessions for the authenticated user."""
        convs = (
            db.query(AssistantConversation)
            .filter(AssistantConversation.user_id == current_user.id)
            .order_by(desc(AssistantConversation.updated_at))
            .limit(limit)
            .all()
        )

        results = []
        for c in convs:
            last_msg = c.messages[-1].content if c.messages else None
            if last_msg and len(last_msg) > 60:
                last_msg = last_msg[:60] + "..."
            results.append(
                ConversationListItem(
                    id=c.id,
                    title=c.title,
                    last_message=last_msg,
                    message_count=len(c.messages),
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        return ConversationListResponse(total_count=len(results), results=results)

    @staticmethod
    def get_conversation_detail(
        db: Session,
        conversation_id: str,
        current_user: Optional[User] = None,
    ) -> ConversationDetailResponse:
        """Get full conversation message history with strict ownership isolation."""
        conv = (
            db.query(AssistantConversation)
            .filter(AssistantConversation.id == conversation_id)
            .first()
        )
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Strict user-ownership isolation
        if conv.user_id and (not current_user or conv.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view another user's conversation history",
            )

        msg_reads: List[ConversationMessageRead] = []
        for m in conv.messages:
            parsed_sources: List[SourceCitation] = []
            if m.sources_json:
                try:
                    s_list = json.loads(m.sources_json)
                    parsed_sources = [SourceCitation(**item) for item in s_list]
                except Exception:
                    pass

            msg_reads.append(
                ConversationMessageRead(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    sources=parsed_sources,
                    intent=m.intent,
                    created_at=m.created_at,
                )
            )

        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=msg_reads,
        )

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: str,
        current_user: Optional[User] = None,
    ) -> bool:
        """Delete conversation session with strict ownership isolation."""
        conv = (
            db.query(AssistantConversation)
            .filter(AssistantConversation.id == conversation_id)
            .first()
        )
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        if conv.user_id and (not current_user or conv.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete another user's conversation",
            )

        db.delete(conv)
        db.commit()
        return True
