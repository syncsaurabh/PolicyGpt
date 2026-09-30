from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.feedback import Feedback, FeedbackPriority, FeedbackStatus, FeedbackType
from app.models.user import User, UserRole
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackHistoryItem,
    FeedbackHistoryResponse,
    FeedbackRead,
    FeedbackResolve,
    FeedbackUpdate,
)
from app.services.activity_service import ActivityService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class FeedbackService:
    @staticmethod
    def create_feedback(
        db: Session,
        feedback_in: FeedbackCreate,
        current_user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> Feedback:
        """Create a new citizen feedback, support request, or issue submission."""
        # Derive owner exclusively from the authenticated user context
        user_id = current_user.id if current_user else None

        data = feedback_in.model_dump()
        # Clean up aliases and helper attributes before passing to model
        data.pop("type", None)
        data.pop("description", None)
        ref_id = data.pop("reference_id", None)
        app_id = data.pop("application_id", None)
        final_ref = ref_id or app_id
        if final_ref and "content" in data:
            data["content"] = f"[Reference: {final_ref}]\n{data['content']}"

        initial_status = FeedbackStatus.SUBMITTED.value
        initial_type = data.pop("feedback_type", FeedbackType.FEEDBACK)
        if isinstance(initial_type, FeedbackType):
            initial_type = initial_type.value

        initial_priority = data.pop("priority", FeedbackPriority.MEDIUM)
        if isinstance(initial_priority, FeedbackPriority):
            initial_priority = initial_priority.value

        feedback = Feedback(
            user_id=user_id,
            feedback_type=initial_type,
            status=initial_status,
            priority=initial_priority,
            **data,
        )
        db.add(feedback)
        db.flush()

        AuditService.log(
            db=db,
            action="FEEDBACK_SUBMITTED",
            entity_type="Feedback",
            entity_id=str(feedback.id),
            user_id=user_id,
            details=f"Feedback '{feedback.subject}' submitted of type '{feedback.feedback_type}' with priority '{feedback.priority}'",
            ip_address=ip_address,
        )

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            event_type="FEEDBACK_SUBMITTED",
            resource_type="Feedback",
            resource_id=str(feedback.id),
            details={"subject": feedback.subject, "type": feedback.feedback_type, "priority": feedback.priority},
            ip_address=ip_address,
        )

        # Notify administrators and government officials about the new ticket
        NotificationService.trigger_feedback_submitted(
            db=db,
            feedback_id=feedback.id,
            subject=feedback.subject,
            feedback_type=feedback.feedback_type,
            user_name=current_user.name if current_user else None,
        )

        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def get_feedback(db: Session, feedback_id: int, current_user: User) -> Feedback:
        """Retrieve a feedback ticket with strict user authorization check."""
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback with ID {feedback_id} not found",
            )

        is_privileged = current_user.role in (UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)
        if not is_privileged and feedback.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access feedback submitted by another user",
            )

        return feedback

    @staticmethod
    def list_feedback(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        feedback_type: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc",
        my_only: bool = False,
    ) -> Tuple[List[FeedbackRead], int, int]:
        """
        List feedback items with multi-field filtering, pagination, and RBAC ownership isolation.
        Citizens can only view their own feedback submissions.
        """
        query = db.query(Feedback)

        is_privileged = current_user.role in (UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)
        if not is_privileged or my_only:
            query = query.filter(Feedback.user_id == current_user.id)
        elif user_id is not None:
            query = query.filter(Feedback.user_id == user_id)

        if status_filter:
            query = query.filter(Feedback.status.ilike(status_filter.strip()))
        if feedback_type:
            query = query.filter(Feedback.feedback_type.ilike(feedback_type.strip()))
        if priority:
            query = query.filter(Feedback.priority.ilike(priority.strip()))
        if category:
            query = query.filter(Feedback.category.ilike(f"%{category.strip()}%"))
        if start_date:
            query = query.filter(Feedback.created_at >= start_date)
        if end_date:
            query = query.filter(Feedback.created_at <= end_date)

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size

        # Sorting logic
        sort_column = getattr(Feedback, sort_by, Feedback.created_at) if sort_by else Feedback.created_at
        order_fn = asc if (sort_order and sort_order.lower() == "asc") else desc
        results = query.order_by(order_fn(sort_column)).offset(offset).limit(page_size).all()

        formatted_results = []
        for f in results:
            item = FeedbackRead(
                id=f.id,
                user_id=f.user_id,
                feedback_type=f.feedback_type,
                type=f.feedback_type,
                category=f.category,
                subject=f.subject,
                content=f.content,
                description=f.content,
                rating=f.rating,
                status=f.status,
                priority=f.priority,
                admin_response=f.admin_response,
                resolution=f.admin_response,
                resolved_by_id=f.resolved_by_id,
                resolved_at=f.resolved_at,
                created_at=f.created_at,
                updated_at=f.updated_at,
                user_name=f.user.name if f.user else None,
                user_email=f.user.email if f.user else None,
                resolver_name=f.resolver.name if f.resolver else None,
            )
            formatted_results.append(item)

        return formatted_results, total_count, total_pages

    @staticmethod
    def update_feedback(
        db: Session,
        feedback_id: int,
        feedback_update: FeedbackUpdate,
        current_user: User,
    ) -> Feedback:
        """Update feedback ticket attributes (Admin / Government Official only)."""
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback with ID {feedback_id} not found",
            )

        update_data = feedback_update.model_dump(exclude_unset=True)
        update_data.pop("resolution", None)

        if "status" in update_data and isinstance(update_data["status"], FeedbackStatus):
            update_data["status"] = update_data["status"].value
        if "priority" in update_data and isinstance(update_data["priority"], FeedbackPriority):
            update_data["priority"] = update_data["priority"].value

        # If status is updated to RESOLVED, set resolution timestamp and resolver
        if update_data.get("status") == FeedbackStatus.RESOLVED.value and not feedback.resolved_at:
            feedback.resolved_at = datetime.now(timezone.utc)
            feedback.resolved_by_id = current_user.id

        for key, value in update_data.items():
            setattr(feedback, key, value)

        AuditService.log(
            db=db,
            action="FEEDBACK_UPDATED",
            entity_type="Feedback",
            entity_id=str(feedback.id),
            user_id=current_user.id,
            details=f"Updated feedback ID {feedback_id} fields: {list(update_data.keys())}",
        )
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def resolve_feedback(
        db: Session,
        feedback_id: int,
        resolve_in: FeedbackResolve,
        current_user: User,
    ) -> Feedback:
        """Resolve a support ticket or feedback with official response."""
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback with ID {feedback_id} not found",
            )

        new_status = resolve_in.status.value if isinstance(resolve_in.status, FeedbackStatus) else resolve_in.status
        feedback.admin_response = resolve_in.admin_response
        feedback.status = new_status
        feedback.resolved_by_id = current_user.id
        feedback.resolved_at = datetime.now(timezone.utc)

        AuditService.log(
            db=db,
            action="FEEDBACK_RESOLVED",
            entity_type="Feedback",
            entity_id=str(feedback.id),
            user_id=current_user.id,
            details=f"Feedback ID {feedback_id} resolved with response: '{resolve_in.admin_response[:50]}...'",
        )

        # Trigger in-app notification to the citizen
        if feedback.user_id:
            NotificationService.trigger_feedback_resolved(
                db=db,
                user_id=feedback.user_id,
                feedback_id=feedback.id,
                subject=feedback.subject,
                resolution=resolve_in.admin_response,
            )

        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def get_feedback_history(
        db: Session,
        feedback_id: int,
        current_user: User,
    ) -> FeedbackHistoryResponse:
        """Retrieve audit log history for a feedback ticket."""
        # Ensure user has access to this ticket
        feedback = FeedbackService.get_feedback(db=db, feedback_id=feedback_id, current_user=current_user)

        audit_entries = (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == "Feedback", AuditLog.entity_id == str(feedback.id))
            .order_by(asc(AuditLog.created_at))
            .all()
        )

        history_items = [
            FeedbackHistoryItem(
                id=a.id,
                action=a.action,
                details=a.details,
                user_id=a.user_id,
                created_at=a.created_at,
            )
            for a in audit_entries
        ]

        return FeedbackHistoryResponse(
            feedback_id=feedback.id,
            total_events=len(history_items),
            history=history_items,
        )
