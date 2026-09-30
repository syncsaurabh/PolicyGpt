from datetime import date, datetime
import json
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import asc, cast, Date, desc, or_
from sqlalchemy.orm import Session
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.models.search_history import SearchHistory
from app.models.user import User, UserRole


class SearchService:
    @staticmethod
    def _record_search_history(
        db: Session,
        query_text: Optional[str],
        filters: Dict[str, Any],
        result_count: int,
        user_id: Optional[int] = None,
    ) -> None:
        """Record search terms and filters in the search_history table."""
        try:
            # Clean filters dictionary of None values
            clean_filters = {k: str(v) for k, v in filters.items() if v is not None}
            entry = SearchHistory(
                user_id=user_id,
                query=query_text or "*",
                filters_json=json.dumps(clean_filters),
                result_count=result_count,
            )
            db.add(entry)
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def _is_test_record_name(name: Optional[str]) -> bool:
        if not name:
            return True
        n = name.strip().lower()
        if len(n) < 4:
            return True
        dummy_markers = ["test", "dummy", "demo", "sample", "temp", "foo", "bar", "schem1", "kishan t", "mail2"]
        return any(m in n for m in dummy_markers)

    @staticmethod
    def search_policies(
        db: Session,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        state: Optional[str] = None,
        ministry: Optional[str] = None,
        department: Optional[str] = None,
        sector: Optional[str] = None,
        publication_date: Optional[date] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user: Optional[User] = None,
    ) -> Tuple[List[Policy], int, int]:
        """Search policies with advanced multi-filter combinations, pagination, and logging."""
        query = db.query(Policy)

        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            query = query.filter(
                Policy.is_active == True,
                Policy.status.in_([PolicyStatus.PUBLISHED.value, PolicyStatus.APPROVED.value]),
                ~Policy.title.ilike("%test%"),
                ~Policy.title.ilike("%dummy%"),
                ~Policy.title.ilike("%demo%"),
                ~Policy.title.ilike("%sample%"),
            )
        else:
            if status_filter:
                query = query.filter(Policy.status.ilike(status_filter.strip()))

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Policy.title.ilike(kw),
                    Policy.description.ilike(kw),
                    Policy.category.ilike(kw),
                    Policy.ministry.ilike(kw),
                    Policy.department.ilike(kw),
                    Policy.sector.ilike(kw),
                )
            )

        if category:
            query = query.filter(Policy.category.ilike(f"%{category.strip()}%"))

        if state:
            query = query.filter(Policy.state.ilike(f"%{state.strip()}%"))

        if ministry:
            query = query.filter(Policy.ministry.ilike(f"%{ministry.strip()}%"))

        if department:
            query = query.filter(Policy.department.ilike(f"%{department.strip()}%"))

        if sector:
            query = query.filter(Policy.sector.ilike(f"%{sector.strip()}%"))

        if publication_date:
            query = query.filter(cast(Policy.publication_date, Date) == publication_date)

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

        # Record history
        SearchService._record_search_history(
            db=db,
            query_text=keyword,
            filters={
                "type": "policy",
                "category": category,
                "state": state,
                "ministry": ministry,
                "department": department,
                "sector": sector,
                "status": status_filter,
            },
            result_count=total_count,
            user_id=current_user.id if current_user else None,
        )

        return results, total_count, total_pages

    @staticmethod
    def search_schemes(
        db: Session,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        state: Optional[str] = None,
        ministry: Optional[str] = None,
        department: Optional[str] = None,
        sector: Optional[str] = None,
        publication_date: Optional[date] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user: Optional[User] = None,
    ) -> Tuple[List[Scheme], int, int]:
        """Search public schemes with multi-field search, dummy exclusion, relevance ranking, and pagination."""
        query = db.query(Scheme)

        is_privileged = current_user is not None and current_user.role in (
            UserRole.ADMINISTRATOR,
            UserRole.GOVERNMENT_OFFICIAL,
        )

        if not is_privileged:
            query = query.filter(
                Scheme.is_active == True,
                Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
                ~Scheme.name.ilike("%test%"),
                ~Scheme.name.ilike("%dummy%"),
                ~Scheme.name.ilike("%demo%"),
                ~Scheme.name.ilike("%sample%"),
                ~Scheme.name.ilike("%kishan t%"),
            )
        else:
            if status_filter:
                query = query.filter(Scheme.status.ilike(status_filter.strip()))

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Scheme.name.ilike(kw),
                    Scheme.description.ilike(kw),
                    Scheme.benefits.ilike(kw),
                    Scheme.target_audience.ilike(kw),
                    Scheme.category.ilike(kw),
                    Scheme.department.ilike(kw),
                    Scheme.ministry.ilike(kw),
                    Scheme.sector.ilike(kw),
                )
            )

        if category:
            query = query.filter(Scheme.category.ilike(f"%{category.strip()}%"))

        if state:
            query = query.filter(Scheme.state.ilike(f"%{state.strip()}%"))

        if ministry:
            query = query.filter(Scheme.ministry.ilike(f"%{ministry.strip()}%"))

        if department:
            query = query.filter(Scheme.department.ilike(f"%{department.strip()}%"))

        if sector:
            query = query.filter(Scheme.sector.ilike(f"%{sector.strip()}%"))

        if publication_date:
            query = query.filter(cast(Scheme.publication_date, Date) == publication_date)

        # Relevance ranking in memory if keyword is provided
        if keyword:
            raw_candidates = query.all()
            tokens = [t.lower() for t in keyword.strip().split() if len(t) > 1]
            scored = []
            for s in raw_candidates:
                score = 0
                name_l = (s.name or "").lower()
                cat_l = (s.category or "").lower()
                target_l = (s.target_audience or "").lower()
                ben_l = (s.benefits or "").lower()
                desc_l = (s.description or "").lower()
                dept_l = (s.department or "").lower()

                for t in tokens:
                    if t in name_l:
                        score += 10
                    if t in cat_l:
                        score += 6
                    if t in target_l:
                        score += 5
                    if t in ben_l:
                        score += 4
                    if t in desc_l:
                        score += 3
                    if t in dept_l:
                        score += 2

                scored.append((score, s))

            scored.sort(key=lambda x: x[0], reverse=True)
            ranked_schemes = [s for score, s in scored]
            total_count = len(ranked_schemes)
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            offset = (page - 1) * page_size
            results = ranked_schemes[offset:offset + page_size]
        else:
            # Standard database sorting
            sort_col = getattr(Scheme, sort_by, Scheme.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_col))
            else:
                query = query.order_by(desc(sort_col))

            total_count = query.count()
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()

        # Record history
        SearchService._record_search_history(
            db=db,
            query_text=keyword,
            filters={
                "type": "scheme",
                "category": category,
                "state": state,
                "ministry": ministry,
                "department": department,
                "sector": sector,
                "status": status_filter,
            },
            result_count=total_count,
            user_id=current_user.id if current_user else None,
        )

        return results, total_count, total_pages
