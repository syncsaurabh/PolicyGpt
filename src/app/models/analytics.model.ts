export interface DistributionItem {
  name: string;
  count: number;
}

export interface OverviewAnalyticsResponse {
  total_policies: number;
  published_policies: number;
  total_schemes: number;
  active_schemes: number;
  total_users: number;
  total_searches: number;
  total_notifications: number;
  unread_notifications: number;
  policy_category_distribution: DistributionItem[];
  scheme_category_distribution: DistributionItem[];
  department_distribution: DistributionItem[];
  user_role_distribution: DistributionItem[];
}

export interface PolicyAnalytics {
  total_policies: number;
  published_count: number;
  draft_count: number;
  pending_approval_count: number;
  approved_count: number;
  rejected_count: number;
  archived_count: number;
  by_category: DistributionItem[];
  by_department: DistributionItem[];
  by_state: DistributionItem[];
}

export interface SchemeAnalytics {
  total_schemes: number;
  active_count: number;
  inactive_count: number;
  draft_count: number;
  archived_count: number;
  published_count: number;
  by_category: DistributionItem[];
  by_department: DistributionItem[];
  by_state: DistributionItem[];
}

export interface UserAnalytics {
  total_users: number;
  active_users: number;
  inactive_users: number;
  by_role: DistributionItem[];
  recent_registrations_30d: number;
}

export interface DepartmentAnalyticsItem {
  department: string;
  policy_count: number;
  scheme_count: number;
  published_policies: number;
  active_schemes: number;
  activity_count: number;
}

export interface DepartmentAnalyticsResponse {
  total_departments: number;
  departments: DepartmentAnalyticsItem[];
}

export interface SearchAnalytics {
  total_searches: number;
  unique_users_count: number;
  popular_queries: DistributionItem[];
  zero_result_searches: number;
}

export interface NotificationAnalytics {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  by_type: DistributionItem[];
  by_channel: DistributionItem[];
}

export interface UsageStatisticsResponse {
  total_activities: number;
  activities_by_event_type: DistributionItem[];
  total_searches: number;
  total_eligibility_checks: number;
  total_feedbacks: number;
  total_reports_generated: number;
  popular_resources: DistributionItem[];
  recent_activities: Record<string, any>[];
}
