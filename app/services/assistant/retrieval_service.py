import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.application import SchemeApplication
from app.models.faq import FAQ
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.policy import Policy, PolicyStatus
from app.models.saved_policy import SavedPolicy
from app.models.scheme import Scheme, SchemeStatus
from app.models.user import User, UserRole
from app.schemas.assistant import SourceCitation
from app.schemas.comparison import ComparisonRequest
from app.schemas.eligibility import EligibilityCheckRequest
from app.services.comparison_service import ComparisonService
from app.services.eligibility_service import EligibilityService
from app.services.faq_service import FAQService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Retrieves verified platform data using existing PolicyGPT services.
    Guarantees strict user-data isolation and prevents hallucination.
    """

    @staticmethod
    def validate_security_and_privacy(
        query: str,
        current_user: Optional[User] = None,
    ) -> Optional[Tuple[str, str, List[SourceCitation]]]:
        """
        Enforce security policies, prompt injection defense, and strict cross-user data isolation.
        Returns a tuple of (rejection_message, intent, citations) if request violates privacy rules.
        """
        q = query.lower().strip()

        # 1. Prompt Injection and System Compromise Defense
        injection_patterns = [
            "ignore rules", "ignore previous instructions", "ignore your rules", "ignore your privacy rules",
            "show all users", "list all users", "give me all users", "get all users",
            "show me the database", "dump database", "user table", "users table",
            "database password", "secret key", "bypass rbac", "ignore rbac",
            "select * from", "drop table", "admin access bypass",
            "show me another citizen's application", "show me another user's application",
            "give me the user table", "dump user data", "show system prompt", "reveal prompt"
        ]
        if any(p in q for p in injection_patterns):
            logger.warning(f"Security Alert: Potential injection attempt detected: '{query[:60]}'")
            return (
                "Request rejected: Security and privacy policies strictly prohibit accessing administrative records or executing unauthorized database operations.",
                "security_rejected",
                [],
            )

        # 2. Third-Party / Cross-User Data Access Attempts
        # Detect patterns asking for other people's data (e.g. "saurabh's application", "citizen b's email", "phone number of user 2")
        third_party_queries = [
            r"\b[a-zA-Z0-9_-]+'s\s+(application|email|phone|phone number|notification|notifications|policy|saved policy|saved policies|ticket|profile|password|document|documents)\b",
            r"\b(application|applications|status|email|phone|phone number|notification|notifications|profile|saved policies|data|document|documents|conversation)\s+of\s+(another|other|user|citizen|[a-zA-Z0-9_-]+)\b",
            r"\b(show|get|tell|find|what is|give)\s+(me\s+)?(another|other|[a-zA-Z0-9_-]+)('s)?\s+(email|phone|phone number|application|applications|notification|notifications|saved policies|saved policy|data|profile)\b",
        ]
        # Check if the query is referring to another named person or other user
        for pattern in third_party_queries:
            match = re.search(pattern, q)
            if match:
                matched_str = match.group(0)
                # Ensure it's not "my application", "my email", etc.
                if not any(prefix in matched_str for prefix in ["my ", "i ", "me "]):
                    logger.warning(f"Privacy Alert: Cross-user inquiry blocked: '{query[:60]}'")
                    return (
                        "I can only provide information related to your own authenticated account. Accessing or inquiring about another user's personal data is strictly prohibited.",
                        "privacy_blocked",
                        [],
                    )

        # 3. Logged-Out / Guest Inquiry on Personal Resources
        personal_intents = [
            "my application", "my applications", "my saved policies", "my notifications",
            "my support tickets", "my tickets", "my feedback", "my profile", "my account",
            "am i eligible", "my eligibility", "show me my application status", "my application status"
        ]
        if current_user is None and any(p in q for p in personal_intents):
            return (
                "You must be logged in to view your personal applications, notifications, saved policies, or profile details. Please log in to your PolicyGPT citizen account.",
                "auth_required",
                [],
            )

        return None

    @staticmethod
    def identify_intent(
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        q = query.lower()

        # User-isolated personal data intents
        if any(w in q for w in ["my application", "my applications", "application status", "my scheme application", "submitted application", "track my application"]):
            return "user_applications"
        if any(w in q for w in ["my saved policies", "saved policies", "bookmarked policies", "my bookmarks"]):
            return "user_saved_policies"
        if any(w in q for w in ["my notifications", "my alerts", "unread notifications"]):
            return "user_notifications"
        if any(w in q for w in ["my support tickets", "my tickets", "my feedback", "my queries"]):
            return "user_feedback"
        if any(w in q for w in ["my profile", "my account details", "who am i", "my account info"]):
            return "user_profile"

        # Application Process / Guidance Intent
        if any(w in q for w in ["how do i apply", "how to apply", "how can i apply", "application process", "how do i submit", "submit an application", "documents required", "required documents", "what documents", "where to apply"]):
            return "application_guidance"

        # General Knowledge intents
        if any(w in q for w in ["compare", "comparison", "difference between", "versus", "vs"]):
            return "comparison"
        if any(w in q for w in ["eligible", "eligibility", "can i apply", "am i qualified", "criteria", "requirements", "qualification", "am i eligible"]):
            return "eligibility"
        if any(w in q for w in ["faq", "help", "password", "reset", "login", "register", "signup", "account", "support", "contact", "issue", "feedback", "complaint", "ticket", "error"]):
            return "faq_support"
        if any(w in q for w in ["policy", "policies", "guidelines", "governance", "act", "bill", "reform", "reforms", "regulations"]):
            return "policy_search"

        # Conversational Follow-up Intent Resolution
        if conversation_history:
            last_msg = conversation_history[-1] if conversation_history else {}
            last_intent = last_msg.get("intent")
            last_content = str(last_msg.get("content", "")).lower()

            if last_intent == "eligibility" or "eligibility" in last_content or "please provide" in last_content:
                has_profile_clues = any(w in q for w in ["age", "income", "years", "student", "farmer", "business", "lakh", "gujarat", "delhi", "maharashtra", "general", "obc", "sc", "st", "male", "female"]) or bool(re.search(r"\b\d{1,2}\b", q))
                if has_profile_clues:
                    return "eligibility"

            if last_intent == "comparison" or "second government scheme" in last_content or "which second" in last_content:
                if not any(w in q for w in ["search", "find all", "list all"]):
                    return "comparison"

        return "scheme_search"

    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        stop_words = {
            "what", "which", "how", "where", "when", "why", "who", "can", "is", "are",
            "the", "a", "an", "for", "in", "to", "of", "and", "or", "me", "i", "my",
            "tell", "show", "find", "list", "about", "available", "any", "some", "get",
            "please", "give", "schemes", "scheme", "policies", "policy", "government",
            "govt", "all", "view", "explore", "details", "info", "information", "portal",
            "latest", "active", "new", "top", "check", "know", "see", "there", "with",
            "this", "that", "these", "those", "another", "between"
        }
        words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
        return [w for w in words if w not in stop_words]

    @staticmethod
    def get_scheme_portal(scheme: Scheme) -> str:
        """Extract or assign the official government portal URL for a scheme."""
        name_l = (scheme.name or "").lower()
        if "pm kisan" in name_l or "kisan" in name_l:
            return "https://pmkisan.gov.in"
        if "ayushman" in name_l or "pm-jay" in name_l or "pmjay" in name_l:
            return "https://mera.pmjay.gov.in"
        if "awas" in name_l or "pmay" in name_l:
            return "https://pmaymis.gov.in"
        if "scholarship" in name_l or "vidya" in name_l or "student" in name_l:
            return "https://scholarships.gov.in"
        if "mudra" in name_l:
            return "https://www.mudra.org.in"
        if "matru vandana" in name_l or "pmmvy" in name_l:
            return "https://pmmvy.wcd.gov.in"
        if "surya ghar" in name_l or "solar" in name_l:
            return "https://pmsuryaghar.gov.in"
        if "amrutam" in name_l or "ma yojana" in name_l:
            return "https://magujarat.in"

        if scheme.application_process:
            url_match = re.search(r"https?://[^\s)\]]+", scheme.application_process)
            if url_match:
                return url_match.group(0).rstrip(".,;")

        return "https://www.india.gov.in/my-government/schemes"

    @staticmethod
    def get_scheme_documents(scheme: Scheme) -> List[str]:
        """Return official required documents list tailored to the scheme domain."""
        cat_l = (scheme.category or "").lower()
        name_l = (scheme.name or "").lower()

        if "scholarship" in cat_l or "student" in cat_l or "scholarship" in name_l:
            return [
                "Aadhaar Card / Student Photo ID",
                "Previous Academic Marksheets / Passing Certificate",
                "Family Income Certificate issued by Revenue Authority",
                "College/School Current Year Admission Fee Receipt",
                "Bank Account Passbook (Aadhaar Linked)",
                "Caste / Community Certificate (if applicable)",
            ]
        elif "farmer" in cat_l or "agriculture" in cat_l or "kisan" in name_l:
            return [
                "Aadhaar Card of Applicant",
                "Cultivable Landholding Ownership Papers (7/12 / Khatauni / RoR)",
                "Active Bank Account Passbook (Aadhaar linked for DBT)",
                "Active Mobile Number linked with Aadhaar for e-KYC",
            ]
        elif "healthcare" in cat_l or "health" in cat_l or "ayushman" in name_l:
            return [
                "Aadhaar Card of all family members",
                "Ration Card / BPL Certificate / Family ID Document",
                "Income Certificate (if applying under state economic threshold)",
                "Recent Passport-size Photographs",
            ]
        elif "housing" in cat_l or "awas" in name_l:
            return [
                "Aadhaar Cards and PAN Cards of adult family members",
                "Income Certificate / Form 16 / Salary Slips",
                "Self-declaration Affidavit stating no pucca house is owned in India",
                "Property / Land Purchase Documents / Construction Estimate",
                "Bank Account Statements (last 6 months)",
            ]
        elif "business" in cat_l or "mudra" in name_l:
            return [
                "Identity Proof (Aadhaar Card / Voter ID / Driving License)",
                "Address Proof of Business Establishment",
                "Udyam / Business Registration Certificate",
                "Business Project Proposal / Quotation of Machinery or Stock",
                "Bank Account Statements for past 6 months",
            ]
        elif "women" in cat_l or "matru" in name_l:
            return [
                "Mother and Child Protection (MCP) Card with ANC records",
                "Aadhaar Card of Mother and Spouse",
                "Aadhaar-linked Bank Account Passbook of Mother",
                "Institutional Delivery / Child Birth Certificate (for subsequent stages)",
            ]
        else:
            return [
                "Aadhaar Card / Government Photo ID",
                "Annual Family Income Certificate",
                "Domicile / Residence Certificate",
                "Aadhaar-seeded Bank Account Passbook",
            ]

    @staticmethod
    def extract_profile_from_context(
        query: str,
        profile_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> EligibilityCheckRequest:
        """Extract structured user profile details from request, query text, and conversation history."""
        data: Dict[str, Any] = {}
        if profile_context:
            data.update(profile_context)

        full_text = query
        if conversation_history:
            for m in conversation_history:
                if m.get("role") == "user":
                    full_text += " " + str(m.get("content", ""))

        text_l = full_text.lower()

        # Age extraction
        if "age" not in data or data["age"] is None:
            age_match = re.search(r"\b(\d{1,2})\s*(?:years?\s*old|years?|yrs?|yo)\b|\b(?:age\s*(?:is|=|:)?\s*|i\s*am\s*(?:a\s*)?)(\d{1,2})\b", text_l)
            if age_match:
                try:
                    val = age_match.group(1) or age_match.group(2)
                    data["age"] = int(val)
                except Exception:
                    pass

        # Income extraction
        if "income" not in data or data["income"] is None:
            inc_lakh_match = re.search(r"\b(?:income\s*(?:is|=|:)?\s*|earning\s*(?:is|=|:)?\s*)?(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|lac|lacs)\b", text_l)
            if inc_lakh_match and inc_lakh_match.group(1):
                try:
                    data["income"] = float(inc_lakh_match.group(1)) * 100000
                except Exception:
                    pass
            else:
                inc_num_match = re.search(r"\b(?:income\s*(?:is|=|:)?\s*|earning\s*(?:is|=|:)?\s*|rs\.?\s*|₹\s*)(\d{4,8})\b", text_l)
                if inc_num_match:
                    try:
                        data["income"] = float(inc_num_match.group(1))
                    except Exception:
                        pass

        # State extraction
        if "location" not in data or data["location"] is None:
            if "state" in data and data["state"]:
                data["location"] = data["state"]
            else:
                common_states = ["gujarat", "maharashtra", "delhi", "karnataka", "tamil nadu", "uttar pradesh", "rajasthan", "punjab", "kerala", "bihar", "madhya pradesh", "west bengal", "telangana", "andhra pradesh", "odisha", "haryana"]
                for st in common_states:
                    if st in text_l:
                        data["location"] = st.title()
                        data["state"] = st.title()
                        break

        # Occupation extraction
        if "occupation" not in data or data["occupation"] is None:
            if any(w in text_l for w in ["student", "studying", "college", "school"]):
                data["occupation"] = "student"
                data["is_student"] = True
            elif any(w in text_l for w in ["farmer", "farming", "agriculture", "kisan"]):
                data["occupation"] = "farmer"
            elif any(w in text_l for w in ["business", "entrepreneur", "shopkeeper", "self-employed", "artisan"]):
                data["occupation"] = "business"
            elif "unemployed" in text_l:
                data["occupation"] = "unemployed"

        # Gender extraction
        if "gender" not in data or data["gender"] is None:
            if any(w in text_l for w in ["female", "woman", "girl", "mother", "lady"]):
                data["gender"] = "female"
            elif any(w in text_l for w in ["male", "man", "boy", "father"]):
                data["gender"] = "male"

        # Social Category
        if "social_category" not in data or data["social_category"] is None:
            if "caste_category" in data and data["caste_category"]:
                data["social_category"] = data["caste_category"]
            elif "sc" in text_l.split():
                data["social_category"] = "SC"
            elif "st" in text_l.split():
                data["social_category"] = "ST"
            elif "obc" in text_l.split():
                data["social_category"] = "OBC"
            elif "general" in text_l.split():
                data["social_category"] = "General"
            elif "bpl" in text_l.split():
                data["social_category"] = "BPL"

        return EligibilityCheckRequest(
            age=data.get("age"),
            income=data.get("income"),
            location=data.get("location") or data.get("state"),
            gender=data.get("gender"),
            occupation=data.get("occupation"),
            education=data.get("education"),
            social_category=data.get("social_category") or data.get("caste_category"),
            disability_status=data.get("disability_status", False),
        )

    @staticmethod
    def resolve_target_scheme(
        db: Session,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Scheme]:
        """Identify which scheme the user is discussing from query or conversation history."""
        q_l = query.lower()
        active_schemes = (
            db.query(Scheme)
            .filter(
                Scheme.is_active == True,
                Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
                ~Scheme.name.ilike("%test%"),
                ~Scheme.name.ilike("%dummy%"),
                ~Scheme.name.ilike("%sample%"),
            )
            .all()
        )

        # 1. Match against scheme name or aliases in current query
        for s in active_schemes:
            s_name_l = s.name.lower()
            if s_name_l in q_l:
                return s
            # Keywords / acronyms
            acronyms = {
                "pm kisan": ["pm kisan", "pm-kisan", "kisan samman"],
                "ayushman": ["ayushman", "pm-jay", "pmjay", "jan arogya"],
                "pmay": ["pmay", "awas yojana", "pm awas"],
                "scholarship": ["post-matric", "vidya scholarship", "student scholarship", "post matric scholarship"],
                "mudra": ["mudra yojana", "mudra loan", "pmmy"],
                "matru vandana": ["matru vandana", "pmmvy", "maternity"],
                "surya ghar": ["surya ghar", "muft bijli", "rooftop solar"],
                "amrutam": ["amrutam", "ma yojana", "mukhyamantri amrutam"],
            }
            for main_k, alias_list in acronyms.items():
                if main_k in s_name_l:
                    if any(a in q_l for a in alias_list):
                        return s

        # 2. Check conversation history (from most recent assistant message)
        if conversation_history:
            for m in reversed(conversation_history):
                content = str(m.get("content", ""))
                sources = m.get("sources", [])
                if isinstance(sources, list) and sources:
                    for src in sources:
                        src_id = src.get("id") if isinstance(src, dict) else getattr(src, "id", None)
                        if src_id:
                            sch = db.query(Scheme).filter(Scheme.id == src_id, Scheme.is_active == True).first()
                            if sch:
                                return sch

                for s in active_schemes:
                    if s.name in content:
                        return s

        return None

    # =========================================================================
    # USER-ISOLATED DATA RETRIEVAL (STRICTLY CURRENT_USER.ID SCOPED)
    # =========================================================================

    @staticmethod
    def retrieve_user_applications(
        db: Session,
        current_user: User,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve applications owned strictly by the currently authenticated user."""
        apps = (
            db.query(SchemeApplication)
            .filter(SchemeApplication.user_id == current_user.id)
            .order_by(SchemeApplication.created_at.desc())
            .all()
        )

        app_list = []
        citations = []
        for a in apps:
            scheme_name = a.scheme.name if a.scheme else "Unknown Scheme"
            app_list.append({
                "application_number": a.application_number,
                "scheme_name": scheme_name,
                "status": a.status,
                "remarks": a.remarks,
                "created_at": a.created_at.isoformat(),
            })
            citations.append(
                SourceCitation(
                    type="application",
                    id=a.id,
                    name=f"Application {a.application_number} ({scheme_name})",
                    category="My Applications",
                    url="/citizen",
                    snippet=f"Status: {a.status} | Submitted: {a.created_at.strftime('%b %d, %Y')}",
                )
            )

        return {"user_id": current_user.id, "applications": app_list}, citations

    @staticmethod
    def retrieve_user_saved_policies(
        db: Session,
        current_user: User,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve saved/bookmarked policies owned strictly by the current user."""
        saved = (
            db.query(SavedPolicy)
            .filter(SavedPolicy.user_id == current_user.id)
            .order_by(SavedPolicy.created_at.desc())
            .all()
        )

        policies_list = []
        citations = []
        for s in saved:
            p_title = s.policy.title if s.policy else "Saved Policy"
            policies_list.append({
                "policy_id": s.policy_id,
                "title": p_title,
                "notes": s.notes,
                "saved_at": s.created_at.isoformat(),
            })
            citations.append(
                SourceCitation(
                    type="policy",
                    id=s.policy_id,
                    name=p_title,
                    category="Saved Policy",
                    url=f"/policies/{s.policy_id}",
                    snippet=f"Saved on {s.created_at.strftime('%b %d, %Y')}",
                )
            )

        return {"user_id": current_user.id, "saved_policies": policies_list}, citations

    @staticmethod
    def retrieve_user_notifications(
        db: Session,
        current_user: User,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve notifications addressed strictly to the current user."""
        notifs = (
            db.query(Notification)
            .filter(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )

        notif_list = []
        citations = []
        for n in notifs:
            notif_list.append({
                "title": n.title,
                "message": n.message,
                "type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            })
            citations.append(
                SourceCitation(
                    type="notification",
                    id=n.id,
                    name=n.title,
                    category="Notification",
                    url="/citizen",
                    snippet=n.message[:100],
                )
            )

        return {"user_id": current_user.id, "notifications": notif_list}, citations

    @staticmethod
    def retrieve_user_feedback(
        db: Session,
        current_user: User,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve feedback and support tickets submitted strictly by current user."""
        tickets = (
            db.query(Feedback)
            .filter(Feedback.user_id == current_user.id)
            .order_by(Feedback.created_at.desc())
            .limit(5)
            .all()
        )

        ticket_list = []
        citations = []
        for t in tickets:
            ticket_list.append({
                "id": t.id,
                "type": t.feedback_type,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "admin_response": t.admin_response,
                "created_at": t.created_at.isoformat(),
            })
            citations.append(
                SourceCitation(
                    type="support",
                    id=t.id,
                    name=f"Ticket #{t.id}: {t.subject}",
                    category=t.feedback_type,
                    url=f"/feedback/{t.id}",
                    snippet=f"Status: {t.status} | Resolution: {t.admin_response or 'Pending triage'}",
                )
            )

        return {"user_id": current_user.id, "tickets": ticket_list}, citations

    @staticmethod
    def retrieve_user_profile(
        db: Session,
        current_user: User,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve current user's profile details strictly from the authenticated JWT user object."""
        profile = {
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value if current_user.role else "CITIZEN",
            "phone_number": current_user.phone_number or "Not Provided",
            "age": current_user.age if getattr(current_user, "age", None) is not None else "Not Provided",
            "state": current_user.state or "Not Provided",
            "address": current_user.address or "Not Provided",
            "pincode": current_user.pincode or "Not Provided",
            "is_active": current_user.is_active,
        }
        return {"profile": profile}, []

    # =========================================================================
    # PUBLIC & RBAC-CHECKED PLATFORM DATA RETRIEVAL
    # =========================================================================

    @staticmethod
    def retrieve_schemes(
        db: Session,
        query: str,
        current_user: Optional[User] = None,
        limit: int = 5,
    ) -> Tuple[List[Dict[str, Any]], List[SourceCitation]]:
        keywords = RetrievalService.extract_keywords(query)
        kw_str = " ".join(keywords) if keywords else None

        detected_state = None
        common_states = ["gujarat", "maharashtra", "delhi", "karnataka", "tamil nadu", "uttar pradesh", "rajasthan", "punjab", "kerala", "bihar", "madhya pradesh", "all india"]
        for st in common_states:
            if st in query.lower():
                detected_state = st.title()
                break

        detected_category = None
        common_cats = ["education", "agriculture", "healthcare", "housing", "women", "student", "scholarship", "financial", "employment", "technology", "tribal", "farmer"]
        for c in common_cats:
            if c in query.lower():
                detected_category = c.title()
                break

        schemes, total, _ = SearchService.search_schemes(
            db=db,
            keyword=kw_str,
            category=detected_category,
            state=detected_state,
            page=1,
            page_size=limit,
            current_user=current_user,
        )

        if not schemes and keywords:
            for kw in keywords[:2]:
                schemes, _, _ = SearchService.search_schemes(
                    db=db,
                    keyword=kw,
                    page=1,
                    page_size=limit,
                    current_user=current_user,
                )
                if schemes:
                    break

        if not schemes and (detected_category or detected_state):
            schemes, _, _ = SearchService.search_schemes(
                db=db,
                keyword=None,
                category=detected_category,
                state=detected_state,
                page=1,
                page_size=limit,
                current_user=current_user,
            )

        if not schemes and not keywords and not detected_category and not detected_state:
            schemes, _, _ = SearchService.search_schemes(
                db=db,
                keyword=None,
                page=1,
                page_size=limit,
                current_user=current_user,
            )

        context_items: List[Dict[str, Any]] = []
        citations: List[SourceCitation] = []

        for s in schemes:
            rules_summary = [r.description or r.rule_name for r in s.eligibility_rules if r.is_active] if hasattr(s, "eligibility_rules") else []
            portal_url = RetrievalService.get_scheme_portal(s)
            docs_list = RetrievalService.get_scheme_documents(s)

            item = {
                "id": s.id,
                "name": s.name,
                "category": s.category or "General Welfare",
                "state": s.state or "All India",
                "department": s.department or "Central/State Authority",
                "ministry": s.ministry or "Government of India",
                "target_audience": s.target_audience or "Eligible Citizens",
                "benefits": s.benefits or "Financial assistance as per scheme guidelines",
                "description": s.description or "Government welfare program.",
                "application_process": s.application_process or "Apply online via official portal.",
                "application_mode": "Online & Common Service Centres (CSC)",
                "official_url": portal_url,
                "required_documents": docs_list,
                "eligibility_rules": rules_summary,
                "publication_date": s.publication_date.isoformat() if s.publication_date else "Active",
            }
            context_items.append(item)
            citations.append(
                SourceCitation(
                    type="scheme",
                    id=s.id,
                    name=s.name,
                    category=s.category or "Welfare Scheme",
                    url=f"/schemes/{s.id}",
                    snippet=f"Category: {s.category or 'General'} | Region: {s.state or 'All India'} | Target: {s.target_audience or 'Eligible Citizens'} | Benefits: {(s.benefits or '')[:100]}",
                )
            )

        return context_items, citations

    @staticmethod
    def retrieve_policies(
        db: Session,
        query: str,
        current_user: Optional[User] = None,
        limit: int = 5,
    ) -> Tuple[List[Dict[str, Any]], List[SourceCitation]]:
        keywords = RetrievalService.extract_keywords(query)
        kw_str = " ".join(keywords) if keywords else None

        policies, total, _ = SearchService.search_policies(
            db=db,
            keyword=kw_str,
            page=1,
            page_size=limit,
            current_user=current_user,
        )

        if not policies and keywords:
            for kw in keywords[:3]:
                policies, _, _ = SearchService.search_policies(
                    db=db,
                    keyword=kw,
                    page=1,
                    page_size=limit,
                    current_user=current_user,
                )
                if policies:
                    break

        if not policies and not keywords:
            policies, _, _ = SearchService.search_policies(
                db=db,
                keyword=None,
                page=1,
                page_size=limit,
                current_user=current_user,
            )

        context_items: List[Dict[str, Any]] = []
        citations: List[SourceCitation] = []

        for p in policies:
            item = {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "sector": p.sector,
                "ministry": p.ministry,
                "state": p.state or "National",
                "description": p.description,
                "status": p.status,
            }
            context_items.append(item)
            citations.append(
                SourceCitation(
                    type="policy",
                    id=p.id,
                    name=p.title,
                    category=p.category,
                    url=f"/policies/{p.id}",
                    snippet=f"Ministry: {p.ministry or 'N/A'} | Sector: {p.sector or 'General'}",
                )
            )

        return context_items, citations

    @staticmethod
    def retrieve_faqs(
        db: Session,
        query: str,
        limit: int = 4,
    ) -> Tuple[List[Dict[str, Any]], List[SourceCitation]]:
        keywords = RetrievalService.extract_keywords(query)
        kw_str = " ".join(keywords) if keywords else None

        faqs, total, _ = FAQService.list_faqs(
            db=db,
            keyword=kw_str,
            is_active_only=True,
            page=1,
            page_size=limit,
        )

        if not faqs and keywords:
            for kw in keywords:
                faqs, _, _ = FAQService.list_faqs(
                    db=db,
                    keyword=kw,
                    is_active_only=True,
                    page=1,
                    page_size=limit,
                )
                if faqs:
                    break

        if not faqs:
            faqs, _, _ = FAQService.list_faqs(
                db=db,
                keyword=None,
                is_active_only=True,
                page=1,
                page_size=limit,
            )

        context_items: List[Dict[str, Any]] = []
        citations: List[SourceCitation] = []

        for f in faqs:
            item = {
                "id": f.id,
                "question": f.question,
                "answer": f.answer,
                "category": f.category,
            }
            context_items.append(item)
            citations.append(
                SourceCitation(
                    type="faq",
                    id=f.id,
                    name=f"FAQ: {f.question[:60]}...",
                    category=f.category,
                    url="/faqs",
                    snippet=f.answer[:120] + "...",
                )
            )

        return context_items, citations

    @staticmethod
    def check_user_eligibility_context(
        db: Session,
        query: str,
        profile_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        target_scheme = RetrievalService.resolve_target_scheme(db, query, conversation_history)
        if not target_scheme:
            # Check if any scheme was found by general keyword
            schemes, citations = RetrievalService.retrieve_schemes(db, query, current_user, limit=3)
            if schemes:
                target_scheme = db.query(Scheme).filter(Scheme.id == schemes[0]["id"]).first()

        if not target_scheme:
            # Prompt user to choose which scheme to check
            sample_schemes = (
                db.query(Scheme)
                .filter(Scheme.is_active == True, Scheme.status == SchemeStatus.ACTIVE.value)
                .limit(4)
                .all()
            )
            return {
                "status": "SELECT_SCHEME",
                "message": "Which government scheme would you like to check your eligibility for?",
                "available_schemes": [s.name for s in sample_schemes],
            }, []

        # Parse user attributes
        req = RetrievalService.extract_profile_from_context(query, profile_context, conversation_history)

        rules = [r for r in target_scheme.eligibility_rules if r.is_active]
        portal = RetrievalService.get_scheme_portal(target_scheme)
        docs = RetrievalService.get_scheme_documents(target_scheme)

        # Check required fields defined across rules
        required_fields = set()
        for r in rules:
            if r.criteria_json:
                try:
                    c = json.loads(r.criteria_json)
                    if isinstance(c, dict):
                        if "min_age" in c or "max_age" in c:
                            required_fields.add("Age")
                        if "min_income" in c or "max_income" in c:
                            required_fields.add("Annual Family Income")
                        if "occupation" in c or "allowed_occupations" in c:
                            required_fields.add("Occupation / Employment Status")
                        if "state" in c or "allowed_states" in c:
                            required_fields.add("State of Residence / Domicile")
                        if "gender" in c or "allowed_genders" in c:
                            required_fields.add("Gender")
                        if "social_category" in c or "allowed_categories" in c:
                            required_fields.add("Social Category (General/OBC/SC/ST)")
                except Exception:
                    pass

        # Identify which required fields are missing
        missing_fields = []
        if "Age" in required_fields and req.age is None:
            missing_fields.append("Your Age in years")
        if "Annual Family Income" in required_fields and req.income is None:
            missing_fields.append("Your Annual Family Income (INR)")
        if "Occupation / Employment Status" in required_fields and not req.occupation:
            missing_fields.append("Your Current Occupation (e.g. Student, Farmer, Business)")
        if "State of Residence / Domicile" in required_fields and not req.location:
            missing_fields.append("Your State of Residence (Domicile)")
        if "Gender" in required_fields and not req.gender:
            missing_fields.append("Your Gender")
        if "Social Category (General/OBC/SC/ST)" in required_fields and not req.social_category:
            missing_fields.append("Your Social Category (General, OBC, SC, ST, or BPL)")

        all_passed = []
        all_failed = []
        is_eligible = True

        for r in rules:
            res = EligibilityService.evaluate_rule(r, req)
            if not res.get("passed", False):
                is_eligible = False
            all_passed.extend(res.get("matched", []))
            all_failed.extend(res.get("failed", []))

        # Filter out "Age required to verify..." from failed if missing_fields is tracked
        pure_failed = [f for f in all_failed if not ("required to verify" in f or "required" in f)]

        citations = [
            SourceCitation(
                type="scheme",
                id=target_scheme.id,
                name=target_scheme.name,
                category=target_scheme.category or "Welfare Scheme",
                url=f"/schemes/{target_scheme.id}",
                snippet=f"Category: {target_scheme.category} | State: {target_scheme.state} | Official Portal: {portal}",
            )
        ]

        if missing_fields:
            return {
                "status": "MISSING_INFO",
                "scheme_id": target_scheme.id,
                "scheme_name": target_scheme.name,
                "missing_fields": missing_fields,
                "required_criteria": [r.description or r.rule_name for r in rules],
                "verified_so_far": all_passed,
                "provided_profile": req.model_dump(exclude_unset=True),
                "official_url": portal,
                "required_documents": docs,
            }, citations

        return {
            "status": "EVALUATED",
            "scheme_id": target_scheme.id,
            "scheme_name": target_scheme.name,
            "is_eligible": is_eligible,
            "matched_criteria": all_passed,
            "failed_criteria": pure_failed,
            "benefits": target_scheme.benefits,
            "application_process": target_scheme.application_process,
            "official_url": portal,
            "required_documents": docs,
            "user_profile": req.model_dump(exclude_unset=True),
        }, citations

    @staticmethod
    def retrieve_application_guidance(
        db: Session,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Retrieve step-by-step application guidance, required documents, and official portal link."""
        target_scheme = RetrievalService.resolve_target_scheme(db, query, conversation_history)
        if not target_scheme:
            schemes, _ = RetrievalService.retrieve_schemes(db, query, current_user, limit=1)
            if schemes:
                target_scheme = db.query(Scheme).filter(Scheme.id == schemes[0]["id"]).first()

        if not target_scheme:
            sample_schemes = (
                db.query(Scheme)
                .filter(Scheme.is_active == True, Scheme.status == SchemeStatus.ACTIVE.value)
                .limit(4)
                .all()
            )
            return {
                "status": "SELECT_SCHEME",
                "message": "Which scheme would you like step-by-step application guidance for?",
                "available_schemes": [s.name for s in sample_schemes],
            }, []

        portal = RetrievalService.get_scheme_portal(target_scheme)
        docs = RetrievalService.get_scheme_documents(target_scheme)

        citations = [
            SourceCitation(
                type="scheme",
                id=target_scheme.id,
                name=target_scheme.name,
                category=target_scheme.category or "Application Guide",
                url=f"/schemes/{target_scheme.id}",
                snippet=f"Official Portal: {portal} | Application Mode: Online & CSC",
            )
        ]

        return {
            "status": "GUIDANCE_READY",
            "scheme_id": target_scheme.id,
            "scheme_name": target_scheme.name,
            "department": target_scheme.department or "Government Administration",
            "ministry": target_scheme.ministry or "Government of India",
            "application_mode": "Online (National/State Portal) and Offline (Common Service Centres - CSC / Citizen Kiosks)",
            "step_by_step_process": target_scheme.application_process or "1. Visit the official portal -> 2. Register with Aadhaar -> 3. Fill personal & bank details -> 4. Upload required documents -> 5. Submit application.",
            "required_documents": docs,
            "official_portal": portal,
            "benefits": target_scheme.benefits,
        }, citations

    @staticmethod
    def compare_schemes_context(
        db: Session,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[Dict[str, Any], List[SourceCitation]]:
        """Extract Scheme A and Scheme B, or prompt for second scheme if only one is known."""
        active_schemes = (
            db.query(Scheme)
            .filter(
                Scheme.is_active == True,
                Scheme.status.in_([SchemeStatus.ACTIVE.value, SchemeStatus.PUBLISHED.value]),
                ~Scheme.name.ilike("%test%"),
                ~Scheme.name.ilike("%dummy%"),
            )
            .all()
        )

        found_schemes: List[Scheme] = []
        q_l = query.lower()

        # Find explicitly mentioned schemes in query
        for s in active_schemes:
            if s.name.lower() in q_l:
                if s not in found_schemes:
                    found_schemes.append(s)
            else:
                words = [w for w in s.name.lower().split() if len(w) > 3 and w not in ["scheme", "yojana", "pradhan", "mantri", "national"]]
                if any(w in q_l for w in words):
                    if s not in found_schemes:
                        found_schemes.append(s)

        # If only 0 or 1 scheme found in query, resolve Scheme A from conversation context
        if len(found_schemes) < 2:
            ctx_scheme = RetrievalService.resolve_target_scheme(db, query, conversation_history)
            if ctx_scheme and ctx_scheme not in found_schemes:
                found_schemes.insert(0, ctx_scheme)

        if len(found_schemes) == 0:
            sample_schemes = active_schemes[:4]
            return {
                "status": "SELECT_SCHEMES_TO_COMPARE",
                "message": "Please specify two government schemes you would like to compare side-by-side.",
                "available_schemes": [s.name for s in sample_schemes],
            }, []

        if len(found_schemes) == 1:
            scheme_a = found_schemes[0]
            suggestions = [s.name for s in active_schemes if s.id != scheme_a.id][:4]
            return {
                "status": "NEED_SECOND_SCHEME",
                "scheme_a_name": scheme_a.name,
                "scheme_a_category": scheme_a.category,
                "suggestions": suggestions,
            }, [
                SourceCitation(
                    type="scheme",
                    id=scheme_a.id,
                    name=scheme_a.name,
                    category=scheme_a.category or "Comparison",
                    url=f"/schemes/{scheme_a.id}",
                    snippet=f"Selected for comparison: {scheme_a.name}",
                )
            ]

        # We have at least 2 schemes to compare
        s_a, s_b = found_schemes[0], found_schemes[1]

        def _format_scheme_comp(s: Scheme) -> Dict[str, Any]:
            rules = [r.description or r.rule_name for r in s.eligibility_rules if r.is_active]
            return {
                "id": s.id,
                "name": s.name,
                "category": s.category or "General Welfare",
                "department": s.department or "Central/State Authority",
                "ministry": s.ministry or "Government of India",
                "target_audience": s.target_audience or "Eligible Citizens",
                "eligibility_summary": "; ".join(rules) if rules else "General eligibility as per department norms",
                "benefits": s.benefits or "Financial / welfare benefits provided",
                "financial_assistance": s.benefits or "Direct Benefit Transfer (DBT)",
                "required_documents": ", ".join(RetrievalService.get_scheme_documents(s)),
                "application_process": s.application_process or "Online submission via official portal",
                "application_mode": "Online & CSC Kiosks",
                "state": s.state or "All India",
                "official_portal": RetrievalService.get_scheme_portal(s),
            }

        citations = [
            SourceCitation(type="scheme", id=s_a.id, name=s_a.name, category=s_a.category, url=f"/schemes/{s_a.id}", snippet=f"Comparison Scheme 1: {s_a.name}"),
            SourceCitation(type="scheme", id=s_b.id, name=s_b.name, category=s_b.category, url=f"/schemes/{s_b.id}", snippet=f"Comparison Scheme 2: {s_b.name}"),
        ]

        return {
            "status": "COMPARED",
            "scheme_a": _format_scheme_comp(s_a),
            "scheme_b": _format_scheme_comp(s_b),
        }, citations
