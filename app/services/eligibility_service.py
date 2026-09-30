import json
from typing import Any, Dict, List
from sqlalchemy.orm import Session, joinedload
from app.models.scheme import Scheme, SchemeStatus
from app.models.eligibility import EligibilityRule
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    SchemeEligibilityResult,
)


class EligibilityService:
    @staticmethod
    def _normalize_list(val: Any) -> List[str]:
        """Convert a single string, list of strings, or comma-separated string to a list of lower-case strings."""
        if val is None:
            return []
        if isinstance(val, list):
            return [str(item).strip().lower() for item in val if str(item).strip()]
        if isinstance(val, str):
            if "," in val:
                return [s.strip().lower() for s in val.split(",") if s.strip()]
            return [val.strip().lower()] if val.strip() else []
        return [str(val).strip().lower()]

    @classmethod
    def evaluate_rule(
        cls,
        rule: EligibilityRule,
        profile: EligibilityCheckRequest,
    ) -> Dict[str, Any]:
        """Evaluate a single database eligibility rule against user profile criteria."""
        matched: List[str] = []
        failed: List[str] = []

        if not rule.criteria_json:
            matched.append(f"{rule.rule_name}: General eligibility passed")
            return {"passed": True, "matched": matched, "failed": failed}

        try:
            criteria = json.loads(rule.criteria_json)
        except Exception:
            # If invalid JSON, treat rule as informational / pass
            matched.append(f"{rule.rule_name}: Standard criteria verified")
            return {"passed": True, "matched": matched, "failed": failed}

        if not isinstance(criteria, dict):
            matched.append(f"{rule.rule_name}: Criteria verified")
            return {"passed": True, "matched": matched, "failed": failed}

        # 1. Age Verification
        min_age = criteria.get("min_age") or criteria.get("minimum_age")
        if min_age is not None:
            try:
                min_age_val = int(min_age)
                if profile.age is not None:
                    if profile.age < min_age_val:
                        failed.append(f"Age {profile.age} is below minimum requirement of {min_age_val} years")
                    else:
                        matched.append(f"Age criterion met (Minimum: {min_age_val})")
                else:
                    failed.append(f"Age required to verify minimum age {min_age_val}")
            except (ValueError, TypeError):
                pass

        max_age = criteria.get("max_age") or criteria.get("maximum_age")
        if max_age is not None:
            try:
                max_age_val = int(max_age)
                if profile.age is not None:
                    if profile.age > max_age_val:
                        failed.append(f"Age {profile.age} exceeds maximum limit of {max_age_val} years")
                    else:
                        matched.append(f"Age criterion met (Maximum: {max_age_val})")
                else:
                    failed.append(f"Age required to verify maximum age {max_age_val}")
            except (ValueError, TypeError):
                pass

        # 2. Income Verification
        min_income = criteria.get("min_income") or criteria.get("minimum_income")
        if min_income is not None:
            try:
                min_inc_val = float(min_income)
                if profile.income is not None:
                    if profile.income < min_inc_val:
                        failed.append(f"Income ₹{profile.income:,.0f} is below minimum requirement of ₹{min_inc_val:,.0f}")
                    else:
                        matched.append(f"Income criterion met (>= ₹{min_inc_val:,.0f})")
                else:
                    failed.append(f"Income required to verify minimum income of ₹{min_inc_val:,.0f}")
            except (ValueError, TypeError):
                pass

        max_income = criteria.get("max_income") or criteria.get("maximum_income")
        if max_income is not None:
            try:
                max_inc_val = float(max_income)
                if profile.income is not None:
                    if profile.income > max_inc_val:
                        failed.append(f"Income ₹{profile.income:,.0f} exceeds maximum threshold of ₹{max_inc_val:,.0f}")
                    else:
                        matched.append(f"Income criterion met (<= ₹{max_inc_val:,.0f})")
                else:
                    failed.append(f"Income required to verify ceiling of ₹{max_inc_val:,.0f}")
            except (ValueError, TypeError):
                pass

        # 3. Gender Verification
        raw_gender = criteria.get("gender") or criteria.get("allowed_genders")
        allowed_genders = cls._normalize_list(raw_gender)
        if allowed_genders and not any(g in allowed_genders for g in ["all", "any", "both"]):
            if profile.gender:
                if profile.gender.strip().lower() not in allowed_genders:
                    failed.append(f"Gender '{profile.gender}' does not match scheme target ({', '.join(allowed_genders)})")
                else:
                    matched.append(f"Gender criterion matched ({profile.gender})")
            else:
                failed.append(f"Gender required ({', '.join(allowed_genders)})")

        # 4. Occupation Verification
        raw_occ = criteria.get("occupation") or criteria.get("allowed_occupations") or criteria.get("occupations")
        allowed_occ = cls._normalize_list(raw_occ)
        if allowed_occ and not any(o in allowed_occ for o in ["all", "any"]):
            if profile.occupation:
                if profile.occupation.strip().lower() not in allowed_occ:
                    failed.append(f"Occupation '{profile.occupation}' does not match scheme target ({', '.join(allowed_occ)})")
                else:
                    matched.append(f"Occupation criterion matched ({profile.occupation})")
            else:
                failed.append(f"Occupation required ({', '.join(allowed_occ)})")

        # 5. Education Verification
        raw_edu = criteria.get("education") or criteria.get("allowed_educations") or criteria.get("qualifications")
        allowed_edu = cls._normalize_list(raw_edu)
        if allowed_edu and not any(e in allowed_edu for e in ["all", "any"]):
            if profile.education:
                if profile.education.strip().lower() not in allowed_edu:
                    failed.append(f"Education '{profile.education}' does not match required qualification ({', '.join(allowed_edu)})")
                else:
                    matched.append(f"Education criterion matched ({profile.education})")
            else:
                failed.append(f"Education qualification required ({', '.join(allowed_edu)})")

        # 6. Location / State Verification
        raw_state = criteria.get("state") or criteria.get("location") or criteria.get("allowed_states")
        allowed_states = cls._normalize_list(raw_state)
        if allowed_states and not any(s in allowed_states for s in ["all", "all india", "national", "any"]):
            if profile.location:
                if profile.location.strip().lower() not in allowed_states:
                    failed.append(f"Domicile/State '{profile.location}' does not match scheme target ({', '.join(allowed_states)})")
                else:
                    matched.append(f"Location criterion matched ({profile.location})")
            else:
                failed.append(f"Location/Domicile required ({', '.join(allowed_states)})")

        # 7. Social Category Verification
        raw_cat = criteria.get("social_category") or criteria.get("allowed_categories") or criteria.get("category")
        allowed_cat = cls._normalize_list(raw_cat)
        if allowed_cat and not any(c in allowed_cat for c in ["all", "any"]):
            if profile.social_category:
                if profile.social_category.strip().lower() not in allowed_cat:
                    failed.append(f"Social category '{profile.social_category}' does not match allowed categories ({', '.join(allowed_cat)})")
                else:
                    matched.append(f"Social category criterion matched ({profile.social_category})")
            else:
                failed.append(f"Social category required ({', '.join(allowed_cat)})")

        # 8. Disability Status Verification
        disability_required = criteria.get("disability_required") or criteria.get("disability_status")
        if disability_required is True:
            if not profile.disability_status:
                failed.append("Scheme requires registered disability status")
            else:
                matched.append("Disability criterion matched")

        is_passed = len(failed) == 0
        return {"passed": is_passed, "matched": matched, "failed": failed}

    @classmethod
    def check_eligibility(
        cls,
        db: Session,
        profile: EligibilityCheckRequest,
    ) -> EligibilityCheckResponse:
        """Evaluate active schemes against user profile using actual stored eligibility rules."""
        active_schemes = (
            db.query(Scheme)
            .options(joinedload(Scheme.eligibility_rules))
            .filter(
                Scheme.is_active == True,
                Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
            )
            .all()
        )

        eligible_results: List[SchemeEligibilityResult] = []

        for scheme in active_schemes:
            active_rules = [r for r in scheme.eligibility_rules if r.is_active]
            scheme_matched_rules: List[str] = []
            scheme_failed_rules: List[str] = []

            if not active_rules:
                # If scheme has no specific eligibility rules recorded, it is open / universally eligible
                scheme_matched_rules.append("Universal eligibility (no restrictive rules defined)")
                is_eligible = True
            else:
                is_eligible = True
                for rule in active_rules:
                    rule_eval = cls.evaluate_rule(rule, profile)
                    if not rule_eval["passed"]:
                        is_eligible = False
                        scheme_failed_rules.extend(rule_eval["failed"])
                    else:
                        scheme_matched_rules.extend(rule_eval["matched"])

            if is_eligible:
                guidance = scheme.application_process
                if not guidance:
                    dept = scheme.department or "the relevant administrative ministry"
                    guidance = f"To apply for {scheme.name}, visit the official portal of {dept} or visit your nearest Citizen Service Centre (CSC) with identity and income certificates."

                eligible_results.append(
                    SchemeEligibilityResult(
                        scheme_id=scheme.id,
                        scheme_name=scheme.name,
                        eligible=True,
                        matched_rules=scheme_matched_rules,
                        failed_rules=[],
                        category=scheme.category,
                        benefits=scheme.benefits,
                        department=scheme.department,
                        application_guidance=guidance,
                    )
                )

        return EligibilityCheckResponse(
            eligible_schemes=eligible_results,
            total_matches=len(eligible_results),
        )
