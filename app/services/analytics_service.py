from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.policy import Policy, PolicyStatus
from app.models.report import Report
from app.models.scheme import Scheme, SchemeStatus
from app.models.search_history import SearchHistory
from app.models.user import User
from app.models.user_activity import UserActivity
from app.schemas.analytics import (
    DepartmentAnalyticsItem,
    DepartmentAnalyticsResponse,
    DistributionItem,
    NotificationAnalytics,
    OverviewAnalyticsResponse,
    PolicyAnalytics,
    SchemeAnalytics,
    SearchAnalytics,
    UsageStatisticsResponse,
    UserAnalytics,
)


class AnalyticsService:
    @staticmethod
    def get_overview_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> OverviewAnalyticsResponse:
        """Aggregate high-level overview metrics across the platform."""
        p_query = db.query(Policy)
        s_query = db.query(Scheme)
        u_query = db.query(User)
        sh_query = db.query(SearchHistory)
        n_query = db.query(Notification)

        if start_date:
            p_query = p_query.filter(Policy.created_at >= start_date)
            s_query = s_query.filter(Scheme.created_at >= start_date)
            u_query = u_query.filter(User.created_at >= start_date)
            sh_query = sh_query.filter(SearchHistory.created_at >= start_date)
            n_query = n_query.filter(Notification.created_at >= start_date)
        if end_date:
            next_day = end_date + timedelta(days=1)
            p_query = p_query.filter(Policy.created_at < next_day)
            s_query = s_query.filter(Scheme.created_at < next_day)
            u_query = u_query.filter(User.created_at < next_day)
            sh_query = sh_query.filter(SearchHistory.created_at < next_day)
            n_query = n_query.filter(Notification.created_at < next_day)

        total_policies = p_query.count()
        published_policies = p_query.filter(
            Policy.status.in_([PolicyStatus.PUBLISHED.value, PolicyStatus.APPROVED.value])
        ).count()

        total_schemes = s_query.count()
        active_schemes = s_query.filter(
            Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value])
        ).count()

        total_users = u_query.count()
        total_searches = sh_query.count()
        total_notifications = n_query.count()
        unread_notifications = n_query.filter(Notification.is_read == False).count()

        # Policy categories distribution
        p_cat_rows = (
            db.query(Policy.category, func.count(Policy.id))
            .filter(Policy.category.isnot(None))
            .group_by(Policy.category)
            .order_by(func.count(Policy.id).desc())
            .limit(10)
            .all()
        )
        policy_cat_dist = [DistributionItem(name=row[0] or "Unassigned", count=row[1]) for row in p_cat_rows]

        # Scheme categories distribution
        s_cat_rows = (
            db.query(Scheme.category, func.count(Scheme.id))
            .filter(Scheme.category.isnot(None))
            .group_by(Scheme.category)
            .order_by(func.count(Scheme.id).desc())
            .limit(10)
            .all()
        )
        scheme_cat_dist = [DistributionItem(name=row[0] or "Unassigned", count=row[1]) for row in s_cat_rows]

        # Department distribution (from policies)
        dept_rows = (
            db.query(Policy.department, func.count(Policy.id))
            .filter(Policy.department.isnot(None))
            .group_by(Policy.department)
            .order_by(func.count(Policy.id).desc())
            .limit(10)
            .all()
        )
        dept_dist = [DistributionItem(name=row[0] or "Unassigned", count=row[1]) for row in dept_rows]

        # User role distribution
        user_role_rows = (
            db.query(User.role, func.count(User.id))
            .group_by(User.role)
            .all()
        )
        role_dist = [DistributionItem(name=getattr(row[0], "value", str(row[0])), count=row[1]) for row in user_role_rows]

        return OverviewAnalyticsResponse(
            total_policies=total_policies,
            published_policies=published_policies,
            total_schemes=total_schemes,
            active_schemes=active_schemes,
            total_users=total_users,
            total_searches=total_searches,
            total_notifications=total_notifications,
            unread_notifications=unread_notifications,
            policy_category_distribution=policy_cat_dist,
            scheme_category_distribution=scheme_cat_dist,
            department_distribution=dept_dist,
            user_role_distribution=role_dist,
        )

    @staticmethod
    def get_policy_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department: Optional[str] = None,
    ) -> PolicyAnalytics:
        """Compute detailed policy metrics, status breakdown, and distributions."""
        query = db.query(Policy)
        if start_date:
            query = query.filter(Policy.created_at >= start_date)
        if end_date:
            query = query.filter(Policy.created_at < end_date + timedelta(days=1))
        if department:
            query = query.filter(Policy.department.ilike(f"%{department.strip()}%"))

        total_policies = query.count()
        published_count = query.filter(Policy.status == PolicyStatus.PUBLISHED.value).count()
        draft_count = query.filter(Policy.status == PolicyStatus.DRAFT.value).count()
        pending_approval_count = query.filter(Policy.status == PolicyStatus.PENDING_APPROVAL.value).count()
        approved_count = query.filter(Policy.status == PolicyStatus.APPROVED.value).count()
        rejected_count = query.filter(Policy.status == PolicyStatus.REJECTED.value).count()
        archived_count = query.filter(Policy.status == PolicyStatus.ARCHIVED.value).count()

        # Category distribution
        cat_rows = (
            query.with_entities(Policy.category, func.count(Policy.id))
            .filter(Policy.category.isnot(None))
            .group_by(Policy.category)
            .order_by(func.count(Policy.id).desc())
            .all()
        )
        by_category = [DistributionItem(name=r[0], count=r[1]) for r in cat_rows if r[0]]

        # Department distribution
        dept_rows = (
            query.with_entities(Policy.department, func.count(Policy.id))
            .filter(Policy.department.isnot(None))
            .group_by(Policy.department)
            .order_by(func.count(Policy.id).desc())
            .all()
        )
        by_department = [DistributionItem(name=r[0], count=r[1]) for r in dept_rows if r[0]]

        # State distribution
        state_rows = (
            query.with_entities(Policy.state, func.count(Policy.id))
            .filter(Policy.state.isnot(None))
            .group_by(Policy.state)
            .order_by(func.count(Policy.id).desc())
            .all()
        )
        by_state = [DistributionItem(name=r[0], count=r[1]) for r in state_rows if r[0]]

        return PolicyAnalytics(
            total_policies=total_policies,
            published_count=published_count,
            draft_count=draft_count,
            pending_approval_count=pending_approval_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            archived_count=archived_count,
            by_category=by_category,
            by_department=by_department,
            by_state=by_state,
        )

    @staticmethod
    def get_scheme_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department: Optional[str] = None,
    ) -> SchemeAnalytics:
        """Compute detailed public scheme metrics, status breakdown, and distributions."""
        query = db.query(Scheme)
        if start_date:
            query = query.filter(Scheme.created_at >= start_date)
        if end_date:
            query = query.filter(Scheme.created_at < end_date + timedelta(days=1))
        if department:
            query = query.filter(Scheme.department.ilike(f"%{department.strip()}%"))

        total_schemes = query.count()
        active_count = query.filter(Scheme.status == SchemeStatus.ACTIVE.value).count()
        inactive_count = query.filter(Scheme.status == SchemeStatus.INACTIVE.value).count()
        draft_count = query.filter(Scheme.status == SchemeStatus.DRAFT.value).count()
        archived_count = query.filter(Scheme.status == SchemeStatus.ARCHIVED.value).count()
        published_count = query.filter(Scheme.status == SchemeStatus.PUBLISHED.value).count()

        # Category distribution
        cat_rows = (
            query.with_entities(Scheme.category, func.count(Scheme.id))
            .filter(Scheme.category.isnot(None))
            .group_by(Scheme.category)
            .order_by(func.count(Scheme.id).desc())
            .all()
        )
        by_category = [DistributionItem(name=r[0], count=r[1]) for r in cat_rows if r[0]]

        # Department distribution
        dept_rows = (
            query.with_entities(Scheme.department, func.count(Scheme.id))
            .filter(Scheme.department.isnot(None))
            .group_by(Scheme.department)
            .order_by(func.count(Scheme.id).desc())
            .all()
        )
        by_department = [DistributionItem(name=r[0], count=r[1]) for r in dept_rows if r[0]]

        # State distribution
        state_rows = (
            query.with_entities(Scheme.state, func.count(Scheme.id))
            .filter(Scheme.state.isnot(None))
            .group_by(Scheme.state)
            .order_by(func.count(Scheme.id).desc())
            .all()
        )
        by_state = [DistributionItem(name=r[0], count=r[1]) for r in state_rows if r[0]]

        return SchemeAnalytics(
            total_schemes=total_schemes,
            active_count=active_count,
            inactive_count=inactive_count,
            draft_count=draft_count,
            archived_count=archived_count,
            published_count=published_count,
            by_category=by_category,
            by_department=by_department,
            by_state=by_state,
        )

    @staticmethod
    def get_user_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> UserAnalytics:
        """Compute user demographics, role distributions, and recent growth."""
        query = db.query(User)
        if start_date:
            query = query.filter(User.created_at >= start_date)
        if end_date:
            query = query.filter(User.created_at < end_date + timedelta(days=1))

        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        inactive_users = query.filter(User.is_active == False).count()

        # Role distribution
        role_rows = (
            query.with_entities(User.role, func.count(User.id))
            .group_by(User.role)
            .order_by(func.count(User.id).desc())
            .all()
        )
        by_role = [DistributionItem(name=getattr(r[0], "value", str(r[0])), count=r[1]) for r in role_rows]

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_registrations = db.query(User).filter(User.created_at >= thirty_days_ago).count()

        return UserAnalytics(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            by_role=by_role,
            recent_registrations_30d=recent_registrations,
        )

    @staticmethod
    def get_department_analytics(
        db: Session,
        department_filter: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> DepartmentAnalyticsResponse:
        """Compute department-wise metrics combining policies, schemes, and user actions."""
        # Find distinct department names from both policies and schemes
        p_depts = db.query(Policy.department).filter(Policy.department.isnot(None))
        s_depts = db.query(Scheme.department).filter(Scheme.department.isnot(None))

        if department_filter:
            p_depts = p_depts.filter(Policy.department.ilike(f"%{department_filter.strip()}%"))
            s_depts = s_depts.filter(Scheme.department.ilike(f"%{department_filter.strip()}%"))

        all_dept_names = set([r[0].strip() for r in p_depts.distinct().all() if r[0] and r[0].strip()])
        all_dept_names.update([r[0].strip() for r in s_depts.distinct().all() if r[0] and r[0].strip()])

        items: List[DepartmentAnalyticsItem] = []
        for dept in sorted(all_dept_names):
            p_q = db.query(Policy).filter(Policy.department.ilike(dept))
            s_q = db.query(Scheme).filter(Scheme.department.ilike(dept))

            if start_date:
                p_q = p_q.filter(Policy.created_at >= start_date)
                s_q = s_q.filter(Scheme.created_at >= start_date)
            if end_date:
                p_q = p_q.filter(Policy.created_at < end_date + timedelta(days=1))
                s_q = s_q.filter(Scheme.created_at < end_date + timedelta(days=1))

            p_count = p_q.count()
            p_pub = p_q.filter(Policy.status.in_([PolicyStatus.PUBLISHED.value, PolicyStatus.APPROVED.value])).count()
            s_count = s_q.count()
            s_act = s_q.filter(Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value])).count()

            # Activity count for this department in user activities
            act_count = db.query(UserActivity).filter(
                UserActivity.details.ilike(f"%{dept}%")
            ).count()

            items.append(
                DepartmentAnalyticsItem(
                    department=dept,
                    policy_count=p_count,
                    scheme_count=s_count,
                    published_policies=p_pub,
                    active_schemes=s_act,
                    activity_count=act_count,
                )
            )

        return DepartmentAnalyticsResponse(
            total_departments=len(items),
            departments=items,
        )

    @staticmethod
    def get_search_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> SearchAnalytics:
        """Compute search query trends and statistics from real search history."""
        query = db.query(SearchHistory)
        if start_date:
            query = query.filter(SearchHistory.created_at >= start_date)
        if end_date:
            query = query.filter(SearchHistory.created_at < end_date + timedelta(days=1))

        total_searches = query.count()
        unique_users = query.with_entities(func.count(distinct(SearchHistory.user_id))).scalar() or 0
        zero_results = query.filter(SearchHistory.result_count == 0).count()

        popular_rows = (
            query.with_entities(SearchHistory.query, func.count(SearchHistory.id))
            .group_by(SearchHistory.query)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(10)
            .all()
        )
        popular_queries = [DistributionItem(name=r[0], count=r[1]) for r in popular_rows if r[0]]

        return SearchAnalytics(
            total_searches=total_searches,
            unique_users_count=unique_users,
            popular_queries=popular_queries,
            zero_result_searches=zero_results,
        )

    @staticmethod
    def get_notification_analytics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> NotificationAnalytics:
        """Compute notification volume, delivery channels, and read rates."""
        query = db.query(Notification)
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        if end_date:
            query = query.filter(Notification.created_at < end_date + timedelta(days=1))

        total_notifications = query.count()
        unread_count = query.filter(Notification.is_read == False).count()
        read_count = query.filter(Notification.is_read == True).count()

        type_rows = (
            query.with_entities(Notification.notification_type, func.count(Notification.id))
            .group_by(Notification.notification_type)
            .order_by(func.count(Notification.id).desc())
            .all()
        )
        by_type = [DistributionItem(name=r[0] or "GENERAL", count=r[1]) for r in type_rows]

        chan_rows = (
            query.with_entities(Notification.channel, func.count(Notification.id))
            .group_by(Notification.channel)
            .order_by(func.count(Notification.id).desc())
            .all()
        )
        by_channel = [DistributionItem(name=r[0] or "IN_APP", count=r[1]) for r in chan_rows]

        return NotificationAnalytics(
            total_notifications=total_notifications,
            unread_count=unread_count,
            read_count=read_count,
            by_type=by_type,
            by_channel=by_channel,
        )

    @staticmethod
    def get_usage_statistics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> UsageStatisticsResponse:
        """Aggregate usage events across searches, eligibility checks, feedback, and reports."""
        act_query = db.query(UserActivity)
        if start_date:
            act_query = act_query.filter(UserActivity.created_at >= start_date)
        if end_date:
            act_query = act_query.filter(UserActivity.created_at < end_date + timedelta(days=1))

        total_activities = act_query.count()

        event_type_rows = (
            act_query.with_entities(UserActivity.event_type, func.count(UserActivity.id))
            .group_by(UserActivity.event_type)
            .order_by(func.count(UserActivity.id).desc())
            .all()
        )
        activities_by_event = [DistributionItem(name=r[0], count=r[1]) for r in event_type_rows]

        total_searches = db.query(SearchHistory).count()
        total_eligibility_checks = act_query.filter(UserActivity.event_type == "ELIGIBILITY_CHECK").count()
        total_feedbacks = db.query(Feedback).count()
        total_reports_generated = db.query(Report).count()

        resource_rows = (
            act_query.with_entities(UserActivity.resource_type, func.count(UserActivity.id))
            .filter(UserActivity.resource_type.isnot(None))
            .group_by(UserActivity.resource_type)
            .order_by(func.count(UserActivity.id).desc())
            .all()
        )
        popular_resources = [DistributionItem(name=r[0], count=r[1]) for r in resource_rows if r[0]]

        recent_act_rows = (
            act_query.order_by(UserActivity.created_at.desc())
            .limit(10)
            .all()
        )
        recent_activities = [
            {
                "id": act.id,
                "event_type": act.event_type,
                "resource_type": act.resource_type,
                "resource_id": act.resource_id,
                "created_at": act.created_at.isoformat() if act.created_at else None,
            }
            for act in recent_act_rows
        ]

        return UsageStatisticsResponse(
            total_activities=total_activities,
            activities_by_event_type=activities_by_event,
            total_searches=total_searches,
            total_eligibility_checks=total_eligibility_checks,
            total_feedbacks=total_feedbacks,
            total_reports_generated=total_reports_generated,
            popular_resources=popular_resources,
            recent_activities=recent_activities,
        )
