import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.user_activity import UserActivity

logger = logging.getLogger(__name__)


class ActivityService:
    @staticmethod
    def log_activity(
        db: Session,
        event_type: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> UserActivity:
        """Record a platform usage event for analytics and auditing."""
        details_str: Optional[str] = None
        if details is not None:
            if isinstance(details, (dict, list)):
                try:
                    details_str = json.dumps(details)
                except Exception:
                    details_str = str(details)
            else:
                details_str = str(details)

        activity = UserActivity(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details_str,
            ip_address=ip_address,
        )
        db.add(activity)
        return activity

    @staticmethod
    def list_activities(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Tuple[List[UserActivity], int, int]:
        """List platform activities with pagination and filtering."""
        query = db.query(UserActivity)
        if user_id is not None:
            query = query.filter(UserActivity.user_id == user_id)
        if event_type:
            query = query.filter(UserActivity.event_type == event_type)
        if resource_type:
            query = query.filter(UserActivity.resource_type == resource_type)

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size
        results = query.order_by(desc(UserActivity.created_at)).offset(offset).limit(page_size).all()

        return results, total_count, total_pages
