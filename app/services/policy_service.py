from datetime import datetime, timezone
import math
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session
from app.models.policy import Policy, PolicyStatus
from app.models.user import User, UserRole
from app.schemas.policy import PolicyCreate, PolicyUpdate
from app.services.activity_service import ActivityService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class PolicyService:
    @staticmethod
    def create_policy(db: Session, policy_in: PolicyCreate, current_user: User) -> Policy:
        """Create a new policy record."""
        policy_data = policy_in.model_dump()
        initial_status = policy_data.pop("status", PolicyStatus.DRAFT) or PolicyStatus.DRAFT
        if isinstance(initial_status, PolicyStatus):
            initial_status = initial_status.value

        policy = Policy(
            **policy_data,
            status=initial_status,
            created_by_id=current_user.id,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action="POLICY_CREATED",
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Policy '{policy.title}' created with status '{policy.status}'",
        )
        ActivityService.log_activity(
            db=db,
            event_type="POLICY_CREATED",
            user_id=current_user.id,
            resource_type="Policy",
            resource_id=str(policy.id),
            details={"title": policy.title, "status": policy.status, "department": policy.department},
        )
        if policy.status == PolicyStatus.PUBLISHED.value:
            NotificationService.trigger_policy_published(
                db=db,
                policy_id=policy.id,
                policy_title=policy.title,
                department=policy.department,
            )
        elif policy.status == PolicyStatus.PENDING_APPROVAL.value:
            NotificationService.trigger_policy_submitted(
                db=db,
                policy_id=policy.id,
                policy_title=policy.title,
                author_id=current_user.id,
            )
        return policy

    @staticmethod
    def get_policy(db: Session, policy_id: int, current_user: Optional[User] = None) -> Policy:
        """Retrieve a single policy by ID, applying RBAC visibility rules."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        # RBAC Check: Citizens, guests, and unauthenticated users can only view active & published policies
        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            if not policy.is_active or policy.status not in (PolicyStatus.PUBLISHED.value, PolicyStatus.APPROVED.value):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Policy with ID {policy_id} not found or not published",
                )

        return policy

    @staticmethod
    def list_policies(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        department: Optional[str] = None,
        state: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user: Optional[User] = None,
    ) -> Tuple[List[Policy], int, int]:
        """List policies with filtering, pagination, sorting, and RBAC visibility."""
        query = db.query(Policy)

        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            # Public / Citizens can only see active and published policies
            query = query.filter(
                Policy.is_active == True,
                Policy.status.in_([PolicyStatus.PUBLISHED.value, PolicyStatus.APPROVED.value]),
            )
        else:
            if status_filter:
                query = query.filter(Policy.status.ilike(status_filter.strip()))

        if category:
            query = query.filter(Policy.category.ilike(f"%{category.strip()}%"))
        if department:
            query = query.filter(Policy.department.ilike(f"%{department.strip()}%"))
        if state:
            query = query.filter(Policy.state.ilike(f"%{state.strip()}%"))
        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(or_(Policy.title.ilike(kw), Policy.description.ilike(kw)))

        # Sorting
        sort_col = getattr(Policy, sort_by, Policy.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        total_count = query.count()
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        return results, total_count, total_pages

    @staticmethod
    def update_policy(
        db: Session,
        policy_id: int,
        policy_in: PolicyUpdate,
        current_user: User,
    ) -> Policy:
        """Update policy attributes (Admin or Government Official)."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        update_data = policy_in.model_dump(exclude_unset=True)
        if "status" in update_data and update_data["status"] is not None:
            if isinstance(update_data["status"], PolicyStatus):
                update_data["status"] = update_data["status"].value

        old_status = policy.status
        for key, value in update_data.items():
            setattr(policy, key, value)

        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action="POLICY_UPDATED",
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Updated policy '{policy.title}' fields: {list(update_data.keys())}",
        )

        if "status" in update_data and update_data["status"] != old_status:
            if policy.status == PolicyStatus.PENDING_APPROVAL.value:
                NotificationService.trigger_policy_submitted(
                    db=db,
                    policy_id=policy.id,
                    policy_title=policy.title,
                    author_id=current_user.id,
                )
            elif policy.status == PolicyStatus.PUBLISHED.value:
                NotificationService.trigger_policy_published(
                    db=db,
                    policy_id=policy.id,
                    policy_title=policy.title,
                    department=policy.department,
                )

        return policy

    @staticmethod
    def archive_policy(db: Session, policy_id: int, current_user: User) -> Policy:
        """Soft-delete / archive a policy."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        policy.is_active = False
        policy.status = PolicyStatus.ARCHIVED.value
        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action="POLICY_ARCHIVED",
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Archived policy '{policy.title}'",
        )
        return policy

    # --- Approval Workflow ---
    @staticmethod
    def submit_for_approval(db: Session, policy_id: int, current_user: User) -> Policy:
        """Submit a policy for review (DRAFT or REJECTED -> PENDING_APPROVAL)."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        valid_source_statuses = (PolicyStatus.DRAFT.value, PolicyStatus.REJECTED.value)
        if policy.status not in valid_source_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: Cannot submit policy with current status '{policy.status}'. Policy must be in DRAFT or REJECTED status.",
            )

        policy.status = PolicyStatus.PENDING_APPROVAL.value
        policy.rejection_reason = None  # Clear previous rejection remarks
        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action="POLICY_SUBMITTED",
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Policy '{policy.title}' submitted for approval",
        )
        NotificationService.trigger_policy_submitted(
            db=db,
            policy_id=policy.id,
            policy_title=policy.title,
            author_id=current_user.id,
        )
        return policy

    @staticmethod
    def approve_policy(
        db: Session,
        policy_id: int,
        current_user: User,
        publish: bool = False,
    ) -> Policy:
        """Approve a policy (PENDING_APPROVAL -> APPROVED or PUBLISHED)."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        if policy.status != PolicyStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: Cannot approve policy with status '{policy.status}'. Policy must be in PENDING_APPROVAL status.",
            )

        if publish:
            policy.status = PolicyStatus.PUBLISHED.value
            policy.publication_date = datetime.now(timezone.utc)
            action_name = "POLICY_PUBLISHED"
        else:
            policy.status = PolicyStatus.APPROVED.value
            action_name = "POLICY_APPROVED"

        policy.approved_by_id = current_user.id
        policy.rejection_reason = None
        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action=action_name,
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Policy '{policy.title}' transitioned to '{policy.status}' by user {current_user.id}",
        )
        ActivityService.log_activity(
            db=db,
            event_type=action_name,
            user_id=current_user.id,
            resource_type="Policy",
            resource_id=str(policy.id),
            details={"title": policy.title, "status": policy.status},
        )
        NotificationService.trigger_policy_approved(
            db=db,
            policy_id=policy.id,
            policy_title=policy.title,
            author_id=policy.created_by_id,
            published=publish,
        )
        if publish:
            NotificationService.trigger_policy_published(
                db=db,
                policy_id=policy.id,
                policy_title=policy.title,
                department=policy.department,
            )
        return policy

    @staticmethod
    def reject_policy(
        db: Session,
        policy_id: int,
        current_user: User,
        reason: Optional[str] = None,
    ) -> Policy:
        """Reject a policy (PENDING_APPROVAL -> REJECTED)."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID {policy_id} not found",
            )

        if policy.status != PolicyStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: Cannot reject policy with status '{policy.status}'. Policy must be in PENDING_APPROVAL status.",
            )

        policy.status = PolicyStatus.REJECTED.value
        policy.rejection_reason = reason
        policy.approved_by_id = current_user.id
        db.commit()
        db.refresh(policy)

        AuditService.log(
            db=db,
            action="POLICY_REJECTED",
            entity_type="Policy",
            entity_id=str(policy.id),
            user_id=current_user.id,
            details=f"Policy '{policy.title}' rejected. Reason: {reason}",
        )
        NotificationService.trigger_policy_rejected(
            db=db,
            policy_id=policy.id,
            policy_title=policy.title,
            author_id=policy.created_by_id,
            reason=reason,
        )
        return policy
