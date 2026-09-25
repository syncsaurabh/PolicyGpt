from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.models.user import User, UserRole
from app.schemas.comparison import ComparisonItem, ComparisonRequest, ComparisonResponse


class ComparisonService:
    @staticmethod
    def compare(
        db: Session,
        req: ComparisonRequest,
        current_user: Optional[User] = None,
    ) -> ComparisonResponse:
        """Compare 2 to 3 policies or schemes side-by-side with RBAC enforcement."""
        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if req.scheme_ids:
            raw_ids = req.scheme_ids
            int_ids: List[int] = []
            for i in raw_ids:
                try:
                    int_ids.append(int(i))
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid scheme ID '{i}': ID must be an integer",
                    )

            schemes = (
                db.query(Scheme)
                .options(joinedload(Scheme.eligibility_rules))
                .filter(Scheme.id.in_(int_ids))
                .all()
            )

            found_ids = {s.id for s in schemes}
            missing = set(int_ids) - found_ids
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"One or more requested schemes not found: {sorted(list(missing))}",
                )

            # Preserve the ordering requested by caller
            scheme_map = {s.id: s for s in schemes}
            ordered_schemes = [scheme_map[sid] for sid in int_ids]

            items: List[ComparisonItem] = []
            for scheme in ordered_schemes:
                if not is_privileged:
                    if not scheme.is_active or scheme.status in (
                        SchemeStatus.ARCHIVED.value,
                        SchemeStatus.INACTIVE.value,
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Scheme with ID {scheme.id} is archived or restricted from public comparison",
                        )

                benefits_list = (
                    [b.strip() for b in scheme.benefits.split(";") if b.strip()]
                    if (scheme.benefits and ";" in scheme.benefits)
                    else ([scheme.benefits] if scheme.benefits else [])
                )

                eligibility_list = [
                    {"rule_name": r.rule_name, "description": r.description}
                    for r in scheme.eligibility_rules
                    if r.is_active
                ]

                items.append(
                    ComparisonItem(
                        id=scheme.id,
                        name=scheme.name,
                        category=scheme.category,
                        benefits=benefits_list,
                        eligibility=eligibility_list,
                        department=scheme.department,
                        state=scheme.state,
                        application_process=scheme.application_process,
                    )
                )

            return ComparisonResponse(comparison_type="scheme", items=items)

        elif req.policy_ids:
            raw_ids = req.policy_ids
            int_ids = []
            for i in raw_ids:
                try:
                    int_ids.append(int(i))
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid policy ID '{i}': ID must be an integer",
                    )

            policies = (
                db.query(Policy)
                .options(joinedload(Policy.schemes))
                .filter(Policy.id.in_(int_ids))
                .all()
            )

            found_ids = {p.id for p in policies}
            missing = set(int_ids) - found_ids
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"One or more requested policies not found: {sorted(list(missing))}",
                )

            policy_map = {p.id: p for p in policies}
            ordered_policies = [policy_map[pid] for pid in int_ids]

            items = []
            for policy in ordered_policies:
                if not is_privileged:
                    if not policy.is_active or policy.status not in (
                        PolicyStatus.PUBLISHED.value,
                        PolicyStatus.APPROVED.value,
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Policy with ID {policy.id} is not published or restricted from public comparison",
                        )

                benefits_list = [policy.description] if policy.description else []
                schemes_list = [s.name for s in policy.schemes if s.is_active]

                items.append(
                    ComparisonItem(
                        id=policy.id,
                        name=policy.title,
                        category=policy.category,
                        benefits=benefits_list,
                        eligibility=schemes_list,
                        department=policy.department,
                        state=policy.state,
                        application_process=f"Administered by {policy.department or 'Nodal Department'} under {policy.ministry or 'Government'}",
                    )
                )

            return ComparisonResponse(comparison_type="policy", items=items)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specify either 'scheme_ids' or 'policy_ids' to compare.",
        )
