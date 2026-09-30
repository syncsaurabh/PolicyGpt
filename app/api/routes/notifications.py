from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.notification import (
    NotificationBroadcast,
    NotificationCreate,
    NotificationPaginationResponse,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationPaginationResponse,
    summary="List notifications for the current authenticated user",
)
def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    channel: Optional[str] = Query(None, description="Filter by delivery channel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated notification history for the authenticated user."""
    results, total_count, total_pages, unread_count = NotificationService.list_user_notifications(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
        channel=channel,
    )
    return NotificationPaginationResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        unread_count=unread_count,
        results=[NotificationRead.model_validate(n) for n in results],
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get unread notifications count badge",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return count of unread notifications for notification bell badges."""
    count = NotificationService.get_unread_count(db=db, user_id=current_user.id)
    return NotificationUnreadCountResponse(unread_count=count)


@router.get(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Get user notification preferences",
)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve notification delivery channel and topic preferences."""
    return NotificationService.get_or_create_preferences(db=db, user_id=current_user.id)


@router.put(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Update user notification preferences (PUT)",
)
@router.patch(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Update user notification preferences (PATCH)",
)
def update_preferences(
    pref_in: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification delivery channel and topic preferences."""
    return NotificationService.update_preferences(db=db, user_id=current_user.id, pref_in=pref_in)


@router.put(
    "/mark-all-read",
    response_model=MessageResponse,
    summary="Mark all notifications as read",
)
@router.patch(
    "/mark-all-read",
    response_model=MessageResponse,
    summary="Mark all notifications as read (PATCH)",
)
@router.put(
    "/read-all",
    response_model=MessageResponse,
    summary="Mark all notifications as read (read-all PUT)",
)
@router.patch(
    "/read-all",
    response_model=MessageResponse,
    summary="Mark all notifications as read (read-all PATCH)",
)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all pending notifications as read for current user."""
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return MessageResponse(message=f"Successfully marked {count} notifications as read")


@router.get(
    "/admin/all",
    summary="List all notifications across users (Admin only)",
)
def list_admin_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, description="Filter by delivery status"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Admin endpoint to inspect and monitor platform-wide notification logs."""
    results, total_count, total_pages = NotificationService.list_all_admin_notifications(
        db=db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        status_filter=status_filter,
        notification_type=notification_type,
        channel=channel,
    )
    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": [NotificationRead.model_validate(n) for n in results],
    }


@router.post(
    "/deadline-check",
    response_model=MessageResponse,
    summary="Trigger scheme deadline reminders scan (Admin only)",
)
def trigger_deadline_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Trigger background check for scheme deadlines and dispatch citizen reminders."""
    count = NotificationService.check_and_trigger_deadline_reminders(db=db)
    return MessageResponse(message=f"Deadline reminder check completed. {count} notifications dispatched.")


@router.get(
    "/{id}",
    response_model=NotificationRead,
    summary="Get single notification details",
)
def get_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a single notification with role-based user isolation."""
    is_admin = current_user.role == UserRole.ADMINISTRATOR
    return NotificationService.get_notification_by_id(
        db=db,
        notification_id=id,
        user_id=current_user.id,
        is_admin=is_admin,
    )


@router.put(
    "/{id}/read",
    response_model=NotificationRead,
    summary="Mark a specific notification as read (PUT)",
)
@router.patch(
    "/{id}/read",
    response_model=NotificationRead,
    summary="Mark a specific notification as read (PATCH)",
)
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read, enforcing user isolation."""
    return NotificationService.mark_as_read(db=db, notification_id=id, user_id=current_user.id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete a notification",
)
def delete_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a notification from the user's list (or by admin)."""
    is_admin = current_user.role == UserRole.ADMINISTRATOR
    NotificationService.delete_notification(
        db=db,
        notification_id=id,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return MessageResponse(message="Notification deleted successfully")


@router.post(
    "",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and send a targeted notification",
)
def create_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.ADMINISTRATOR,
        UserRole.GOVERNMENT_OFFICIAL,
    )),
):
    """Create a targeted notification for a specific user (Admin / Official)."""
    return NotificationService.create_notification(
        db=db,
        user_id=notification_in.user_id,
        title=notification_in.title,
        message=notification_in.message,
        notification_type=notification_in.notification_type.value,
        channel=notification_in.channel.value,
        entity_type=notification_in.entity_type,
        entity_id=notification_in.entity_id,
        scheduled_at=notification_in.scheduled_at,
    )


@router.post(
    "/broadcast",
    response_model=MessageResponse,
    summary="Broadcast notification to portal users",
)
def broadcast_notification(
    broadcast_in: NotificationBroadcast,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Broadcast an announcement or alert to users across specific roles (Admin only)."""
    count = NotificationService.broadcast_notification(
        db=db,
        title=broadcast_in.title,
        message=broadcast_in.message,
        notification_type=broadcast_in.notification_type.value,
        channel=broadcast_in.channel.value,
        target_roles=broadcast_in.target_roles,
    )
    return MessageResponse(message=f"Broadcast sent successfully to {count} users")
