export type PolicyStatus = 'Draft' | 'Under Review' | 'Approved' | 'Published' | 'Archived' | 'Rejected';

export interface PolicyHistoryStep {
  status: PolicyStatus;
  label: string;
  description: string;
  date?: string;
  completed: boolean;
  current?: boolean;
}

export interface PolicyDocument {
  name: string;
  size: string; // e.g. "2.4 MB"
  type: string; // e.g. "PDF", "DOCX"
  url?: string;
  fileData?: string; // base64 or placeholder preview data
}

export interface PolicyItem {
  id: string; // e.g. "POL-001" or numeric "2"
  numericId?: number;
  name: string;
  description: string;
  ministry: string;
  department: string;
  category: string; // e.g. "Education", "Healthcare", "Agriculture", "Employment", "Finance", "Housing"
  sector: string;
  state?: string;
  publicationDate: string;
  effectiveDate: string;
  expiryDate?: string;
  tags: string[];
  document: PolicyDocument;
  status: PolicyStatus;
  updatedAt: string;
  submittedAt?: string;
  nextStep?: string;
  rejectionReason?: string;
  history?: PolicyHistoryStep[];
}

export interface PolicyCreateDto {
  title: string;
  description?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  is_active?: boolean;
  status?: string;
}

export interface PolicyUpdateDto {
  title?: string;
  description?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  status?: string;
  is_active?: boolean;
}

export interface PolicyReadDto {
  id: number;
  title: string;
  description?: string;
  category?: string;
  department?: string;
  ministry?: string;
  state?: string;
  sector?: string;
  is_active: boolean;
  status: string;
  publication_date?: string | null;
  rejection_reason?: string | null;
  created_by_id?: number | null;
  approved_by_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyPaginationResponseDto {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: PolicyReadDto[];
}

export interface PolicyApprovalActionDto {
  reason?: string;
  publish?: boolean;
}

export const INITIAL_POLICIES: PolicyItem[] = [
  {
    id: 'POL-001',
    name: 'National Education Policy 2020',
    description: 'A comprehensive framework for transforming education in India.',
    ministry: 'Ministry of Education',
    department: 'Department of School Education',
    category: 'Education',
    sector: 'Education',
    publicationDate: '05 Sep 2026',
    effectiveDate: '01 Oct 2026',
    expiryDate: '—',
    tags: ['Education', 'Students', 'Schools'],
    document: {
      name: 'National_Education_Policy_2020.pdf',
      size: '2.4 MB',
      type: 'PDF'
    },
    status: 'Published',
    updatedAt: '05 Sep 2026',
    submittedAt: '10 Sep 2026',
    nextStep: 'Awaiting approval from the designated government official',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '05 Sep 2026',
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Policy submitted for approval',
        date: '10 Sep 2026',
        completed: true
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Policy approved by Ministry committee',
        date: '12 Sep 2026',
        completed: true
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Policy published and active in national repository',
        date: '15 Sep 2026',
        completed: true,
        current: true
      }
    ]
  },
  {
    id: 'POL-002',
    name: 'PM-KISAN Policy',
    description: 'Income support scheme for all landholding farmer families across the country.',
    ministry: 'Ministry of Agriculture',
    department: 'Department of Agriculture & Farmers Welfare',
    category: 'Agriculture',
    sector: 'Agriculture & Rural Development',
    publicationDate: '04 Sep 2026',
    effectiveDate: '01 Oct 2026',
    expiryDate: '—',
    tags: ['Agriculture', 'Farmers', 'Financial Aid'],
    document: {
      name: 'PM_KISAN_Guidelines_2026.pdf',
      size: '1.8 MB',
      type: 'PDF'
    },
    status: 'Approved',
    updatedAt: '04 Sep 2026',
    submittedAt: '02 Sep 2026',
    nextStep: 'Scheduling public release',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '01 Sep 2026',
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Policy submitted for approval',
        date: '02 Sep 2026',
        completed: true
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Approved by Agricultural Committee',
        date: '04 Sep 2026',
        completed: true,
        current: true
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Not yet published',
        completed: false
      }
    ]
  },
  {
    id: 'POL-003',
    name: 'National Health Policy',
    description: 'Guidelines for universal access to good quality healthcare services without financial hardship.',
    ministry: 'Ministry of Health',
    department: 'Department of Public Health',
    category: 'Healthcare',
    sector: 'Public Health',
    publicationDate: '03 Sep 2026',
    effectiveDate: '01 Nov 2026',
    expiryDate: '—',
    tags: ['Healthcare', 'Hospitals', 'Insurance'],
    document: {
      name: 'National_Health_Policy_Framework.pdf',
      size: '3.1 MB',
      type: 'PDF'
    },
    status: 'Under Review',
    updatedAt: '03 Sep 2026',
    submittedAt: '10 Sep 2026',
    nextStep: 'Awaiting approval from the designated government official',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '05 Sep 2026',
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Policy submitted for approval',
        date: '10 Sep 2026',
        completed: false,
        current: true
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Awaiting approval',
        completed: false
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Not yet published',
        completed: false
      }
    ]
  },
  {
    id: 'POL-004',
    name: 'National Employment Policy',
    description: 'Roadmap for enhancing wage employment opportunities and skill upgrades for working youth.',
    ministry: 'Ministry of Labour',
    department: 'Department of Employment & Training',
    category: 'Employment',
    sector: 'Labour & Employment',
    publicationDate: '02 Sep 2026',
    effectiveDate: '15 Oct 2026',
    expiryDate: '—',
    tags: ['Employment', 'Youth', 'Skilling'],
    document: {
      name: 'National_Employment_Policy_Draft.docx',
      size: '1.2 MB',
      type: 'DOCX'
    },
    status: 'Draft',
    updatedAt: '02 Sep 2026',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '02 Sep 2026',
        completed: true,
        current: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Awaiting submission',
        completed: false
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Awaiting approval',
        completed: false
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Not yet published',
        completed: false
      }
    ]
  },
  {
    id: 'POL-005',
    name: 'National Housing Policy',
    description: 'Promoting affordable, sustainable, and inclusive urban housing for all socio-economic groups.',
    ministry: 'Ministry of Housing & Uraban Affairs',
    department: 'Department of Urban Housing',
    category: 'Housing',
    sector: 'Urban Infrastructure',
    publicationDate: '01 Sep 2026',
    effectiveDate: '01 Oct 2026',
    expiryDate: '—',
    tags: ['Housing', 'Urban', 'Affordable Homes'],
    document: {
      name: 'National_Housing_Policy_2026.pdf',
      size: '2.7 MB',
      type: 'PDF'
    },
    status: 'Published',
    updatedAt: '01 Sep 2026',
    submittedAt: '28 Aug 2026',
    nextStep: 'Active in national repository',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '25 Aug 2026',
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Policy submitted for approval',
        date: '28 Aug 2026',
        completed: true
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Approved by Urban Affairs Board',
        date: '30 Aug 2026',
        completed: true
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Policy published and active in national repository',
        date: '01 Sep 2026',
        completed: true,
        current: true
      }
    ]
  },
  {
    id: 'POL-006',
    name: 'Digital India Public Infrastructure Policy',
    description: 'Unified architecture for open digital public goods, data empowerment, and AI governance.',
    ministry: 'Ministry of Electronics & IT',
    department: 'Digital Governance Division',
    category: 'Finance',
    sector: 'Information Technology',
    publicationDate: '28 Aug 2026',
    effectiveDate: '15 Sep 2026',
    expiryDate: '—',
    tags: ['Digital Goods', 'Fintech', 'Identity'],
    document: {
      name: 'Digital_Public_Infrastructure_Framework.pdf',
      size: '4.2 MB',
      type: 'PDF'
    },
    status: 'Approved',
    updatedAt: '28 Aug 2026',
    submittedAt: '20 Aug 2026',
    nextStep: 'Awaiting gazette publication',
    history: [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: '15 Aug 2026',
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: 'Policy submitted for approval',
        date: '20 Aug 2026',
        completed: true
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: 'Approved by Inter-ministerial Committee',
        date: '28 Aug 2026',
        completed: true,
        current: true
      },
      {
        status: 'Published',
        label: 'Published',
        description: 'Not yet published',
        completed: false
      }
    ]
  }
];
