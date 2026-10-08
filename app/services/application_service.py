from datetime import datetime, timezone
import math
import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.application import ApplicationStatus, SchemeApplication
from app.models.scheme import Scheme
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicantSummary,
    ApplicationCreate,
    ApplicationPaginationResponse,
    ApplicationRead,
    ApplicationStatusUpdate,
    SchemeSummary,
)
from app.services.notification_service import NotificationService


class ApplicationService:
    @staticmethod
    def _map_to_read(app: SchemeApplication) -> ApplicationRead:
        scheme_name = app.scheme.name if app.scheme else f"Scheme #{app.scheme_id}"
        scheme_summary = None
        if app.scheme:
            scheme_summary = SchemeSummary(
                id=app.scheme.id,
                name=app.scheme.name,
                category=app.scheme.category,
                department=app.scheme.department,
                ministry=app.scheme.ministry,
                state=app.scheme.state,
                sector=app.scheme.sector,
                benefits=app.scheme.benefits,
            )

        applicant_summary = None
        if app.user:
            applicant_summary = ApplicantSummary(
                id=app.user.id,
                name=app.user.name,
                email=app.user.email,
                phone_number=app.user.phone_number,
                state=app.user.state,
                age=app.user.age,
                role=app.user.role.value if hasattr(app.user.role, 'value') else str(app.user.role),
            )

        reviewed_by_name = None
        if app.reviewed_by:
            reviewed_by_name = app.reviewed_by.name

        return ApplicationRead(
            id=app.id,
            application_number=app.application_number,
            user_id=app.user_id,
            scheme_id=app.scheme_id,
            scheme_name=scheme_name,
            status=app.status,
            details_json=app.details_json,
            remarks=app.remarks,
            reviewed_by_id=app.reviewed_by_id,
            reviewed_by_name=reviewed_by_name,
            reviewed_at=app.reviewed_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
            scheme=scheme_summary,
            applicant=applicant_summary,
        )

    @staticmethod
    def create_application(
        db: Session,
        current_user: User,
        payload: ApplicationCreate,
    ) -> ApplicationRead:
        """Create a new scheme application submitted by a Citizen."""
        scheme = db.query(Scheme).filter(Scheme.id == payload.scheme_id, Scheme.is_active == True).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {payload.scheme_id} not found",
            )

        # Generate standard application reference number
        app_num = f"APP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        app_item = SchemeApplication(
            user_id=current_user.id,
            scheme_id=scheme.id,
            application_number=app_num,
            status=ApplicationStatus.SUBMITTED.value,
            details_json=payload.details_json,
            remarks=payload.remarks,
        )
        db.add(app_item)
        db.commit()
        db.refresh(app_item)

        # Trigger notification
        NotificationService.trigger_application_submitted(
            db=db,
            user_id=current_user.id,
            application_number=app_num,
            scheme_name=scheme.name,
            department=scheme.department,
        )

        # Re-query with relationships loaded
        loaded = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
                joinedload(SchemeApplication.reviewed_by),
            )
            .filter(SchemeApplication.id == app_item.id)
            .first()
        )
        return ApplicationService._map_to_read(loaded)

    @staticmethod
    def list_applications(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        scheme_id: Optional[int] = None,
        department: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[ApplicationRead], int, int]:
        """
        List applications with RBAC scoping and multi-attribute filters.
        - Citizen: only their own applications.
        - Government Official: scoped to schemes in their department / state or all allowed.
        - Administrator: all platform applications.
        """
        query = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
                joinedload(SchemeApplication.reviewed_by),
            )
            .join(Scheme, SchemeApplication.scheme_id == Scheme.id)
            .join(User, SchemeApplication.user_id == User.id)
        )

        # RBAC Scoping
        is_admin = current_user.role == UserRole.ADMINISTRATOR
        is_official = current_user.role == UserRole.GOVERNMENT_OFFICIAL

        if not is_admin and not is_official:
            # Citizens / Public users can ONLY see their own applications
            query = query.filter(SchemeApplication.user_id == current_user.id)
        elif is_official:
            # If official has a specific state, scope to All-India + their state schemes
            if current_user.state and current_user.state.strip():
                state_val = current_user.state.strip()
                query = query.filter(
                    or_(
                        Scheme.state == None,
                        Scheme.state == "",
                        Scheme.state.ilike("%All India%"),
                        Scheme.state.ilike("%Central%"),
                        Scheme.state.ilike(f"%{state_val}%"),
                    )
                )

        # Filter by status
        if status_filter:
            clean_status = status_filter.strip().upper().replace(" ", "_")
            query = query.filter(func.upper(SchemeApplication.status) == clean_status)

        # Filter by scheme ID
        if scheme_id:
            query = query.filter(SchemeApplication.scheme_id == scheme_id)

        # Filter by department
        if department:
            query = query.filter(Scheme.department.ilike(f"%{department.strip()}%"))

        # Keyword search across application number, scheme name, user name, email, remarks
        if keyword:
            term = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    SchemeApplication.application_number.ilike(term),
                    Scheme.name.ilike(term),
                    User.name.ilike(term),
                    User.email.ilike(term),
                    SchemeApplication.remarks.ilike(term),
                )
            )

        total_count = query.count()
        total_pages = max(1, math.ceil(total_count / page_size))

        # Sorting
        sort_column = getattr(SchemeApplication, sort_by, SchemeApplication.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        items = query.offset((page - 1) * page_size).limit(page_size).all()
        results = [ApplicationService._map_to_read(it) for it in items]

        return results, total_count, total_pages

    @staticmethod
    def get_application_by_id(
        db: Session,
        application_id: int,
        current_user: User,
    ) -> ApplicationRead:
        """Retrieve single application by ID with strict ownership/RBAC validation."""
        app_item = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
                joinedload(SchemeApplication.reviewed_by),
            )
            .filter(SchemeApplication.id == application_id)
            .first()
        )
        if not app_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found",
            )

        is_privileged = current_user.role in (UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL)
        if not is_privileged and app_item.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access applications belonging to other citizens",
            )

        return ApplicationService._map_to_read(app_item)

    @staticmethod
    def update_application_status(
        db: Session,
        application_id: int,
        payload: ApplicationStatusUpdate,
        current_user: User,
    ) -> ApplicationRead:
        """Update scheme application status (Official / Admin only)."""
        app_item = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
            )
            .filter(SchemeApplication.id == application_id)
            .first()
        )
        if not app_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found",
            )

        old_status = app_item.status
        new_status = payload.status.value
        app_item.status = new_status
        if payload.remarks:
            app_item.remarks = payload.remarks
        elif payload.rejection_reason and new_status == ApplicationStatus.REJECTED.value:
            app_item.remarks = f"Rejected: {payload.rejection_reason}"

        app_item.reviewed_by_id = current_user.id
        app_item.reviewed_at = datetime.now(timezone.utc)
        app_item.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(app_item)

        # Notify Citizen about the status update
        scheme_name = app_item.scheme.name if app_item.scheme else f"Scheme #{app_item.scheme_id}"
        NotificationService.trigger_application_status_changed(
            db=db,
            user_id=app_item.user_id,
            application_number=app_item.application_number,
            scheme_name=scheme_name,
            new_status=new_status,
            remarks=app_item.remarks,
        )

        # Reload with reviewer
        loaded = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
                joinedload(SchemeApplication.reviewed_by),
            )
            .filter(SchemeApplication.id == application_id)
            .first()
        )
        return ApplicationService._map_to_read(loaded)

    @staticmethod
    def withdraw_application(
        db: Session,
        application_id: int,
        current_user: User,
        reason: Optional[str] = None,
    ) -> ApplicationRead:
        """Allow a citizen to withdraw their own application."""
        app_item = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
            )
            .filter(SchemeApplication.id == application_id)
            .first()
        )
        if not app_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found",
            )

        if app_item.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot withdraw an application submitted by another user",
            )

        if app_item.status in (ApplicationStatus.APPROVED.value, ApplicationStatus.DISBURSED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot withdraw an application that has already reached '{app_item.status}' status",
            )

        app_item.status = ApplicationStatus.WITHDRAWN.value
        app_item.remarks = f"Withdrawn by applicant. Reason: {reason}" if reason else "Withdrawn by applicant"
        app_item.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(app_item)

        scheme_name = app_item.scheme.name if app_item.scheme else f"Scheme #{app_item.scheme_id}"
        NotificationService.trigger_application_status_changed(
            db=db,
            user_id=app_item.user_id,
            application_number=app_item.application_number,
            scheme_name=scheme_name,
            new_status=ApplicationStatus.WITHDRAWN.value,
            remarks=app_item.remarks,
        )

        loaded = (
            db.query(SchemeApplication)
            .options(
                joinedload(SchemeApplication.scheme),
                joinedload(SchemeApplication.user),
                joinedload(SchemeApplication.reviewed_by),
            )
            .filter(SchemeApplication.id == application_id)
            .first()
        )
        return ApplicationService._map_to_read(loaded)
