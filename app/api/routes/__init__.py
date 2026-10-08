from app.api.routes.applications import router as applications_router
"""API routes package."""
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.policies import router as policies_router
from app.api.routes.schemes import router as schemes_router
from app.api.routes.search import router as search_router
from app.api.routes.eligibility import router as eligibility_router
from app.api.routes.comparison import router as comparison_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.reports import router as reports_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.faqs import router as faqs_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.assistant import router as assistant_router

__all__ = [
    "applications_router",
    "auth_router",
    "users_router",
    "policies_router",
    "schemes_router",
    "search_router",
    "eligibility_router",
    "comparison_router",
    "analytics_router",
    "notifications_router",
    "reports_router",
    "feedback_router",
    "faqs_router",
    "dashboard_router",
    "assistant_router",
]
