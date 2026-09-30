import math
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session, joinedload
from app.models.policy import Policy
from app.models.scheme import Scheme, SchemeStatus
from app.models.eligibility import EligibilityRule
from app.models.user import User, UserRole
from app.schemas.scheme import SchemeCreate, SchemeUpdate, EligibilityRuleCreate
from app.services.activity_service import ActivityService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class SchemeService:
    @staticmethod
    def create_scheme(db: Session, scheme_in: SchemeCreate, current_user: User) -> Scheme:
        """Create a new public scheme record with optional attached eligibility rules."""
        scheme_data = scheme_in.model_dump()
        rules_data = scheme_data.pop("eligibility_rules", None)
        initial_status = scheme_data.pop("status", SchemeStatus.ACTIVE) or SchemeStatus.ACTIVE
        if isinstance(initial_status, SchemeStatus):
            initial_status = initial_status.value

        # Verify parent policy exists if policy_id provided
        if scheme_data.get("policy_id"):
            policy = db.query(Policy).filter(Policy.id == scheme_data["policy_id"]).first()
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent Policy with ID {scheme_data['policy_id']} does not exist",
                )

        scheme = Scheme(
            **scheme_data,
            status=initial_status,
            created_by_id=current_user.id,
        )
        db.add(scheme)
        db.flush()

        # Add any initial eligibility rules
        if rules_data:
            for rule_dict in rules_data:
                rule = EligibilityRule(
                    scheme_id=scheme.id,
                    rule_name=rule_dict["rule_name"],
                    criteria_json=rule_dict.get("criteria_json"),
                    description=rule_dict.get("description"),
                    is_active=rule_dict.get("is_active", True),
                )
                db.add(rule)

        AuditService.log(
            db=db,
            action="SCHEME_CREATED",
            entity_type="Scheme",
            entity_id=str(scheme.id),
            user_id=current_user.id,
            details=f"Scheme '{scheme.name}' created with category '{scheme.category}'",
        )
        ActivityService.log_activity(
            db=db,
            event_type="SCHEME_CREATED",
            user_id=current_user.id,
            resource_type="Scheme",
            resource_id=str(scheme.id),
            details={"name": scheme.name, "status": scheme.status, "department": scheme.department},
        )
        NotificationService.trigger_scheme_created(
            db=db,
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            department=scheme.department,
        )
        db.commit()
        db.refresh(scheme)
        return scheme

    @staticmethod
    def get_scheme(db: Session, scheme_id: int, current_user: Optional[User] = None) -> Scheme:
        """Retrieve a single scheme with its eligibility rules, applying RBAC visibility."""
        scheme = (
            db.query(Scheme)
            .options(joinedload(Scheme.eligibility_rules))
            .filter(Scheme.id == scheme_id)
            .first()
        )
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {scheme_id} not found",
            )

        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            if not scheme.is_active or scheme.status in (SchemeStatus.ARCHIVED.value, SchemeStatus.INACTIVE.value):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scheme with ID {scheme_id} not found or inactive",
                )

        return scheme

    @staticmethod
    def list_schemes(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        department: Optional[str] = None,
        state: Optional[str] = None,
        policy_id: Optional[int] = None,
        keyword: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user: Optional[User] = None,
    ) -> Tuple[List[Scheme], int, int]:
        """List schemes with filtering, pagination, sorting, and RBAC visibility."""
        query = db.query(Scheme)

        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            query = query.filter(
                Scheme.is_active == True,
                Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
            )
        else:
            if status_filter:
                query = query.filter(Scheme.status.ilike(status_filter.strip()))

        if category:
            query = query.filter(Scheme.category.ilike(f"%{category.strip()}%"))
        if department:
            query = query.filter(Scheme.department.ilike(f"%{department.strip()}%"))
        if state:
            query = query.filter(Scheme.state.ilike(f"%{state.strip()}%"))
        if policy_id is not None:
            query = query.filter(Scheme.policy_id == policy_id)
        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(or_(Scheme.name.ilike(kw), Scheme.description.ilike(kw)))

        # Sorting
        sort_col = getattr(Scheme, sort_by, Scheme.created_at)
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
    def update_scheme(
        db: Session,
        scheme_id: int,
        scheme_in: SchemeUpdate,
        current_user: User,
    ) -> Scheme:
        """Update scheme details (Admin or Government Official)."""
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {scheme_id} not found",
            )

        update_data = scheme_in.model_dump(exclude_unset=True)

        if "policy_id" in update_data and update_data["policy_id"] is not None:
            policy = db.query(Policy).filter(Policy.id == update_data["policy_id"]).first()
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent Policy with ID {update_data['policy_id']} does not exist",
                )

        if "status" in update_data and update_data["status"] is not None:
            if isinstance(update_data["status"], SchemeStatus):
                update_data["status"] = update_data["status"].value

        for key, value in update_data.items():
            setattr(scheme, key, value)

        AuditService.log(
            db=db,
            action="SCHEME_UPDATED",
            entity_type="Scheme",
            entity_id=str(scheme.id),
            user_id=current_user.id,
            details=f"Updated scheme '{scheme.name}' fields: {list(update_data.keys())}",
        )
        ActivityService.log_activity(
            db=db,
            event_type="SCHEME_UPDATED",
            user_id=current_user.id,
            resource_type="Scheme",
            resource_id=str(scheme.id),
            details={"name": scheme.name, "updated_fields": list(update_data.keys())},
        )
        NotificationService.trigger_scheme_updated(
            db=db,
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            department=scheme.department,
        )
        db.commit()
        db.refresh(scheme)
        return scheme

    @staticmethod
    def archive_scheme(db: Session, scheme_id: int, current_user: User) -> Scheme:
        """Soft-delete / archive a scheme."""
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {scheme_id} not found",
            )

        scheme.is_active = False
        scheme.status = SchemeStatus.ARCHIVED.value

        AuditService.log(
            db=db,
            action="SCHEME_ARCHIVED",
            entity_type="Scheme",
            entity_id=str(scheme.id),
            user_id=current_user.id,
            details=f"Archived scheme '{scheme.name}'",
        )
        db.commit()
        db.refresh(scheme)
        return scheme

    # --- Eligibility Rules Operations ---
    @staticmethod
    def add_eligibility_rule(
        db: Session,
        scheme_id: int,
        rule_in: EligibilityRuleCreate,
        current_user: User,
    ) -> EligibilityRule:
        """Add an eligibility rule to a scheme."""
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID {scheme_id} not found",
            )

        rule = EligibilityRule(
            scheme_id=scheme.id,
            rule_name=rule_in.rule_name,
            criteria_json=rule_in.criteria_json,
            description=rule_in.description,
            is_active=rule_in.is_active,
        )
        db.add(rule)
        db.flush()

        AuditService.log(
            db=db,
            action="RULE_ADDED",
            entity_type="EligibilityRule",
            entity_id=str(rule.id),
            user_id=current_user.id,
            details=f"Added rule '{rule.rule_name}' to scheme ID {scheme_id}",
        )
        db.commit()
        db.refresh(rule)
        return rule
