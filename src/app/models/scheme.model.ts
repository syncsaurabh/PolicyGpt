export type SchemeStatus = 'Active' | 'Draft' | 'Under Review' | 'Closed' | 'Archived';

export type SchemeCategory =
  | 'Scholarships'
  | 'Farmer Welfare'
  | 'Healthcare'
  | 'Housing'
  | 'Business Support'
  | 'Women Empowerment'
  | 'Senior Citizen Welfare'
  | 'Student Schemes'
  | 'Employment Programs'
  | 'Social Security';

export interface SchemeItem {
  id: string; // e.g. "SCH-001" or numeric "1"
  numericId?: number;
  name: string;
  description: string;
  category: SchemeCategory;
  ministry: string;
  department: string;
  state: string; // e.g. "Central / All India", "Maharashtra", etc.
  sector?: string;
  targetAudience?: string;
  benefits: string;
  eligibilityCriteria: string;
  applicationProcess: string;
  applicationUrl: string;
  startDate: string;
  endDate: string;
  status: SchemeStatus;
  updatedAt: string;
  createdAt?: string;
  policyId?: number;
  tags?: string[];
}

export interface EligibilityRuleDto {
  id?: number;
  scheme_id?: number;
  rule_name: string;
  criteria_json?: string;
  description?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SchemeCreateDto {
  name: string;
  description?: string;
  benefits?: string;
  target_audience?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  application_process?: string;
  policy_id?: number;
  is_active?: boolean;
  status?: string;
  eligibility_rules?: EligibilityRuleDto[];
}

export interface SchemeUpdateDto {
  name?: string;
  description?: string;
  benefits?: string;
  target_audience?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  application_process?: string;
  policy_id?: number;
  status?: string;
  is_active?: boolean;
}

export interface SchemeReadDto {
  id: number;
  name: string;
  description?: string;
  benefits?: string;
  target_audience?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  application_process?: string;
  policy_id?: number | null;
  is_active: boolean;
  status: string;
  publication_date?: string | null;
  created_by_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface SchemeDetailReadDto extends SchemeReadDto {
  eligibility_rules: EligibilityRuleDto[];
}

export interface SchemePaginationResponseDto {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: SchemeReadDto[];
}

export interface EligibilityCheckRequest {
  age?: number | null;
  gender?: string | null;
  income?: number | null;
  occupation?: string | null;
  education?: string | null;
  location?: string | null;
  social_category?: string | null;
  disability_status?: boolean | null;
}

export interface SchemeEligibilityResult {
  scheme_id: number;
  scheme_name: string;
  eligible: boolean;
  matched_rules?: string[];
  failed_rules?: string[];
  category?: string | null;
  benefits?: string | null;
  department?: string | null;
  application_guidance?: string | null;
  match_percentage?: number;
}

export interface EligibilityCheckResponse {
  eligible_schemes: SchemeEligibilityResult[];
  total_matches: number;
}


export const SCHEME_CATEGORIES: SchemeCategory[] = [
  'Scholarships',
  'Farmer Welfare',
  'Healthcare',
  'Housing',
  'Business Support',
  'Women Empowerment',
  'Senior Citizen Welfare',
  'Student Schemes',
  'Employment Programs',
  'Social Security'
];

export const SCHEME_STATES: string[] = [
  'Central / All India',
  'Andhra Pradesh',
  'Assam',
  'Bihar',
  'Delhi (NCT)',
  'Gujarat',
  'Haryana',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Tamil Nadu',
  'Telangana',
  'Uttar Pradesh',
  'West Bengal'
];

export const INITIAL_SCHEMES: SchemeItem[] = [
  {
    id: 'SCH-001',
    name: 'PM Kisan Samman Nidhi (PM-KISAN)',
    description: 'Direct income support of ₹6,000 per year in three equal installments to all landholding farmer families across the country.',
    category: 'Farmer Welfare',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    state: 'Central / All India',
    benefits: 'Direct financial benefit of ₹6,000 annually deposited straight into the verified Aadhaar-linked bank accounts of beneficiary farmers.',
    eligibilityCriteria: 'All small and marginal landholding farmer families with cultivable landholding in their names. Institutional landholders and income tax paying individuals are excluded.',
    applicationProcess: 'Farmers can register through the PM-KISAN portal, mobile app, or via Common Service Centres (CSCs). Aadhaar authentication and land records are required.',
    applicationUrl: 'https://pmkisan.gov.in',
    startDate: '01 Dec 2018',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '10 Sep 2026',
    createdAt: '01 Jan 2024',
    tags: ['Farmers', 'Income Support', 'Direct Benefit Transfer', 'Agriculture']
  },
  {
    id: 'SCH-002',
    name: 'Ayushman Bharat - PM Jan Arogya Yojana (AB-PMJAY)',
    description: 'Flagship health insurance scheme providing health cover up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.',
    category: 'Healthcare',
    ministry: 'Ministry of Health & Family Welfare',
    department: 'National Health Authority',
    state: 'Central / All India',
    benefits: 'Cashless and paperless access to services for the beneficiary at both public and empanelled private hospitals up to ₹5,00,000 per family annually.',
    eligibilityCriteria: 'Households identified under rural and urban deprivation criteria of the Socio-Economic and Caste Census (SECC 2011), plus all senior citizens aged 70 and above irrespective of income.',
    applicationProcess: 'Eligible citizens can generate their Ayushman Card (Golden Card) at empanelled healthcare facilities, CSCs, or through the PMJAY mobile app using Aadhaar verification.',
    applicationUrl: 'https://pmjay.gov.in',
    startDate: '23 Sep 2018',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '08 Sep 2026',
    createdAt: '01 Jan 2024',
    tags: ['Healthcare', 'Insurance', 'Hospitalization', 'Cashless Care']
  },
  {
    id: 'SCH-003',
    name: 'Pradhan Mantri Awas Yojana - Urban 2.0 (PMAY-U)',
    description: 'Housing mission aimed at providing all-weather pucca houses to all eligible urban households including slum dwellers and low-income families.',
    category: 'Housing',
    ministry: 'Ministry of Housing & Urban Affairs',
    department: 'Urban Housing Mission Division',
    state: 'Central / All India',
    benefits: 'Subsidies up to ₹2.5 lakh for construction or purchase of homes, and interest subsidies up to ₹1.8 lakh on home loans under the Credit Linked Subsidy Scheme (CLSS).',
    eligibilityCriteria: 'Economically Weaker Section (EWS) with annual income up to ₹3 lakh, Lower Income Group (LIG) up to ₹6 lakh, and Middle Income Groups (MIG) without an existing pucca house.',
    applicationProcess: 'Apply online through PMAY urban portal or nearest municipal corporation/urban local body office with identity proof, income certificate, and land ownership/affidavit.',
    applicationUrl: 'https://pmay-urban.gov.in',
    startDate: '25 Jun 2015',
    endDate: '31 Dec 2028',
    status: 'Active',
    updatedAt: '05 Sep 2026',
    createdAt: '15 Feb 2024',
    tags: ['Housing', 'Urban Development', 'Affordable Homes', 'Subsidies']
  },
  {
    id: 'SCH-004',
    name: 'National Merit-cum-Means Scholarship Scheme (NMMSS)',
    description: 'Awarding scholarships to meritorious students of economically weaker sections to arrest dropout rate at class 8 and encourage secondary stage study.',
    category: 'Scholarships',
    ministry: 'Ministry of Education',
    department: 'Department of School Education & Literacy',
    state: 'Central / All India',
    benefits: '₹12,000 per annum (₹1,000 per month) from Class 9 to Class 12 for students studying in State Government, Government-aided and Local body schools.',
    eligibilityCriteria: 'Students having parental annual income not exceeding ₹3,50,000 and who have secured at least 55% marks or equivalent in class 7 exam. Must pass selection test conducted by States/UTs.',
    applicationProcess: 'Applications must be submitted online on the National Scholarship Portal (NSP) accompanied by school verification and income certificates.',
    applicationUrl: 'https://scholarships.gov.in',
    startDate: '01 May 2024',
    endDate: '31 Mar 2027',
    status: 'Active',
    updatedAt: '04 Sep 2026',
    createdAt: '01 May 2024',
    tags: ['Scholarships', 'Students', 'Secondary Education', 'Merit']
  },
  {
    id: 'SCH-005',
    name: 'Pradhan Mantri Mudra Yojana (PMMY)',
    description: 'Loans up to ₹20 lakh to non-corporate, non-farm small/micro enterprises to encourage entrepreneurship and business growth.',
    category: 'Business Support',
    ministry: 'Ministry of Finance',
    department: 'Department of Financial Services',
    state: 'Central / All India',
    benefits: 'Collateral-free institutional loans categorized into Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 lakh), Tarun (₹5 lakh to ₹10 lakh), and Tarun Plus (up to ₹20 lakh).',
    eligibilityCriteria: 'Any Indian citizen having a business plan for a non-farm sector income-generating activity such as manufacturing, processing, trading, or service sector.',
    applicationProcess: 'Apply online through Udyamimitra portal or visit any Commercial Bank, Regional Rural Bank (RRB), or Micro Finance Institution (MFI) with business plan and KYC documents.',
    applicationUrl: 'https://www.mudra.org.in',
    startDate: '08 Apr 2015',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '01 Sep 2026',
    createdAt: '10 Jan 2024',
    tags: ['Business', 'MSME', 'Microfinance', 'Entrepreneurship', 'Credit']
  },
  {
    id: 'SCH-006',
    name: 'Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS)',
    description: 'Guarantees at least 100 days of wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.',
    category: 'Employment Programs',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    state: 'Central / All India',
    benefits: 'Statutory minimum wage compensation for 100 days of guaranteed work, unemployment allowance if work is not allocated within 15 days of application.',
    eligibilityCriteria: 'Adult members of any rural household residing in the Gram Panchayat area willing to perform manual and unskilled labor.',
    applicationProcess: 'Apply for a Job Card at the local Gram Panchayat office. Work application is submitted specifying the duration for which work is sought.',
    applicationUrl: 'https://nrega.nic.in',
    startDate: '02 Feb 2006',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '28 Aug 2026',
    createdAt: '01 Jan 2024',
    tags: ['Employment', 'Rural Development', 'Wages', 'Job Card']
  },
  {
    id: 'SCH-007',
    name: 'Sukanya Samriddhi Yojana (SSY)',
    description: 'Small savings deposit scheme aimed exclusively for the welfare and higher education of the girl child with attractive tax-free interest rates.',
    category: 'Women Empowerment',
    ministry: 'Ministry of Women and Child Development',
    department: 'Department of Economic Affairs',
    state: 'Central / All India',
    benefits: 'High government-backed interest rate (currently 8.2% p.a.), Section 80C income tax deduction, and complete tax exemption on accrued interest and maturity proceeds.',
    eligibilityCriteria: 'Parents or legal guardians of a girl child can open an account in the name of the girl from birth until she attains the age of 10 years. Maximum 2 accounts per family.',
    applicationProcess: 'Submit the account opening form along with birth certificate of girl child and KYC documents of guardian at any authorized Post Office or commercial bank branch.',
    applicationUrl: 'https://www.nsiindia.gov.in',
    startDate: '22 Jan 2015',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '25 Aug 2026',
    createdAt: '15 Jan 2024',
    tags: ['Women', 'Girl Child', 'Savings', 'Tax Benefit', 'Education']
  },
  {
    id: 'SCH-008',
    name: 'Pradhan Mantri Vaya Vandana Yojana (PMVVY)',
    description: 'Pension scheme providing social security and guaranteed pension return to senior citizens aged 60 years and above against uncertain market conditions.',
    category: 'Senior Citizen Welfare',
    ministry: 'Ministry of Finance',
    department: 'Department of Financial Services',
    state: 'Central / All India',
    benefits: 'Guaranteed pension payable monthly, quarterly, half-yearly, or annually for 10 years with return of purchase price upon survival of the pensioner.',
    eligibilityCriteria: 'Indian citizens who have completed 60 years of age. Maximum investment limit is ₹15 lakh per senior citizen.',
    applicationProcess: 'Subscription can be purchased both online and offline through Life Insurance Corporation of India (LIC), which is the sole authorized operator.',
    applicationUrl: 'https://licindia.in',
    startDate: '04 May 2017',
    endDate: '31 Mar 2027',
    status: 'Active',
    updatedAt: '20 Aug 2026',
    createdAt: '01 Feb 2024',
    tags: ['Senior Citizens', 'Pension', 'Retirement', 'Social Security']
  },
  {
    id: 'SCH-009',
    name: 'Atal Pension Yojana (APY)',
    description: 'Universal social security pension scheme aimed primarily at the unorganized sector workers with fixed monthly pension options upon attaining 60 years.',
    category: 'Social Security',
    ministry: 'Ministry of Finance',
    department: 'Pension Fund Regulatory and Development Authority (PFRDA)',
    state: 'Central / All India',
    benefits: 'Guaranteed monthly pension ranging from ₹1,000 to ₹5,000 depending on subscriber contributions and age at entry. Pension continues to spouse after subscriber demise.',
    eligibilityCriteria: 'All bank or post office savings account holders between the ages of 18 and 40 years. Subscriber must not be an income tax payer as of current rules.',
    applicationProcess: 'Fill out APY registration form via net banking, mobile banking app, or submit physical form to the branch where savings account is maintained.',
    applicationUrl: 'https://www.npscra.nsdl.co.in',
    startDate: '09 May 2015',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '15 Aug 2026',
    createdAt: '01 Jan 2024',
    tags: ['Pension', 'Social Security', 'Unorganized Sector', 'Retirement']
  },
  {
    id: 'SCH-010',
    name: 'PM SVANidhi (Micro-Credit for Street Vendors)',
    description: 'Special micro-credit facility empowering urban, peri-urban and rural street vendors with working capital loans to resume and expand livelihoods.',
    category: 'Business Support',
    ministry: 'Ministry of Housing & Urban Affairs',
    department: 'Urban Livelihoods Division',
    state: 'Central / All India',
    benefits: 'First tranche working capital loan up to ₹10,000, subsequent tranches of ₹20,000 and ₹50,000 on timely repayment with 7% interest subsidy and cashback on digital transactions.',
    eligibilityCriteria: 'Street vendors vending in urban areas possessing a Certificate of Vending / ID card issued by Urban Local Bodies (ULBs) or Recommendation Letter.',
    applicationProcess: 'Apply online through PMSVANidhi mobile app or portal with Aadhaar, mobile number, and ULB vendor identification.',
    applicationUrl: 'https://pmsvanidhi.mohua.gov.in',
    startDate: '01 Jun 2020',
    endDate: '31 Dec 2026',
    status: 'Active',
    updatedAt: '12 Aug 2026',
    createdAt: '01 Jun 2024',
    tags: ['Street Vendors', 'Microcredit', 'Interest Subsidy', 'Digital Payments']
  },
  {
    id: 'SCH-011',
    name: 'Maharashtra Mahatma Jyotirao Phule Jan Arogya Yojana',
    description: 'State health insurance scheme providing comprehensive financial health coverage for catastrophic illnesses to families holding ration cards.',
    category: 'Healthcare',
    ministry: 'Ministry of Health & Family Welfare',
    department: 'Public Health Department, Government of Maharashtra',
    state: 'Maharashtra',
    benefits: 'Free medical care up to ₹5 lakh per family per year for over 1,350 medical and surgical therapies across government and private network hospitals in Maharashtra.',
    eligibilityCriteria: 'Residents of Maharashtra possessing Yellow, Orange, or Antyodaya ration cards, Annapurna cards, or farmer families from distress districts.',
    applicationProcess: 'Show valid ration card and photo identity to the Arogyamitra at any network hospital reception for immediate treatment pre-authorization.',
    applicationUrl: 'https://www.jeevandayee.gov.in',
    startDate: '02 Jul 2012',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '10 Aug 2026',
    createdAt: '15 Feb 2024',
    tags: ['Maharashtra', 'Healthcare', 'Cashless Hospitalization', 'State Scheme']
  },
  {
    id: 'SCH-012',
    name: 'Karnataka Yuva Nidhi Scheme',
    description: 'Direct monthly unemployment allowance to educated youth residing in Karnataka who remain unemployed after obtaining degree or diploma certificates.',
    category: 'Employment Programs',
    ministry: 'Ministry of Labour',
    department: 'Department of Skill Development & Livelihood, Karnataka',
    state: 'Karnataka',
    benefits: '₹3,000 per month for unemployed graduates and ₹1,500 per month for unemployed diploma holders for up to 2 years or until employment is secured.',
    eligibilityCriteria: 'Youth domiciled in Karnataka who passed degree/diploma in the academic year and have not secured employment or self-employment after 6 months of graduation.',
    applicationProcess: 'Apply online through Seva Sindhu portal using Aadhaar, graduation certificate verification, and bank account seeding.',
    applicationUrl: 'https://sevasindhu.karnataka.gov.in',
    startDate: '01 Jan 2024',
    endDate: '31 Dec 2027',
    status: 'Active',
    updatedAt: '05 Aug 2026',
    createdAt: '01 Jan 2024',
    tags: ['Karnataka', 'Youth', 'Unemployment Allowance', 'Graduates']
  },
  {
    id: 'SCH-013',
    name: 'Kanya Sumangala Yojana',
    description: 'Conditional cash transfer scheme in Uttar Pradesh aimed at girl child welfare across education stages from birth to graduation.',
    category: 'Women Empowerment',
    ministry: 'Ministry of Women and Child Development',
    department: 'Department of Women & Child Welfare, Uttar Pradesh',
    state: 'Uttar Pradesh',
    benefits: 'Total assistance of ₹25,000 disbursed across 6 stages from birth, complete immunization, school enrollment in Class 1, 6, 9, and admission into degree/diploma.',
    eligibilityCriteria: 'Resident families of Uttar Pradesh with maximum two daughters and total family annual income not exceeding ₹3,00,000.',
    applicationProcess: 'Online application at MKSY official state portal with birth certificate, immunization proof, student admission receipts, and income certificate.',
    applicationUrl: 'https://mksy.up.gov.in',
    startDate: '01 Apr 2019',
    endDate: 'Ongoing',
    status: 'Under Review',
    updatedAt: '25 Jul 2026',
    createdAt: '10 Mar 2024',
    tags: ['Uttar Pradesh', 'Girl Child', 'Education Incentive', 'State Welfare']
  },
  {
    id: 'SCH-014',
    name: 'Central Sector Scheme of Scholarships for College & University Students',
    description: 'Scholarship scheme providing financial support to meritorious students from low-income families to meet regular day-to-day expenses while pursuing higher studies.',
    category: 'Student Schemes',
    ministry: 'Ministry of Education',
    department: 'Department of Higher Education',
    state: 'Central / All India',
    benefits: '₹12,000 per annum at graduation level for first 3 years and ₹20,000 per annum at post-graduation level disbursed directly to recipient bank accounts.',
    eligibilityCriteria: 'Students scoring above 80th percentile in relevant stream in Class 12 board exams, pursuing regular university degrees, with parental income under ₹4.5 lakh/year.',
    applicationProcess: 'Apply annually through National Scholarship Portal (NSP) with college admission verification, marksheets, and parental income affidavit.',
    applicationUrl: 'https://scholarships.gov.in',
    startDate: '15 Jul 2024',
    endDate: '31 Oct 2026',
    status: 'Draft',
    updatedAt: '18 Jul 2026',
    createdAt: '15 Jul 2024',
    tags: ['Higher Education', 'College', 'University', 'Merit Scholarship']
  },
  {
    id: 'SCH-015',
    name: 'Pradhan Mantri Matru Vandana Yojana (PMMVY)',
    description: 'Maternity benefit program providing cash incentives for pregnant women and lactating mothers for health seeking behavior and nutritional support.',
    category: 'Women Empowerment',
    ministry: 'Ministry of Women and Child Development',
    department: 'Department of Women & Child Development',
    state: 'Central / All India',
    benefits: '₹5,000 in two installments for first child and ₹6,000 for second girl child paid into bank account upon early registration, ANC checkups, and child immunization.',
    eligibilityCriteria: 'Pregnant women and lactating mothers who are not regular government or PSU employees and belong to socially and economically disadvantaged groups.',
    applicationProcess: 'Register at nearest Anganwadi Centre (AWC) or approved health facility, or apply directly on PMMVY portal using Mother and Child Protection (MCP) card.',
    applicationUrl: 'https://pmmvy.wcd.gov.in',
    startDate: '01 Jan 2017',
    endDate: 'Ongoing',
    status: 'Active',
    updatedAt: '10 Jul 2026',
    createdAt: '01 Jan 2024',
    tags: ['Maternity', 'Nutrition', 'Mother & Child', 'Cash Transfer']
  }
];
