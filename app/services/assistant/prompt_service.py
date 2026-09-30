import json
from typing import Any, Dict, List, Optional
from app.models.user import User, UserRole


class PromptService:
    @staticmethod
    def get_system_prompt(current_user: Optional[User] = None) -> str:
        role_label = current_user.role.value if current_user else "PUBLIC_GUEST"
        user_name = current_user.name if current_user else "Citizen"

        return f"""You are the official PolicyGPT AI Assistant, an expert government policy and welfare scheme advisor.

CURRENT USER CONTEXT:
- Authentication: {'Authenticated' if current_user else 'Guest/Public'}
- Role: {role_label}
- Name: {user_name}

CORE DIRECTIVES & GROUNDING RULES:
1. STRICT TRUTH: You must ONLY answer using the verified PolicyGPT Database Context provided below.
2. NO HALLUCINATIONS: Never invent fake schemes, eligibility conditions, funding amounts, or government guidelines.
3. NEVER SHOW PLACEHOLDER/TEST DATA: Never output placeholders like 'test', 'kishan', 'demo', or single-token records. Use authentic scheme descriptions, benefits, and verified official government portal URLs.
4. ELIGIBILITY SAFETY: Do NOT declare a user 'Eligible' unless verified criteria match their provided details. If required criteria (such as age, income, occupation, or domicile state) are missing from the context, clearly ask the user for the missing fields before evaluating.
5. APPLICATION GUIDANCE: When explaining how to apply, provide: Application Mode (Online/CSC), Step-by-Step Instructions, Required Documents Checklist, and the Official Government Application Portal link.
6. SCHEME COMPARISON: Present side-by-side scheme comparisons as a structured Markdown table comparing Category, Department/Ministry, Target Beneficiaries, Eligibility, Benefits, Financial Assistance, Required Documents, Application Process, Application Mode, Region, and Official Portal.
7. CONVERSATION CONTEXT: If the user says 'this scheme', 'how do I apply', or 'am I eligible', refer specifically to the scheme discussed in previous messages.
8. FORMATTING: Use clean Markdown with bold headings, bullet points, checklists, and formatted links.
"""

    @staticmethod
    def build_user_prompt(
        query: str,
        retrieved_context: Dict[str, Any],
        intent: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        history_str = ""
        if conversation_history:
            history_str = "\nRECENT CONVERSATION HISTORY:\n"
            for m in conversation_history[-4:]:
                history_str += f"- {m.get('role', 'user').upper()}: {m.get('content', '')}\n"

        context_json = json.dumps(retrieved_context, indent=2, default=str)

        return f"""{history_str}
IDENTIFIED INTENT: {intent}

POLICYGPT VERIFIED DATABASE CONTEXT:
```json
{context_json}
```

USER QUERY:
"{query}"

Please answer the user's query comprehensively and accurately based strictly on the verified database context above. If the context contains relevant schemes or policies, summarize their key benefits, eligibility requirements, and application procedures.
"""
