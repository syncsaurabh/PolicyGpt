export type ApplicationStatus =
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'DISBURSED'
  | 'WITHDRAWN';

export interface ApplicantSummary {
  id: number;
  name: string;
  email: string;
  phone_number?: string | null;
  state?: string | null;
  age?: number | null;
  role?: string | null;
}

export interface SchemeSummary {
  id: number;
  name: string;
  category?: string | null;
  department?: string | null;
  ministry?: string | null;
  state?: string | null;
  sector?: string | null;
  benefits?: string | null;
}

export interface ApplicationCreateDto {
  scheme_id: number;
  details_json?: string | null;
  remarks?: string | null;
}

export interface ApplicationStatusUpdateDto {
  status: ApplicationStatus;
  remarks?: string | null;
  rejection_reason?: string | null;
}

export interface ApplicationWithdrawDto {
  reason?: string | null;
}

export interface ApplicationReadDto {
  id: number;
  application_number: string;
  user_id: number;
  scheme_id: number;
  scheme_name: string;
  status: ApplicationStatus | string;
  details_json?: string | null;
  remarks?: string | null;
  reviewed_by_id?: number | null;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
  scheme?: SchemeSummary | null;
  applicant?: ApplicantSummary | null;
}

export interface ApplicationPaginationResponseDto {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: ApplicationReadDto[];
}
