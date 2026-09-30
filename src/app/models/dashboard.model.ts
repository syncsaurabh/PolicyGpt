import {
  DepartmentAnalyticsItem,
  DistributionItem,
  NotificationAnalytics,
  OverviewAnalyticsResponse,
  PolicyAnalytics,
  SchemeAnalytics,
  UsageStatisticsResponse,
  UserAnalytics
} from './analytics.model';

export interface SavedPolicyItem {
  id: number;
  policy_id?: number | null;
  scheme_id?: number | null;
  item_type?: 'policy' | 'scheme' | string;
  title: string;
  category?: string | null;
  department?: string | null;
  ministry?: string | null;
  state?: string | null;
  sector?: string | null;
  status: string;
  saved_at: string;
  notes?: string | null;
}

export interface SavedPolicyCreate {
  policy_id?: number | null;
  scheme_id?: number | null;
  notes?: string | null;
}

export interface SchemeEligibilityResult {
  scheme_id: number;
  scheme_name: string;
  eligible: boolean;
  matched_rules: string[];
  failed_rules: string[];
  category?: string | null;
  benefits?: string | null;
  department?: string | null;
  application_guidance?: string | null;
}

export interface CitizenNotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  channel: string;
  status: string;
  is_read: boolean;
  created_at: string;
  entity_type?: string | null;
  entity_id?: string | null;
}

export interface CitizenSearchHistoryItem {
  id: number;
  query: string;
  filters_json?: string | null;
  result_count: number;
  created_at: string;
}

export interface ApplicationStatusItem {
  id: number;
  scheme_id: number;
  scheme_name: string;
  application_number: string;
  status: string;
  details_json?: string | null;
  remarks?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SchemeApplicationCreate {
  scheme_id: number;
  details_json?: string | null;
  remarks?: string | null;
}

export interface CitizenDashboardResponse {
  saved_policies?: SavedPolicyItem[];
  eligible_schemes?: SchemeEligibilityResult[];
  recent_notifications?: CitizenNotificationItem[];
  search_history?: CitizenSearchHistoryItem[];
  application_status?: ApplicationStatusItem[];
}

export interface GovernmentDashboardResponse {
  policy_statistics: PolicyAnalytics;
  scheme_usage: SchemeAnalytics;
  user_activity: UsageStatisticsResponse;
  department_reports?: DepartmentAnalyticsItem[];
  notification_statistics: NotificationAnalytics;
}

export interface AdminReportsSummary {
  total_reports_generated?: number;
  recent_reports?: Record<string, any>[];
}

export interface AuditLogItem {
  id: number;
  user_id?: number | null;
  user_email?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  details?: string | null;
  ip_address?: string | null;
  created_at: string;
}

export interface AdminDashboardResponse {
  user_management: UserAnalytics;
  policy_management: PolicyAnalytics;
  analytics: OverviewAnalyticsResponse;
  reports: AdminReportsSummary;
  audit_logs?: AuditLogItem[];
}
