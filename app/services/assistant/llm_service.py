import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Multi-provider LLM abstraction supporting Google Gemini, OpenAI, and
    an intelligent built-in deterministic grounding fallback engine.
    """

    @classmethod
    def generate_response(
        cls,
        system_prompt: str,
        user_prompt: str,
        intent: str,
        retrieved_context: Dict[str, Any],
    ) -> str:
        start_time = time.time()
        api_key_gemini = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        api_key_openai = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

        # 1. Try Gemini if configured
        if api_key_gemini and (settings.LLM_PROVIDER in ("gemini", "auto")):
            try:
                answer = cls._call_gemini(api_key_gemini, system_prompt, user_prompt)
                if answer:
                    logger.info(f"Generated response via Gemini in {time.time() - start_time:.2f}s")
                    return answer
            except Exception as e:
                logger.warning(f"Gemini API invocation failed: {e}. Falling back to grounded engine.")

        # 2. Try OpenAI if configured
        if api_key_openai and (settings.LLM_PROVIDER in ("openai", "auto")):
            try:
                answer = cls._call_openai(api_key_openai, system_prompt, user_prompt)
                if answer:
                    logger.info(f"Generated response via OpenAI in {time.time() - start_time:.2f}s")
                    return answer
            except Exception as e:
                logger.warning(f"OpenAI API invocation failed: {e}. Falling back to grounded engine.")

        # 3. Intelligent Built-in Grounded Synthesis Engine (Zero hallucination fallback)
        logger.info("Using PolicyGPT Built-in Grounded Engine for response generation.")
        return cls._generate_grounded_fallback(intent, retrieved_context)

    @classmethod
    def _call_gemini(cls, api_key: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        model = settings.LLM_MODEL_NAME if "gemini" in settings.LLM_MODEL_NAME else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
        return None

    @classmethod
    def _call_openai(cls, api_key: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            else:
                logger.warning(f"OpenAI API returned status {resp.status_code}: {resp.text}")
        return None

    @classmethod
    def _generate_grounded_fallback(cls, intent: str, context: Dict[str, Any]) -> str:
        """
        Deterministic, hallucination-free response synthesis based strictly
        on verified platform records.
        """
        if intent == "scheme_search":
            schemes = context.get("schemes", [])
            if not schemes:
                return (
                    "I searched the PolicyGPT database but could not find any active government schemes "
                    "matching your query criteria. Please try broadening your search keywords (e.g., 'Education', "
                    "'Agriculture', 'Gujarat', 'Women') or check the full schemes repository."
                )

            lines = [f"Found **{len(schemes)} verified government scheme(s)** in the PolicyGPT database:\n"]
            for i, s in enumerate(schemes, start=1):
                name = s.get("name", "Government Scheme")
                category = s.get("category", "General Welfare")
                dept = s.get("department") or s.get("ministry") or "Central/State Authority"
                state = s.get("state", "All India")
                target = s.get("target_audience", "Eligible Citizens")
                benefits = s.get("benefits", "Financial assistance as per official norms.")
                desc = s.get("description", "Government welfare program.")
                app_proc = s.get("application_process", "Apply online through the official portal.")
                app_mode = s.get("application_mode", "Online & Common Service Centres (CSC)")
                portal = s.get("official_url", "https://www.india.gov.in")
                rules = s.get("eligibility_rules", [])
                docs = s.get("required_documents", [])

                lines.append(f"### {i}. {name}")
                lines.append(f"*{desc}*\n")
                lines.append(f"- **Category / Domain:** {category}")
                lines.append(f"- **Administering Authority:** {dept}")
                lines.append(f"- **Applicable Region:** {state}")
                lines.append(f"- **Target Beneficiaries:** {target}")
                lines.append(f"- **Key Benefits:** {benefits}")
                if rules:
                    lines.append(f"- **Eligibility Summary:** {'; '.join(rules)}")
                if docs:
                    lines.append(f"- **Required Documents:** {', '.join(docs)}")
                lines.append(f"- **Application Mode:** {app_mode}")
                lines.append(f"- **How to Apply:** {app_proc}")
                lines.append(f"- **Official Application Portal:** [{portal}]({portal})\n")

            lines.append("You can click on any source card below to view full details or ask me: *'Am I eligible for this scheme?'* or *'How do I apply?'*")
            return "\n".join(lines)

        elif intent == "application_guidance":
            status = context.get("status")
            if status == "SELECT_SCHEME":
                available = context.get("available_schemes", [])
                lines = [
                    "Please specify which government scheme you would like step-by-step application guidance for.\n",
                    "**Available Verified Schemes:**",
                ]
                for s_name in available:
                    lines.append(f"- **{s_name}**")
                lines.append("\nYou can reply with the scheme name to get immediate application instructions.")
                return "\n".join(lines)

            scheme_name = context.get("scheme_name", "Scheme")
            dept = context.get("department") or context.get("ministry") or "Administrative Department"
            portal = context.get("official_portal", "https://www.india.gov.in")
            app_mode = context.get("application_mode", "Online and Offline")
            process = context.get("step_by_step_process", "Apply via official portal.")
            docs = context.get("required_documents", [])
            benefits = context.get("benefits", "Direct scheme benefits.")

            lines = [
                f"### How to Apply for **{scheme_name}**\n",
                f"- **Administering Department:** {dept}",
                f"- **Application Mode:** {app_mode}",
                f"- **Official Portal Link:** [{portal}]({portal})",
                f"- **Key Benefits Provided:** {benefits}\n",
                "#### Step-by-Step Application Process:",
            ]

            # Format steps
            if "->" in process:
                steps = [st.strip() for st in process.split("->") if st.strip()]
                for st in steps:
                    lines.append(f"- {st}")
            else:
                lines.append(f"{process}\n")

            if docs:
                lines.append("\n#### Required Documents Checklist:")
                for d in docs:
                    lines.append(f"- [x] {d}")

            lines.append(f"\nFor online submission, please proceed to the verified portal: [{portal}]({portal})")
            return "\n".join(lines)

        elif intent == "eligibility":
            status = context.get("status")
            if status == "SELECT_SCHEME":
                available = context.get("available_schemes", [])
                lines = [
                    "Which government scheme would you like to check your eligibility for?\n",
                    "**Available Schemes to evaluate:**",
                ]
                for s_name in available:
                    lines.append(f"- **{s_name}**")
                lines.append("\nPlease reply with the scheme name, or provide your age, state, and income.")
                return "\n".join(lines)

            elif status == "MISSING_INFO":
                scheme_name = context.get("scheme_name", "Scheme")
                missing = context.get("missing_fields", [])
                req_crit = context.get("required_criteria", [])
                verified = context.get("verified_so_far", [])
                portal = context.get("official_url", "")

                lines = [
                    f"### Scheme Eligibility Assessment: **{scheme_name}**\n",
                    "To accurately determine your eligibility, I need a few more details from you:\n",
                    "**Please provide the following information:**",
                ]
                for m in missing:
                    lines.append(f"- **{m}**")

                if req_crit:
                    lines.append("\n**Official Eligibility Requirements for this Scheme:**")
                    for c in req_crit:
                        lines.append(f"- {c}")

                if verified:
                    lines.append("\n**Criteria Verified So Far:**")
                    for v in verified:
                        lines.append(f"- *Passed:* {v}")

                lines.append("\n*Note: We do not declare eligibility until your verified criteria match all official requirements.*")
                return "\n".join(lines)

            elif status == "EVALUATED":
                scheme_name = context.get("scheme_name", "Scheme")
                is_elig = context.get("is_eligible", False)
                matched = context.get("matched_criteria", [])
                failed = context.get("failed_criteria", [])
                portal = context.get("official_url", "")

                status_label = "**Eligible based on provided information**" if is_elig else "**Not Eligible based on provided criteria**"

                lines = [
                    f"### Scheme Eligibility Assessment: **{scheme_name}**\n",
                    f"Assessment Outcome: {status_label}\n",
                ]

                if matched:
                    lines.append("**Matched Eligibility Criteria:**")
                    for m in matched:
                        lines.append(f"- {m}")
                    lines.append("")

                if failed:
                    lines.append("**Unmet Conditions / Ineligible Factors:**")
                    for f in failed:
                        lines.append(f"- {f}")
                    lines.append("")

                if is_elig:
                    lines.append(f"You can proceed to apply directly at the official portal: [{portal}]({portal})")
                else:
                    lines.append("You may explore alternative schemes or contact the department for special category relaxations.")

                return "\n".join(lines)

            # Fallback evaluations list
            evaluations = context.get("evaluations", [])
            if not evaluations:
                return (
                    "To check your exact eligibility for government schemes, please specify the scheme name "
                    "and provide your profile details (such as age, income, state, category, or occupation)."
                )

            lines = ["### Scheme Eligibility Assessment\n"]
            for ev in evaluations:
                s_name = ev.get("scheme_name", "Scheme")
                is_elig = ev.get("is_eligible", False)
                status_str = "Eligible based on criteria" if is_elig else "Requirements Pending / Ineligible"
                lines.append(f"**{s_name}**: **{status_str}**")
                if ev.get("matched_criteria"):
                    lines.append("- *Matched:* " + "; ".join(ev["matched_criteria"]))
                if ev.get("failed_criteria"):
                    lines.append("- *Conditions/Remarks:* " + "; ".join(ev["failed_criteria"]))
                lines.append("")

            return "\n".join(lines)

        elif intent == "comparison":
            status = context.get("status")
            if status == "SELECT_SCHEMES_TO_COMPARE":
                available = context.get("available_schemes", [])
                lines = [
                    "Please specify two government schemes you would like to compare side-by-side.\n",
                    "**Available schemes for comparison:**",
                ]
                for s_name in available:
                    lines.append(f"- **{s_name}**")
                return "\n".join(lines)

            elif status == "NEED_SECOND_SCHEME":
                s_a_name = context.get("scheme_a_name", "Scheme A")
                s_a_cat = context.get("scheme_a_category", "General")
                suggestions = context.get("suggestions", [])

                lines = [
                    f"You have selected **{s_a_name}** ({s_a_cat}). Which second government scheme would you like to compare it with?\n",
                    "**Suggested comparison options:**",
                ]
                for sug in suggestions:
                    lines.append(f"- **{sug}**")
                lines.append(f"\nReply with: *'Compare {s_a_name} with [Scheme Name]'* to generate the full comparison table.")
                return "\n".join(lines)

            elif status == "COMPARED":
                s_a = context.get("scheme_a", {})
                s_b = context.get("scheme_b", {})

                lines = [
                    f"### Side-by-Side Scheme Comparison\n",
                    f"Comparing **{s_a.get('name')}** vs **{s_b.get('name')}**:\n",
                    "| Feature | " + s_a.get('name', 'Scheme A') + " | " + s_b.get('name', 'Scheme B') + " |",
                    "| :--- | :--- | :--- |",
                    f"| **Category** | {s_a.get('category', 'N/A')} | {s_b.get('category', 'N/A')} |",
                    f"| **Department / Ministry** | {s_a.get('ministry', s_a.get('department', 'N/A'))} | {s_b.get('ministry', s_b.get('department', 'N/A'))} |",
                    f"| **Target Beneficiaries** | {s_a.get('target_audience', 'Eligible Citizens')} | {s_b.get('target_audience', 'Eligible Citizens')} |",
                    f"| **Eligibility Summary** | {s_a.get('eligibility_summary', 'As per norms')} | {s_b.get('eligibility_summary', 'As per norms')} |",
                    f"| **Key Benefits** | {s_a.get('benefits', 'N/A')} | {s_b.get('benefits', 'N/A')} |",
                    f"| **Financial Assistance** | {s_a.get('financial_assistance', 'DBT transfer')} | {s_b.get('financial_assistance', 'DBT transfer')} |",
                    f"| **Required Documents** | {s_a.get('required_documents', 'Aadhaar, Income Certificate')} | {s_b.get('required_documents', 'Aadhaar, Income Certificate')} |",
                    f"| **Application Process** | {s_a.get('application_process', 'Online portal')} | {s_b.get('application_process', 'Online portal')} |",
                    f"| **Application Mode** | {s_a.get('application_mode', 'Online & CSC')} | {s_b.get('application_mode', 'Online & CSC')} |",
                    f"| **Applicable Region** | {s_a.get('state', 'All India')} | {s_b.get('state', 'All India')} |",
                    f"| **Official Portal** | [{s_a.get('official_portal', 'Portal')}]({s_a.get('official_portal', '')}) | [{s_b.get('official_portal', 'Portal')}]({s_b.get('official_portal', '')}) |",
                ]
                return "\n".join(lines)

            # Fallback comparison if raw data is provided
            comp_data = context.get("data", {})
            items = comp_data.get("items", [])
            if len(items) >= 2:
                it1, it2 = items[0], items[1]
                lines = [
                    f"### Side-by-Side Scheme Comparison\n",
                    f"| Feature | {it1.get('name')} | {it2.get('name')} |",
                    f"| :--- | :--- | :--- |",
                    f"| **Category** | {it1.get('category')} | {it2.get('category')} |",
                    f"| **Department** | {it1.get('department') or 'N/A'} | {it2.get('department') or 'N/A'} |",
                    f"| **Benefits** | {it1.get('benefits')} | {it2.get('benefits')} |",
                    f"| **Application Process** | {it1.get('application_process')} | {it2.get('application_process')} |",
                ]
                return "\n".join(lines)
            return "Please specify two schemes to perform a detailed side-by-side comparison."

        elif intent == "policy_search":
            policies = context.get("policies", [])
            if not policies:
                return (
                    "I could not find matching public policy documents in the database for your search query. "
                    "Try searching by sector (e.g., Healthcare, Energy, Education) or ministry."
                )

            lines = [f"Found **{len(policies)} public policy record(s)**:\n"]
            for i, p in enumerate(policies, start=1):
                lines.append(f"### {i}. {p.get('title')}")
                lines.append(f"- **Sector / Category:** {p.get('sector', p.get('category', 'National'))}")
                lines.append(f"- **Ministry / Dept:** {p.get('ministry', 'Central Government')}")
                lines.append(f"- **Summary:** {p.get('description', 'N/A')}\n")

            return "\n".join(lines)

        elif intent == "faq_support":
            faqs = context.get("faqs", [])
            if faqs:
                lines = ["Here is the verified guidance from our Help Desk & FAQs:\n"]
                for f in faqs:
                    lines.append(f"**Q: {f.get('question')}**")
                    lines.append(f"{f.get('answer')}\n")
                lines.append("If you still require assistance, you can use the **Contact Support** page to create a support ticket.")
                return "\n".join(lines)
            else:
                return (
                    "I could not locate an exact FAQ answering this query. "
                    "You can submit a ticket to our Help Desk via the **Contact Support** page in the Citizen Portal."
                )

        elif intent == "user_applications":
            apps = context.get("applications", [])
            if not apps:
                return "You do not have any submitted scheme applications on record. You can explore available schemes and submit applications through the portal."
            lines = [f"Here are your active scheme applications ({len(apps)}):\n"]
            for a in apps:
                lines.append(f"- **{a.get('scheme_name')}** (App #{a.get('application_number')})")
                lines.append(f"  Status: **{a.get('status')}** | Submitted: {a.get('created_at', '')[:10]}")
                if a.get("remarks"):
                    lines.append(f"  Remarks: {a.get('remarks')}")
            return "\n".join(lines)

        elif intent == "user_saved_policies":
            saved = context.get("saved_policies", [])
            if not saved:
                return "You have not bookmarked or saved any policies yet. You can bookmark policies while browsing the Policy repository."
            lines = [f"Here are your saved/bookmarked policies ({len(saved)}):\n"]
            for p in saved:
                lines.append(f"- **{p.get('title')}** (Saved on {p.get('saved_at', '')[:10]})")
            return "\n".join(lines)

        elif intent == "user_notifications":
            notifs = context.get("notifications", [])
            if notifs:
                lines = [f"Here are your latest account notifications ({len(notifs)}):\n"]
                for n in notifs:
                    status_badge = "Unread" if not n.get("is_read") else "Read"
                    lines.append(f"- **{n.get('title')}** [{status_badge}]")
                    lines.append(f"  {n.get('message')}")
                return "\n".join(lines)
            return "You have no unread notifications at this time."

        elif intent == "user_feedback":
            tickets = context.get("tickets", [])
            if not tickets:
                return "You have no active support tickets or submitted feedback records."
            lines = [f"Here are your submitted support tickets ({len(tickets)}):\n"]
            for t in tickets:
                lines.append(f"- **#{t.get('id')}: {t.get('subject')}** [{t.get('status')}]")
                if t.get("admin_response"):
                    lines.append(f"  *Resolution Note:* {t.get('admin_response')}")
            return "\n".join(lines)

        elif intent == "user_profile":
            prof = context.get("profile", {})
            return (
                f"### Your Profile Information\n"
                f"- **Name:** {prof.get('name')}\n"
                f"- **Email:** {prof.get('email')}\n"
                f"- **Role:** {prof.get('role')}\n"
                f"- **Phone:** {prof.get('phone_number')}\n"
            )

        return (
            "I am your PolicyGPT AI Assistant. You can ask me to search government schemes and policies, "
            "evaluate your scheme eligibility, compare multiple schemes, or assist with portal support questions."
        )
