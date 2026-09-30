from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from app.models.application import ApplicationStatus, SchemeApplication
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.policy import Policy
from app.models.report import Report
from app.models.saved_policy import SavedPolicy
from app.models.scheme import Scheme
from app.models.search_history import SearchHistory
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardResponse,
    AdminReportsSummary,
    ApplicationStatusItem,
    AuditLogItem,
    CitizenDashboardResponse,
    CitizenNotificationItem,
    CitizenSearchHistoryItem,
    GovernmentDashboardResponse,
    SavedPolicyItem,
)
from app.schemas.eligibility import EligibilityCheckRequest
from app.services.analytics_service import AnalyticsService
from app.services.eligibility_service import EligibilityService
from app.services.notification_service import NotificationService


class DashboardService:
    # ==========================================
    # 1. CITIZEN DASHBOARD
    # ==========================================

    @staticmethod
    def get_citizen_dashboard(db: Session, current_user: User) -> CitizenDashboardResponse:
        """
        Aggregate personalized dashboard data strictly for the authenticated Citizen.
        - Saved Policies & Schemes
        - Eligible Schemes (via EligibilityService)
        - Recent Notifications
        - Search History
        - Scheme Application Statuses
        """
        # 1. Saved Policies & Schemes (User Isolation)
        saved_records = (
            db.query(SavedPolicy)
            .options(joinedload(SavedPolicy.policy), joinedload(SavedPolicy.scheme))
            .filter(SavedPolicy.user_id == current_user.id)
            .order_by(desc(SavedPolicy.created_at))
            .all()
        )
        saved_policies: List[SavedPolicyItem] = []
        for sp in saved_records:
            if sp.policy:
                saved_policies.append(
                    SavedPolicyItem(
                        id=sp.id,
                        policy_id=sp.policy.id,
                        scheme_id=None,
                        item_type="policy",
                        title=sp.policy.title,
                        category=sp.policy.category,
                        department=sp.policy.department,
                        ministry=sp.policy.ministry,
                        state=sp.policy.state,
                        sector=sp.policy.sector,
                        status=sp.policy.status,
                        saved_at=sp.created_at,
                        notes=sp.notes,
                    )
                )
            elif sp.scheme:
                saved_policies.append(
                    SavedPolicyItem(
                        id=sp.id,
                        policy_id=None,
                        scheme_id=sp.scheme.id,
                        item_type="scheme",
                        title=sp.scheme.name,
                        category=sp.scheme.category,
                        department=sp.scheme.department,
                        ministry=sp.scheme.ministry,
                        state=sp.scheme.state,
                        sector=sp.scheme.sector,
                        status=sp.scheme.status,
                        saved_at=sp.created_at,
                        notes=sp.notes,
                    )
                )

        # 2. Eligible Schemes (Reuse EligibilityService without duplicating logic)
        eligibility_response = EligibilityService.check_eligibility(
            db=db,
            profile=EligibilityCheckRequest(),
        )
        eligible_schemes = eligibility_response.eligible_schemes

        # 3. Recent Notifications (User Isolation - limit 10)
        notif_records = (
            db.query(Notification)
            .filter(Notification.user_id == current_user.id)
            .order_by(desc(Notification.created_at))
            .limit(10)
            .all()
        )
        recent_notifications = [
            CitizenNotificationItem(
                id=n.id,
                title=n.title,
                message=n.message,
                notification_type=n.notification_type,
                channel=n.channel,
                status=n.status,
                is_read=n.is_read,
                created_at=n.created_at,
                entity_type=n.entity_type,
                entity_id=n.entity_id,
            )
            for n in notif_records
        ]

        # 4. Search History (User Isolation - limit 10)
        search_records = (
            db.query(SearchHistory)
            .filter(SearchHistory.user_id == current_user.id)
            .order_by(desc(SearchHistory.created_at))
            .limit(10)
            .all()
        )
        search_history = [
            CitizenSearchHistoryItem(
                id=s.id,
                query=s.query,
                filters_json=s.filters_json,
                result_count=s.result_count,
                created_at=s.created_at,
            )
            for s in search_records
        ]

        # 5. Application Statuses (User Isolation - limit 10)
        app_records = (
            db.query(SchemeApplication)
            .options(joinedload(SchemeApplication.scheme))
            .filter(SchemeApplication.user_id == current_user.id)
            .order_by(desc(SchemeApplication.created_at))
            .limit(10)
            .all()
        )
        application_status: List[ApplicationStatusItem] = []
        for app_item in app_records:
            scheme_name = app_item.scheme.name if app_item.scheme else f"Scheme #{app_item.scheme_id}"
            application_status.append(
                ApplicationStatusItem(
                    id=app_item.id,
                    scheme_id=app_item.scheme_id,
                    scheme_name=scheme_name,
                    application_number=app_item.application_number,
                    status=app_item.status,
                    details_json=app_item.details_json,
                    remarks=app_item.remarks,
                    created_at=app_item.created_at,
                    updated_at=app_item.updated_at,
                )
            )

        return CitizenDashboardResponse(
            saved_policies=saved_policies,
            eligible_schemes=eligible_schemes,
            recent_notifications=recent_notifications,
            search_history=search_history,
            application_status=application_status,
        )

    # --- Citizen Helper Management Operations ---

    @staticmethod
    def save_policy(
        db: Session,
        user_id: int,
        policy_id: Optional[int] = None,
        scheme_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> SavedPolicy:
        """Save/bookmark a policy or scheme for a citizen."""
        if not policy_id and not scheme_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either policy_id or scheme_id must be provided",
            )

        if policy_id:
            policy = db.query(Policy).filter(Policy.id == policy_id, Policy.is_active == True).first()
            if not policy:
                # Also check if it might be a scheme if policy wasn't found
                scheme = db.query(Scheme).filter(Scheme.id == policy_id, Scheme.is_active == True).first()
                if scheme:
                    scheme_id = policy_id
                    policy_id = None
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Policy with ID {policy_id} not found",
                    )

        if scheme_id:
            scheme = db.query(Scheme).filter(Scheme.id == scheme_id, Scheme.is_active == True).first()
            if not scheme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scheme with ID {scheme_id} not found",
                )
            existing = db.query(SavedPolicy).filter(
                SavedPolicy.user_id == user_id,
                SavedPolicy.scheme_id == scheme_id,
            ).first()
            if existing:
                if notes is not None:
                    existing.notes = notes
                    db.commit()
                    db.refresh(existing)
                return existing

            saved = SavedPolicy(
                user_id=user_id,
                scheme_id=scheme_id,
                policy_id=None,
                notes=notes,
            )
            db.add(saved)
            db.commit()
            db.refresh(saved)
            return saved

        # Save policy
        existing = db.query(SavedPolicy).filter(
            SavedPolicy.user_id == user_id,
            SavedPolicy.policy_id == policy_id,
        ).first()
        if existing:
            if notes is not None:
                existing.notes = notes
                db.commit()
                db.refresh(existing)
            return existing

        saved = SavedPolicy(
            user_id=user_id,
            policy_id=policy_id,
            scheme_id=None,
            notes=notes,
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    @staticmethod
    def remove_saved_policy(db: Session, user_id: int, item_id: int) -> bool:
        """Remove a saved policy or scheme bookmark for a citizen."""
        saved = db.query(SavedPolicy).filter(
            SavedPolicy.user_id == user_id,
            (SavedPolicy.policy_id == item_id) | (SavedPolicy.scheme_id == item_id) | (SavedPolicy.id == item_id)
        ).first()
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved item record not found",
            )
        db.delete(saved)
        db.commit()
        return True

    @staticmethod
    def submit_application(
        db: Session,
        user_id: int,
        scheme_id: int,
        details_json: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> SchemeApplication:
        """Submit a scheme application for tracking."""
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id, Scheme.is_active == True).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {scheme_id} not found",
            )

        app_num = f"APP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        app_item = SchemeApplication(
            user_id=user_id,
            scheme_id=scheme_id,
            application_number=app_num,
            status=ApplicationStatus.SUBMITTED.value,
            details_json=details_json,
            remarks=remarks,
        )
        db.add(app_item)
        NotificationService.trigger_application_submitted(
            db=db,
            user_id=user_id,
            application_number=app_num,
            scheme_name=scheme.name,
        )
        db.commit()
        db.refresh(app_item)
        return app_item

    # ==========================================
    # 2. GOVERNMENT OFFICIAL DASHBOARD
    # ==========================================

    @staticmethod
    def get_government_dashboard(db: Session, current_user: User) -> GovernmentDashboardResponse:
        policy_stats = AnalyticsService.get_policy_analytics(db=db)
        scheme_usage = AnalyticsService.get_scheme_analytics(db=db)
        user_activity = AnalyticsService.get_usage_statistics(db=db)
        dept_analytics_resp = AnalyticsService.get_department_analytics(db=db)
        notification_stats = AnalyticsService.get_notification_analytics(db=db)

        return GovernmentDashboardResponse(
            policy_statistics=policy_stats,
            scheme_usage=scheme_usage,
            user_activity=user_activity,
            department_reports=dept_analytics_resp.departments,
            notification_statistics=notification_stats,
        )

    # ==========================================
    # 3. ADMIN DASHBOARD
    # ==========================================

    @staticmethod
    def get_admin_dashboard(db: Session, current_user: User) -> AdminDashboardResponse:
        user_mgmt = AnalyticsService.get_user_analytics(db=db)
        policy_mgmt = AnalyticsService.get_policy_analytics(db=db)
        overview_analytics = AnalyticsService.get_overview_analytics(db=db)

        total_reports = db.query(Report).count()
        recent_report_rows = (
            db.query(Report)
            .order_by(desc(Report.created_at))
            .limit(5)
            .all()
        )
        recent_reports = [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type,
                "file_format": r.file_format,
                "status": r.status,
                "record_count": r.record_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_report_rows
        ]
        reports_summary = AdminReportsSummary(
            total_reports_generated=total_reports,
            recent_reports=recent_reports,
        )

        audit_rows = (
            db.query(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(20)
            .all()
        )
        user_ids = {a.user_id for a in audit_rows if a.user_id is not None}
        user_map = {}
        if user_ids:
            users = db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
            user_map = {u.id: u.email for u in users}

        audit_logs = [
            AuditLogItem(
                id=a.id,
                user_id=a.user_id,
                user_email=user_map.get(a.user_id) if a.user_id else None,
                action=a.action,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                details=a.details,
                ip_address=a.ip_address,
                created_at=a.created_at,
            )
            for a in audit_rows
        ]

        return AdminDashboardResponse(
            user_management=user_mgmt,
            policy_management=policy_mgmt,
            analytics=overview_analytics,
            reports=reports_summary,
            audit_logs=audit_logs,
        )
