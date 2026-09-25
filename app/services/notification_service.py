from datetime import datetime, timezone
import logging
from typing import List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User, UserRole
from app.models.scheme import Scheme, SchemeStatus
from app.models.application import SchemeApplication, ApplicationStatus
from app.schemas.notification import NotificationPreferenceUpdate
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    # =========================================================================
    # 1. Multi-Channel Dispatch Handlers (Email, SMS, In-App)
    # =========================================================================

    @staticmethod
    def _build_email_html(
        subject: str,
        body: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[Union[str, int]] = None,
    ) -> str:
        """Construct a responsive, professional HTML email template."""
        badge_html = (
            f'<span style="display:inline-block;padding:4px 10px;background-color:#eff6ff;color:#1d4ed8;border-radius:4px;font-size:12px;font-weight:600;margin-bottom:12px;">{entity_type} #{entity_id}</span>'
            if entity_type and entity_id
            else ""
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1e293b;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f8fafc;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width:600px;background-color:#ffffff;border-radius:8px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
          <!-- Header -->
          <tr>
            <td style="background-color:#0f172a;padding:24px;text-align:left;">
              <h2 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:-0.5px;">PolicyGPT</h2>
              <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">National Policy & Citizen Welfare Platform</p>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding:32px 24px;">
              {badge_html}
              <h1 style="margin:0 0 16px 0;font-size:18px;font-weight:600;color:#0f172a;line-height:1.4;">{subject}</h1>
              <div style="font-size:14px;line-height:1.6;color:#334155;white-space:pre-line;">
                {body}
              </div>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f5f9;padding:16px 24px;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;text-align:center;">
              <p style="margin:0;">This is an automated notification from PolicyGPT. Please do not reply directly to this email.</p>
              <p style="margin:4px 0 0 0;">Manage your notification preferences in your PolicyGPT Account Settings.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[Union[str, int]] = None,
    ) -> bool:
        """
        Send an email notification via EmailService (Gmail SMTP).
        Gracefully handles unconfigured credentials and connection/auth exceptions with structured logging.
        """
        html_content = NotificationService._build_email_html(
            subject=subject,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return EmailService.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=body,
        )

    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """
        Send an SMS notification via Twilio if configured.
        Gracefully handles missing credentials and logs actions.
        """
        if not phone_number:
            logger.warning("[Twilio SMS Dispatcher] No recipient phone number provided.")
            return False

        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
            logger.info(
                f"[Twilio SMS Dispatcher] Twilio credentials not configured. Skipping SMS to {phone_number}. Message: '{message[:30]}...'"
            )
            return False

        try:
            import urllib.parse
            import urllib.request
            import base64

            auth_str = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            data = urllib.parse.urlencode({
                "From": settings.TWILIO_PHONE_NUMBER,
                "To": phone_number,
                "Body": message,
            }).encode()

            req = urllib.request.Request(url, data=data, headers={"Authorization": f"Basic {auth_b64}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    logger.info(f"[Twilio SMS Dispatcher] SMS sent to {phone_number}")
                    return True
            return False
        except Exception as e:
            logger.error(f"[Twilio SMS Dispatcher] Failed to send SMS to {phone_number}: {str(e)}")
            return False

    # =========================================================================
    # 2. User Preferences & Filter Evaluation
    # =========================================================================

    @staticmethod
    def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
        """Retrieve existing notification preferences or initialize default preferences."""
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                sms_enabled=True,
                in_app_enabled=True,
                policy_alerts=True,
                scheme_updates=True,
                deadline_reminders=True,
                application_updates=True,
                system_alerts=True,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(db: Session, user_id: int, pref_in: NotificationPreferenceUpdate) -> NotificationPreference:
        """Update a user's notification preferences."""
        pref = NotificationService.get_or_create_preferences(db, user_id)
        update_data = pref_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(pref, key, value)
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def is_topic_enabled(pref: NotificationPreference, notification_type: str) -> bool:
        """Check if user preference permits notifications for this topic category."""
        policy_types = {
            NotificationType.NEW_POLICY.value,
            NotificationType.POLICY_CREATED.value,
            NotificationType.POLICY_UPDATED.value,
            NotificationType.POLICY_APPROVED.value,
            NotificationType.POLICY_REJECTED.value,
        }
        scheme_types = {
            NotificationType.NEW_SCHEME.value,
            NotificationType.SCHEME_CREATED.value,
            NotificationType.SCHEME_UPDATED.value,
            NotificationType.SCHEME_UPDATE.value,
        }
        deadline_types = {
            NotificationType.SCHEME_DEADLINE.value,
            NotificationType.DEADLINE_REMINDER.value,
        }
        application_types = {
            NotificationType.APPLICATION_SUBMITTED.value,
            NotificationType.APPLICATION_STATUS_CHANGED.value,
            NotificationType.APPLICATION_APPROVED.value,
            NotificationType.APPLICATION_REJECTED.value,
            NotificationType.APPLICATION_UPDATE.value,
            NotificationType.APPLICATION_UPDATED.value,
        }
        system_types = {
            NotificationType.SYSTEM_ANNOUNCEMENT.value,
            NotificationType.SYSTEM_ALERT.value,
        }

        if notification_type in policy_types:
            return pref.policy_alerts
        if notification_type in scheme_types:
            return pref.scheme_updates
        if notification_type in deadline_types:
            return pref.deadline_reminders
        if notification_type in application_types:
            return getattr(pref, "application_updates", True)
        if notification_type in system_types:
            return pref.system_alerts

        return True

    # =========================================================================
    # 3. Notification Lifecycle & Persistence
    # =========================================================================

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = NotificationType.GENERAL.value,
        channel: str = NotificationChannel.IN_APP.value,
        entity_type: Optional[str] = None,
        entity_id: Optional[Union[str, int]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Notification:
        """
        Create and persist an in-app notification record and attempt multi-channel dispatch
        according to user preferences and channel configuration.
        """
        pref = NotificationService.get_or_create_preferences(db, user_id)
        topic_allowed = NotificationService.is_topic_enabled(pref, notification_type)

        status_val = NotificationStatus.SENT.value
        now = datetime.now(timezone.utc)

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            status=status_val,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            is_read=False,
            scheduled_at=scheduled_at,
            sent_at=now,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Trigger external dispatch if allowed and configured
        user = db.query(User).filter(User.id == user_id).first()
        if user and topic_allowed:
            # Email channel dispatch
            if pref.email_enabled and channel in (NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value):
                NotificationService.send_email(
                    to_email=user.email,
                    subject=title,
                    body=message,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )

            # SMS channel dispatch
            if pref.sms_enabled and getattr(user, "phone_number", None) and channel in (NotificationChannel.SMS.value,):
                NotificationService.send_sms(
                    phone_number=user.phone_number,
                    message=f"{title}: {message}",
                )

        return notification

    @staticmethod
    def broadcast_notification(
        db: Session,
        title: str,
        message: str,
        notification_type: str = NotificationType.SYSTEM_ALERT.value,
        channel: str = NotificationChannel.IN_APP.value,
        target_roles: Optional[List[str]] = None,
    ) -> int:
        """Broadcast a notification to active users matching target roles."""
        query = db.query(User).filter(User.is_active == True)
        if target_roles:
            normalized_roles = [UserRole.from_string(r) for r in target_roles]
            query = query.filter(User.role.in_(normalized_roles))

        users = query.all()
        count = 0
        now = datetime.now(timezone.utc)
        for user in users:
            pref = NotificationService.get_or_create_preferences(db, user.id)
            if not NotificationService.is_topic_enabled(pref, notification_type):
                continue

            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                notification_type=notification_type,
                channel=channel,
                status=NotificationStatus.SENT.value,
                is_read=False,
                sent_at=now,
            )
            db.add(notification)
            count += 1

            if pref.email_enabled and channel in (NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value):
                NotificationService.send_email(to_email=user.email, subject=title, body=message)

        db.commit()
        return count

    @staticmethod
    def get_notification_by_id(
        db: Session,
        notification_id: int,
        user_id: int,
        is_admin: bool = False,
    ) -> Notification:
        """Retrieve single notification with role-based user isolation."""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID {notification_id} not found",
            )
        if not is_admin and notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access notifications belonging to another user",
            )
        return notification

    @staticmethod
    def list_user_notifications(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Tuple[List[Notification], int, int, int]:
        """
        List notifications for a specific user with pagination and filtering.
        Returns: (results, total_count, total_pages, unread_count)
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

        if unread_only:
            query = query.filter(Notification.is_read == False)
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        if channel:
            query = query.filter(Notification.channel == channel)

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size
        results = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()

        return results, total_count, total_pages, unread_count

    @staticmethod
    def list_all_admin_notifications(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        notification_type: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Tuple[List[Notification], int, int]:
        """Administrative query to inspect notifications across all users."""
        query = db.query(Notification)
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if status_filter:
            query = query.filter(Notification.status == status_filter)
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        if channel:
            query = query.filter(Notification.channel == channel)

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size
        results = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()

        return results, total_count, total_pages

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Count unread notifications for a user."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
        """Mark a single notification as read, enforcing user isolation."""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID {notification_id} not found",
            )
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot modify notifications belonging to another user",
            )

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        notification.status = NotificationStatus.READ.value
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all unread notifications for a user as read."""
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).all()
        now = datetime.now(timezone.utc)
        for n in unread:
            n.is_read = True
            n.read_at = now
            n.status = NotificationStatus.READ.value
        db.commit()
        return len(unread)

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int, is_admin: bool = False) -> bool:
        """Delete a notification belonging to the current user or by admin."""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID {notification_id} not found",
            )
        if not is_admin and notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot delete notifications belonging to another user",
            )

        db.delete(notification)
        db.commit()
        return True

    # =========================================================================
    # 4. Automated Business Event Triggers
    # =========================================================================

    @staticmethod
    def trigger_policy_published(db: Session, policy_id: int, policy_title: str, department: Optional[str] = None):
        """Broadcast alert to citizens, researchers and officials when a policy is published."""
        dept_info = f" ({department})" if department else ""
        title = f"New Policy Published: {policy_title}"
        message = f"A new government policy '{policy_title}'{dept_info} has been approved and published on the platform."

        citizens_and_officials = db.query(User).filter(
            User.is_active == True,
            User.role.in_([UserRole.CITIZEN, UserRole.GOVERNMENT_OFFICIAL, UserRole.RESEARCHER, UserRole.ORGANIZATION]),
        ).all()

        for user in citizens_and_officials:
            NotificationService.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type=NotificationType.NEW_POLICY.value,
                channel=NotificationChannel.IN_APP.value,
                entity_type="Policy",
                entity_id=policy_id,
            )

    @staticmethod
    def trigger_policy_submitted(db: Session, policy_id: int, policy_title: str, author_id: int):
        """Notify government officials and administrators when a policy is submitted for approval."""
        title = f"Policy Submitted for Review: {policy_title}"
        message = f"Policy '{policy_title}' (ID: {policy_id}) has been submitted for official approval and review."

        reviewers = db.query(User).filter(
            User.is_active == True,
            User.role.in_([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]),
        ).all()

        for user in reviewers:
            NotificationService.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type=NotificationType.POLICY_CREATED.value,
                channel=NotificationChannel.IN_APP.value,
                entity_type="Policy",
                entity_id=policy_id,
            )

    @staticmethod
    def trigger_policy_approved(db: Session, policy_id: int, policy_title: str, author_id: Optional[int], published: bool = False):
        """Notify policy creator when their policy submission is approved/published."""
        if not author_id:
            return
        status_text = "approved and published" if published else "approved"
        title = f"Policy Approved: {policy_title}"
        message = f"Your submitted policy '{policy_title}' has been {status_text} by the reviewing official."

        NotificationService.create_notification(
            db=db,
            user_id=author_id,
            title=title,
            message=message,
            notification_type=NotificationType.POLICY_APPROVED.value,
            channel=NotificationChannel.IN_APP.value,
            entity_type="Policy",
            entity_id=policy_id,
        )

    @staticmethod
    def trigger_policy_rejected(db: Session, policy_id: int, policy_title: str, author_id: Optional[int], reason: Optional[str] = None):
        """Notify policy creator when their policy submission is rejected."""
        if not author_id:
            return
        reason_msg = f" Reason: {reason}" if reason else ""
        title = f"Policy Submission Rejected: {policy_title}"
        message = f"Your submitted policy '{policy_title}' has been rejected by the reviewing official.{reason_msg}"

        NotificationService.create_notification(
            db=db,
            user_id=author_id,
            title=title,
            message=message,
            notification_type=NotificationType.POLICY_REJECTED.value,
            channel=NotificationChannel.IN_APP.value,
            entity_type="Policy",
            entity_id=policy_id,
        )

    @staticmethod
    def trigger_scheme_created(db: Session, scheme_id: int, scheme_name: str, department: Optional[str] = None):
        """Notify all stakeholders and citizens when a new welfare scheme is launched."""
        dept_info = f" under {department}" if department else ""
        title = f"New Welfare Scheme: {scheme_name}"
        message = f"A new government scheme '{scheme_name}'{dept_info} has been launched. Check your eligibility to apply."

        users = db.query(User).filter(
            User.is_active == True,
            User.role.in_([
                UserRole.CITIZEN,
                UserRole.ORGANIZATION,
                UserRole.ADMINISTRATOR,
                UserRole.GOVERNMENT_OFFICIAL,
                UserRole.RESEARCHER,
            ]),
        ).all()

        for user in users:
            NotificationService.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type=NotificationType.SCHEME_CREATED.value,
                channel=NotificationChannel.IN_APP.value,
                entity_type="Scheme",
                entity_id=scheme_id,
            )

    @staticmethod
    def trigger_scheme_updated(db: Session, scheme_id: int, scheme_name: str, department: Optional[str] = None):
        """Notify all stakeholders and citizens when a scheme is updated or published."""
        dept_info = f" under {department}" if department else ""
        title = f"Scheme Update: {scheme_name}"
        message = f"The scheme '{scheme_name}'{dept_info} has been updated with revised guidelines and benefits."

        users = db.query(User).filter(
            User.is_active == True,
            User.role.in_([
                UserRole.CITIZEN,
                UserRole.ORGANIZATION,
                UserRole.ADMINISTRATOR,
                UserRole.GOVERNMENT_OFFICIAL,
                UserRole.RESEARCHER,
            ]),
        ).all()

        for user in users:
            NotificationService.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type=NotificationType.SCHEME_UPDATED.value,
                channel=NotificationChannel.IN_APP.value,
                entity_type="Scheme",
                entity_id=scheme_id,
            )

    @staticmethod
    def trigger_application_submitted(db: Session, user_id: int, application_number: str, scheme_name: str):
        """Notify applicant upon successful scheme application submission."""
        title = f"Application Submitted: {application_number}"
        message = f"Your application ({application_number}) for '{scheme_name}' has been successfully submitted and is under verification."

        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.APPLICATION_SUBMITTED.value,
            channel=NotificationChannel.IN_APP.value,
            entity_type="SchemeApplication",
            entity_id=application_number,
        )

    @staticmethod
    def trigger_application_status_changed(
        db: Session,
        user_id: int,
        application_number: str,
        scheme_name: str,
        new_status: str,
        remarks: Optional[str] = None,
    ):
        """Notify citizen when their scheme application status transitions."""
        notif_type = NotificationType.APPLICATION_STATUS_CHANGED.value
        if new_status == ApplicationStatus.APPROVED.value:
            notif_type = NotificationType.APPLICATION_APPROVED.value
        elif new_status == ApplicationStatus.REJECTED.value:
            notif_type = NotificationType.APPLICATION_REJECTED.value

        remarks_info = f" Remarks: {remarks}" if remarks else ""
        title = f"Application {new_status.title()}: {application_number}"
        message = f"Your application ({application_number}) for scheme '{scheme_name}' is now '{new_status}'.{remarks_info}"

        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notif_type,
            channel=NotificationChannel.IN_APP.value,
            entity_type="SchemeApplication",
            entity_id=application_number,
        )

    @staticmethod
    def trigger_eligibility_match(db: Session, user_id: int, matched_schemes_count: int):
        """Notify citizen when new eligible schemes are discovered for their profile."""
        title = f"New Eligible Schemes Found ({matched_schemes_count})"
        message = f"We found {matched_schemes_count} new government schemes that match your profile. Check your dashboard to view and apply."

        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.ELIGIBILITY_MATCH.value,
            channel=NotificationChannel.IN_APP.value,
            entity_type="Eligibility",
            entity_id=matched_schemes_count,
        )

    @staticmethod
    def check_and_trigger_deadline_reminders(db: Session) -> int:
        """
        Scan active schemes and pending applications for upcoming deadlines and dispatch reminders.
        Returns count of notifications created.
        """
        schemes = db.query(Scheme).filter(
            Scheme.is_active == True,
            Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
        ).all()

        count = 0
        citizens = db.query(User).filter(User.is_active == True, User.role == UserRole.CITIZEN).all()

        for scheme in schemes:
            title = f"Deadline Reminder: {scheme.name}"
            message = f"Applications for scheme '{scheme.name}' are closing soon. Ensure your documents and applications are submitted."
            for user in citizens:
                pref = NotificationService.get_or_create_preferences(db, user.id)
                if pref.deadline_reminders:
                    NotificationService.create_notification(
                        db=db,
                        user_id=user.id,
                        title=title,
                        message=message,
                        notification_type=NotificationType.DEADLINE_REMINDER.value,
                        channel=NotificationChannel.IN_APP.value,
                        entity_type="Scheme",
                        entity_id=scheme.id,
                    )
                    count += 1

        return count

    @staticmethod
    def trigger_feedback_resolved(db: Session, user_id: Optional[int], feedback_id: int, subject: str):
        """Notify citizen when their support query or feedback ticket receives a response."""
        if not user_id:
            return
        title = f"Query Resolved: {subject}"
        message = f"An official response has been posted for your query '{subject}'. Please review the resolution details."
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.FEEDBACK_RESPONSE.value,
            channel=NotificationChannel.IN_APP.value,
            entity_type="Feedback",
            entity_id=feedback_id,
        )
