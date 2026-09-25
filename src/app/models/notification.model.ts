/**
 * Notification models and TypeScript schemas aligned with FastAPI backend.
 */

export enum NotificationType {
  NEW_POLICY = 'NEW_POLICY',
  POLICY_CREATED = 'POLICY_CREATED',
  POLICY_UPDATED = 'POLICY_UPDATED',
  POLICY_APPROVED = 'POLICY_APPROVED',
  POLICY_REJECTED = 'POLICY_REJECTED',
  NEW_SCHEME = 'NEW_SCHEME',
  SCHEME_CREATED = 'SCHEME_CREATED',
  SCHEME_UPDATED = 'SCHEME_UPDATED',
  SCHEME_UPDATE = 'SCHEME_UPDATE',
  SCHEME_DEADLINE = 'SCHEME_DEADLINE',
  DEADLINE_REMINDER = 'DEADLINE_REMINDER',
  APPLICATION_SUBMITTED = 'APPLICATION_SUBMITTED',
  APPLICATION_STATUS_CHANGED = 'APPLICATION_STATUS_CHANGED',
  APPLICATION_APPROVED = 'APPLICATION_APPROVED',
  APPLICATION_REJECTED = 'APPLICATION_REJECTED',
  APPLICATION_UPDATE = 'APPLICATION_UPDATE',
  APPLICATION_UPDATED = 'APPLICATION_UPDATED',
  ELIGIBILITY_MATCH = 'ELIGIBILITY_MATCH',
  SYSTEM_ANNOUNCEMENT = 'SYSTEM_ANNOUNCEMENT',
  SYSTEM_ALERT = 'SYSTEM_ALERT',
  FEEDBACK_RESPONSE = 'FEEDBACK_RESPONSE',
  GENERAL = 'GENERAL'
}

export enum NotificationChannel {
  IN_APP = 'IN_APP',
  EMAIL = 'EMAIL',
  SMS = 'SMS',
  PUSH = 'PUSH'
}

export enum NotificationStatus {
  PENDING = 'PENDING',
  SENT = 'SENT',
  DELIVERED = 'DELIVERED',
  FAILED = 'FAILED',
  READ = 'READ'
}

export interface NotificationRead {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: string;
  channel: string;
  status: string;
  entity_type?: string | null;
  entity_id?: string | null;
  is_read: boolean;
  read_at?: string | null;
  scheduled_at?: string | null;
  sent_at?: string | null;
  created_at: string;
}

export interface NotificationPaginationResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  unread_count: number;
  results: NotificationRead[];
}

export interface AdminNotificationPaginationResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: NotificationRead[];
}

export interface NotificationUnreadCountResponse {
  unread_count: number;
}

export interface NotificationPreferenceRead {
  id: number;
  user_id: number;
  email_enabled: boolean;
  sms_enabled: boolean;
  in_app_enabled: boolean;
  policy_alerts: boolean;
  scheme_updates: boolean;
  deadline_reminders: boolean;
  application_updates: boolean;
  system_alerts: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferenceUpdate {
  email_enabled?: boolean;
  sms_enabled?: boolean;
  in_app_enabled?: boolean;
  policy_alerts?: boolean;
  scheme_updates?: boolean;
  deadline_reminders?: boolean;
  application_updates?: boolean;
  system_alerts?: boolean;
}

export interface NotificationCreate {
  user_id: number;
  title: string;
  message: string;
  notification_type?: NotificationType | string;
  channel?: NotificationChannel | string;
  entity_type?: string | null;
  entity_id?: string | null;
  scheduled_at?: string | null;
}

export interface NotificationBroadcast {
  title: string;
  message: string;
  notification_type?: NotificationType | string;
  channel?: NotificationChannel | string;
  target_roles?: string[] | null;
}

export interface NotificationListParams {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
  notification_type?: string;
  channel?: string;
}

export interface AdminNotificationListParams {
  page?: number;
  page_size?: number;
  user_id?: number;
  status_filter?: string;
  notification_type?: string;
  channel?: string;
}

export interface MessageResponse {
  message: string;
}
