/**
 * Reports Models matching Backend Swagger/OpenAPI Specifications.
 */

export interface ReportRead {
  id: number;
  generated_by?: number | null;
  title: string;
  report_type: string;
  file_format?: string | null;
  file_path?: string | null;
  parameters_json?: string | null;
  status: string;
  record_count: number;
  metadata_json?: string | null;
  created_at: string;
}

export interface ReportPaginationResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: ReportRead[];
}

export interface ReportDataResponse<T = Record<string, any>> {
  report_title: string;
  report_type: string;
  generated_at: string;
  record_count: number;
  filters: Record<string, any>;
  data: T[];
}

export interface ReportHistoryParams {
  page?: number;
  page_size?: number;
  report_type?: string;
}

export interface PolicyReportParams {
  start_date?: string;
  end_date?: string;
  department?: string;
  category?: string;
  state?: string;
  status_filter?: string;
}

export interface SchemeReportParams {
  start_date?: string;
  end_date?: string;
  department?: string;
  category?: string;
  state?: string;
  status_filter?: string;
}

export interface DepartmentReportParams {
  department?: string;
}

export interface UserActivityReportParams {
  start_date?: string;
  end_date?: string;
  event_type?: string;
}

export type ExportFormat = 'pdf' | 'excel' | 'xlsx';
