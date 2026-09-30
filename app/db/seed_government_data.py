import json
import logging
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.models.scheme import Scheme, SchemeStatus
from app.models.policy import Policy, PolicyStatus
from app.models.faq import FAQ
from app.models.eligibility import EligibilityRule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    db = SessionLocal()
    try:
        # 1. Soft-archive or remove obvious dummy/test schemes
        dummy_schemes = db.query(Scheme).all()
        for s in dummy_schemes:
            name_lower = (s.name or "").lower()
            desc_lower = (s.description or "").lower()
            benefits_lower = (s.benefits or "").lower()
            is_dummy = (
                "test" in name_lower
                or "dummy" in name_lower
                or "kishan" in name_lower
                or name_lower.strip() in ["scheme", "schem1"]
                or len(name_lower.strip()) < 5
                or (benefits_lower in ["kishan", "test", "scheme", "pm kishan"])
            )
            if is_dummy:
                s.is_active = False
                s.status = SchemeStatus.ARCHIVED.value
                logger.info(f"Archived test scheme: id={s.id}, name='{s.name}'")

        # 2. Soft-archive dummy policies
        dummy_policies = db.query(Policy).all()
        for p in dummy_policies:
            title_lower = (p.title or "").lower()
            if "test" in title_lower or "mail" in title_lower or title_lower.strip() in ["policy", "pol", "viaksh"] or len(title_lower.strip()) < 5:
                p.is_active = False
                p.status = PolicyStatus.ARCHIVED.value
                logger.info(f"Archived test policy: id={p.id}, title='{p.title}'")

        # 3. Seed verified policies
        policies_data = [
            {
                "title": "National Education Policy 2020",
                "description": "Comprehensive framework to transform India's education system, emphasizing holistic, flexible, and multidisciplinary education alongside digital literacy and vocational training.",
                "category": "Education",
                "ministry": "Ministry of Education",
                "department": "Department of Higher Education",
                "sector": "Education & Skill Development",
                "state": "National",
                "status": PolicyStatus.PUBLISHED.value,
                "is_active": True,
            },
            {
                "title": "National Health Policy 2017",
                "description": "Aims to attain the highest possible level of health and well-being for all ages through preventive and promotive health care orientation and universal access to good quality health care services.",
                "category": "Healthcare",
                "ministry": "Ministry of Health and Family Welfare",
                "department": "Department of Health",
                "sector": "Healthcare & Wellness",
                "state": "National",
                "status": PolicyStatus.PUBLISHED.value,
                "is_active": True,
            },
            {
                "title": "Digital India Programme Policy",
                "description": "Flagship initiative to transform India into a digitally empowered society and knowledge economy through digital infrastructure, on-demand governance, and digital citizen empowerment.",
                "category": "Technology",
                "ministry": "Ministry of Electronics and Information Technology",
                "department": "Digital India Corporation",
                "sector": "Governance & Technology",
                "state": "National",
                "status": PolicyStatus.PUBLISHED.value,
                "is_active": True,
            },
            {
                "title": "National Green Mobility Policy 2026",
                "description": "National policy driving transition to zero-emission electric mobility, public transit decarbonization, battery manufacturing ecosystems, and consumer incentives.",
                "category": "Energy & Environment",
                "ministry": "Ministry of Heavy Industries",
                "department": "Automotive Development Division",
                "sector": "Renewable Energy & Clean Mobility",
                "state": "National",
                "status": PolicyStatus.PUBLISHED.value,
                "is_active": True,
            },
        ]

        created_policies = {}
        for pdata in policies_data:
            existing = db.query(Policy).filter(Policy.title == pdata["title"]).first()
            if not existing:
                pol = Policy(**pdata)
                db.add(pol)
                db.flush()
                created_policies[pdata["title"]] = pol
                logger.info(f"Created Policy: '{pol.title}'")
            else:
                existing.is_active = True
                existing.status = PolicyStatus.PUBLISHED.value
                created_policies[pdata["title"]] = existing

        # 4. Seed Verified Government Welfare Schemes
        schemes_data = [
            {
                "name": "PM Kisan Samman Nidhi Yojana",
                "description": "Central sector welfare scheme providing direct financial assistance to small and marginal farmer families across India to support agricultural inputs and domestic needs.",
                "benefits": "Direct income benefit of ₹6,000 per year transferred in 3 equal four-monthly installments of ₹2,000 each directly into farmer bank accounts via Direct Benefit Transfer (DBT).",
                "target_audience": "Small and marginal farmers with cultivable landholding",
                "category": "Farmer Welfare",
                "department": "Department of Agriculture and Farmers Welfare",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "state": "All India",
                "sector": "Agriculture & Rural Development",
                "application_process": "1. Visit the official PM-Kisan portal (https://pmkisan.gov.in) -> 2. Click 'New Farmer Registration' under Farmers Corner -> 3. Enter Aadhaar number, state, and mobile number -> 4. Enter land record details (Khata/Khasra numbers) and bank details -> 5. Submit for state revenue department e-KYC verification.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Farmer Age & Landholding Criteria",
                        "criteria_json": json.dumps({"min_age": 18, "occupation": ["farmer", "agriculture"]}),
                        "description": "Applicant must be an Indian citizen aged 18+ who owns cultivable agricultural land. Institutional landholders and income-tax payers are excluded.",
                    }
                ],
            },
            {
                "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
                "description": "The world's largest government-funded healthcare assurance scheme providing comprehensive health cover for secondary and tertiary hospitalization to economically vulnerable citizens.",
                "benefits": "Cashless and paperless inpatient health insurance cover of up to ₹5,00,000 per family per year across thousands of empanelled public and private hospitals across India.",
                "target_audience": "Low income families, rural deprived households, and identified occupational urban workers",
                "category": "Healthcare",
                "department": "National Health Authority (NHA)",
                "ministry": "Ministry of Health and Family Welfare",
                "state": "All India",
                "sector": "Healthcare & Wellness",
                "application_process": "1. Visit the official portal (https://mera.pmjay.gov.in) to check family eligibility -> 2. Visit any Empanelled Health Care Provider (EHCP) hospital or CSC center with Aadhaar/Ration Card -> 3. Complete biometric e-KYC -> 4. Receive Ayushman Card for instant cashless admission.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Income and SECC Deprivation Criteria",
                        "criteria_json": json.dumps({"max_income": 300000, "social_category": ["SC", "ST", "OBC", "General", "BPL"]}),
                        "description": "Annual household income must be under ₹3,00,000 or listed under Socio-Economic Caste Census (SECC) deprivation categories.",
                    }
                ],
            },
            {
                "name": "Pradhan Mantri Awas Yojana (PMAY)",
                "description": "Comprehensive housing mission providing financial subsidies and interest concessions to ensure every eligible family has access to a pucca house with basic amenities.",
                "benefits": "Direct financial grant and Credit Linked Subsidy Scheme (CLSS) interest subsidy up to ₹2.67 Lakh on home loans for purchase, construction, or enhancement of a dwelling unit.",
                "target_audience": "Economically Weaker Section (EWS), Low Income Groups (LIG), and Middle Income Groups (MIG)",
                "category": "Housing",
                "department": "Ministry of Housing and Urban Affairs",
                "ministry": "Ministry of Housing and Urban Affairs",
                "state": "All India",
                "sector": "Housing & Urban Affairs",
                "application_process": "1. Access the official PMAY portal (https://pmaymis.gov.in) -> 2. Select 'Citizen Assessment' and enter Aadhaar details -> 3. Fill personal, income, present address, and proposed dwelling details -> 4. Upload income certificate and property papers -> 5. Track approval via Application ID.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Housing Domicile & Income Ceiling Criteria",
                        "criteria_json": json.dumps({"min_age": 21, "max_income": 600000}),
                        "description": "Applicant must be aged 21+, must not own a pucca house in India, and household income must fall within EWS/LIG limits (up to ₹6,00,000).",
                    }
                ],
            },
            {
                "name": "National Post-Matric Scholarship Scheme for Students",
                "description": "Merit-cum-means scholarship scheme providing financial assistance to underprivileged students pursuing post-matriculation or post-secondary education in recognized institutions.",
                "benefits": "100% tuition and compulsory non-refundable fees reimbursement plus monthly maintenance allowance of up to ₹20,000 per academic year credited via DBT.",
                "target_audience": "Students enrolled in Class 11, Class 12, ITI, Diploma, Undergraduate, or Postgraduate courses",
                "category": "Scholarships",
                "department": "Department of Higher Education",
                "ministry": "Ministry of Education",
                "state": "All India",
                "sector": "Education & Student Welfare",
                "application_process": "1. Register on the National Scholarship Portal (https://scholarships.gov.in) -> 2. Complete student profile with Aadhaar and bank details -> 3. Choose Post-Matric Scholarship -> 4. Upload previous year marksheet, fee receipt, and income certificate -> 5. Submit for Institute and State Nodal verification.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Student Enrolled & Family Income Limit",
                        "criteria_json": json.dumps({"min_age": 15, "max_age": 30, "max_income": 250000, "occupation": ["student"]}),
                        "description": "Enrolled in recognized post-matric course. Age 15–30. Family annual income from all sources must not exceed ₹2,50,000.",
                    }
                ],
            },
            {
                "name": "Pradhan Mantri Mudra Yojana (PMMY)",
                "description": "Micro-finance scheme facilitating easy, collateral-free credit to non-corporate, non-farm small and micro enterprises for income-generating business activities.",
                "benefits": "Collateral-free loans up to ₹10 Lakh in three tiers: Shishu (loans up to ₹50,000), Kishore (loans ₹50,000 to ₹5 Lakh), and Tarun (loans ₹5 Lakh to ₹10 Lakh) with affordable interest rates.",
                "target_audience": "Micro-entrepreneurs, artisans, shopkeepers, small manufacturers, and self-employed youth",
                "category": "Business Support",
                "department": "Department of Financial Services",
                "ministry": "Ministry of Finance",
                "state": "All India",
                "sector": "Financial Services & Micro Enterprises",
                "application_process": "1. Apply online on the Udyamimitra portal (https://www.mudra.org.in) or visit any commercial bank or NBFC -> 2. Fill standard Mudra application form with business proposal -> 3. Submit KYC documents, business registration, and purchase quotations -> 4. Loan sanctioned and Mudra debit card issued.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Indian Citizen Micro-Enterprise Criteria",
                        "criteria_json": json.dumps({"min_age": 18, "max_age": 65, "occupation": ["business", "self-employed", "entrepreneur", "artisan"]}),
                        "description": "Indian citizen aged 18–65 with a viable business plan for non-farm micro enterprise.",
                    }
                ],
            },
            {
                "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
                "description": "Maternity benefit programme providing conditional cash transfers to pregnant women and lactating mothers for improved health and nutrition during pregnancy and childbirth.",
                "benefits": "Cash incentive of ₹5,000 in two installments for the first live child and ₹6,000 for a second girl child directly credited into mother's Aadhaar-linked bank account.",
                "target_audience": "Pregnant women and lactating mothers from low and middle income families",
                "category": "Women Empowerment",
                "department": "Department of Women and Child Development",
                "ministry": "Ministry of Women and Child Development",
                "state": "All India",
                "sector": "Women & Child Development",
                "application_process": "1. Register at nearest Anganwadi Centre (AWC) or apply online at PMMVY portal (https://pmmvy.wcd.gov.in) -> 2. Submit Mother and Child Protection (MCP) card -> 3. Complete antenatal checkups -> 4. DBT funds credited on institutional delivery and vaccination milestones.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Maternal Age & Health Registration Criteria",
                        "criteria_json": json.dumps({"gender": ["female"], "min_age": 19, "max_income": 800000}),
                        "description": "Pregnant women aged 19+ registered at Anganwadi/Health Centres. Regular government employees are excluded.",
                    }
                ],
            },
            {
                "name": "PM Surya Ghar: Muft Bijli Yojana",
                "description": "Nationwide green energy initiative offering capital subsidies for installing rooftop solar panels on residential homes, delivering up to 300 units of free electricity every month.",
                "benefits": "Direct capital subsidy of ₹30,000 for 1 kW systems, ₹60,000 for 2 kW systems, and up to ₹78,000 for 3 kW+ rooftop solar systems, reducing domestic electricity bills to zero.",
                "target_audience": "Residential homeowners with suitable roof area and active grid electricity connection",
                "category": "Social Security",
                "department": "Ministry of New and Renewable Energy",
                "ministry": "Ministry of New and Renewable Energy",
                "state": "All India",
                "sector": "Renewable Energy & Environment",
                "application_process": "1. Register on National Portal (https://pmsuryaghar.gov.in) with electricity consumer number -> 2. Submit application for rooftop solar -> 3. Receive technical feasibility approval from DISCOM -> 4. Complete installation via empaneled vendor -> 5. Receive net-meter inspection and DBT subsidy credit.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Residential Homeowner Criteria",
                        "criteria_json": json.dumps({"min_age": 18}),
                        "description": "Indian citizen aged 18+ with active residential electricity connection and rooftop ownership.",
                    }
                ],
            },
            {
                "name": "Mukhyamantri Amrutam (MA) Yojana",
                "description": "State healthcare assistance program providing cashless tertiary medical treatment to lower income and BPL families domiciled in Gujarat.",
                "benefits": "Comprehensive cashless coverage up to ₹5,00,000 per family per year for cardiovascular diseases, neurosurgery, burns, poly-trauma, cancer, renal diseases, and neonatal diseases.",
                "target_audience": "Families domiciled in Gujarat with annual income up to ₹4,00,000",
                "category": "Healthcare",
                "department": "Health and Family Welfare Department",
                "ministry": "Government of Gujarat",
                "state": "Gujarat",
                "sector": "State Healthcare",
                "application_process": "1. Visit nearest Taluka Civic Centre or Kiosk in Gujarat -> 2. Submit income certificate and Gujarat ration card -> 3. Complete biometric and photo enrollment -> 4. Receive instant MA Card for cashless treatment at empanelled hospitals.",
                "status": SchemeStatus.ACTIVE.value,
                "is_active": True,
                "rules": [
                    {
                        "rule_name": "Gujarat Domicile & Income Threshold",
                        "criteria_json": json.dumps({"state": ["gujarat"], "max_income": 400000}),
                        "description": "Resident of Gujarat with annual family income up to ₹4,00,000.",
                    }
                ],
            },
        ]

        for sdata in schemes_data:
            rules_data = sdata.pop("rules", [])
            existing_scheme = db.query(Scheme).filter(Scheme.name == sdata["name"]).first()
            if not existing_scheme:
                scheme = Scheme(**sdata)
                db.add(scheme)
                db.flush()
                logger.info(f"Created Scheme: '{scheme.name}' (ID: {scheme.id})")
                for rdata in rules_data:
                    rule = EligibilityRule(scheme_id=scheme.id, is_active=True, **rdata)
                    db.add(rule)
            else:
                for k, v in sdata.items():
                    setattr(existing_scheme, k, v)
                existing_scheme.is_active = True
                existing_scheme.status = SchemeStatus.ACTIVE.value
                db.flush()
                # Clear and re-add rules
                for rdata in rules_data:
                    existing_rule = db.query(EligibilityRule).filter(
                        EligibilityRule.scheme_id == existing_scheme.id,
                        EligibilityRule.rule_name == rdata["rule_name"]
                    ).first()
                    if not existing_rule:
                        rule = EligibilityRule(scheme_id=existing_scheme.id, is_active=True, **rdata)
                        db.add(rule)
                    else:
                        existing_rule.criteria_json = rdata.get("criteria_json")
                        existing_rule.description = rdata.get("description")
                        existing_rule.is_active = True

        # 5. Seed FAQs
        faqs_data = [
            {
                "question": "How do I search and apply for government welfare schemes?",
                "answer": "You can explore schemes in PolicyGPT by category, state, or keywords. Once you find a scheme, view its details to check eligibility rules, required documents, and click the official portal link to submit your online application.",
                "category": "Schemes & Applications",
                "is_active": True,
            },
            {
                "question": "How does PolicyGPT check my scheme eligibility?",
                "answer": "PolicyGPT evaluates your age, state of residence, annual family income, occupation, and social category against the scheme's verified eligibility rules in our database. It provides an itemized breakdown of matched criteria and any conditions you must meet.",
                "category": "Eligibility",
                "is_active": True,
            },
            {
                "question": "What documents are commonly required for scholarship and welfare schemes?",
                "answer": "Commonly required documents include: 1. Aadhaar Card / Identity Proof, 2. Family Income Certificate issued by competent revenue authority, 3. Domicile / Residence Certificate, 4. Bank Account Passbook linked with Aadhaar, 5. Educational Marksheets / Admission receipts (for scholarships), and 6. Landholding papers (for farmer schemes).",
                "category": "Documentation",
                "is_active": True,
            },
            {
                "question": "How do I track the status of my submitted scheme application?",
                "answer": "Log in to your PolicyGPT Citizen Portal and navigate to 'My Applications'. You can see real-time status updates (Submitted, Under Review, Approved, or Action Required) along with administrative remarks.",
                "category": "Applications",
                "is_active": True,
            },
            {
                "question": "How can I compare multiple government schemes side-by-side?",
                "answer": "Use the Scheme Comparison feature or ask the PolicyGPT Assistant (e.g. 'Compare PM Kisan and PM Awas Yojana'). It will generate a side-by-side table comparing benefits, financial assistance, eligibility, and application processes.",
                "category": "Comparison",
                "is_active": True,
            },
        ]

        for fdata in faqs_data:
            existing_faq = db.query(FAQ).filter(FAQ.question == fdata["question"]).first()
            if not existing_faq:
                faq = FAQ(**fdata)
                db.add(faq)
                logger.info(f"Created FAQ: '{faq.question}'")

        db.commit()
        logger.info("Database seeding successfully completed!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
