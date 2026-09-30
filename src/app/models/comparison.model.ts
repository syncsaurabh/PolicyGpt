/**
 * Comparison Data Models aligning with FastAPI backend schemas and UI requirements.
 */

export interface ComparisonItem {
  id: number;
  name: string;
  type?: 'Policy' | 'Scheme' | 'policy' | 'scheme';
  code?: string;
  category?: string | null;
  ministry?: string | null;
  department?: string | null;
  state?: string | null;
  sector?: string | null;
  status?: string | null;
  description?: string | null;
  benefits?: string | string[] | null;
  eligibility?: string | string[] | null;
  target_audience?: string | null;
  application_process?: string | null;
  documents_required?: string | string[] | null;
}

export interface ComparisonRequest {
  scheme_ids?: (number | string)[];
  policy_ids?: (number | string)[];
}

export interface ComparisonResponse {
  comparison_type: 'scheme' | 'policy' | 'mixed' | string;
  items: ComparisonItem[];
}

export interface SelectableCompareItem {
  id: number;
  code: string;
  name: string;
  type: 'Policy' | 'Scheme';
  category: string;
  ministry: string;
  department: string;
  description: string;
  state: string;
  target_audience: string;
  status: string;
  benefits: string;
  eligibility: string;
  application_process: string;
  documents_required: string;
}
