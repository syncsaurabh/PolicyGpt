/**
 * Feedback & Support Models matching Backend Swagger/OpenAPI Specifications.
 */

export enum FeedbackType {
  FEEDBACK = 'FEEDBACK',
  ISSUE = 'ISSUE',
  SUPPORT = 'SUPPORT',
  INQUIRY = 'INQUIRY',
  SUGGESTION = 'SUGGESTION',
  COMPLAINT = 'COMPLAINT',
}

export enum FeedbackPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  URGENT = 'URGENT',
}

export enum FeedbackStatus {
  OPEN = 'OPEN',
  SUBMITTED = 'SUBMITTED',
  IN_PROGRESS = 'IN_PROGRESS',
  IN_REVIEW = 'IN_REVIEW',
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED',
}

/**
 * Payload for POST /api/v1/feedback
 */
export interface FeedbackCreate {
  subject: string;
  content: string;
  description?: string | null;
  feedback_type?: FeedbackType | null;
  type?: FeedbackType | null;
  category?: string | null;
  reference_id?: string | null;
  application_id?: string | null;
  rating?: number | null;
  priority?: FeedbackPriority;
}

/**
 * Single Feedback/Support Ticket Schema (GET /api/v1/feedback/{id} & in list results)
 */
export interface FeedbackRead {
  id: number;
  user_id?: number | null;
  user_name?: string | null;
  user_email?: string | null;
  feedback_type: string;
  type?: string | null;
  category?: string | null;
  subject: string;
  content: string;
  description?: string | null;
  rating?: number | null;
  status: string;
  priority: string;
  admin_response?: string | null;
  resolution?: string | null;
  resolved_by_id?: number | null;
  resolver_name?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Paginated Response for feedback list
 */
export interface FeedbackPaginationResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: FeedbackRead[];
}

/**
 * Single History/Audit Event for a ticket
 */
export interface FeedbackHistoryItem {
  id: number;
  action: string;
  details?: string | null;
  user_id?: number | null;
  created_at: string;
}

/**
 * Response for GET /api/v1/feedback/{id}/history
 */
export interface FeedbackHistoryResponse {
  feedback_id: number;
  total_events: number;
  history: FeedbackHistoryItem[];
}

/**
 * Query filters for GET /api/v1/feedback/my
 */
export interface MyFeedbackListParams {
  page?: number;
  page_size?: number;
  status?: string;
  feedback_type?: string;
  priority?: string;
  category?: string;
}

/**
 * Admin update triage payload: PUT /api/v1/feedback/{id}/status
 */
export interface FeedbackUpdate {
  status?: FeedbackStatus | null;
  priority?: FeedbackPriority | null;
  category?: string | null;
  admin_response?: string | null;
  resolution?: string | null;
}

/**
 * Admin resolve ticket payload: POST /api/v1/feedback/{id}/resolve
 */
export interface FeedbackResolve {
  admin_response?: string | null;
  resolution?: string | null;
  status?: FeedbackStatus;
}

/**
 * Query filters for Admin list: GET /api/v1/feedback
 */
export interface AdminFeedbackListParams extends MyFeedbackListParams {
  user_id?: number;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_order?: string;
}
