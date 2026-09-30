import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AdminFeedbackListParams,
  FeedbackCreate,
  FeedbackHistoryResponse,
  FeedbackPaginationResponse,
  FeedbackRead,
  FeedbackResolve,
  FeedbackUpdate,
  MyFeedbackListParams,
} from '../../models/feedback.model';

@Injectable({
  providedIn: 'root',
})
export class FeedbackService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/feedback`;

  /**
   * Submit citizen feedback, issue report, or support request.
   * POST /api/v1/feedback
   */
  submitFeedback(payload: FeedbackCreate): Observable<FeedbackRead> {
    return this.http.post<FeedbackRead>(this.baseUrl, payload);
  }

  /**
   * List feedback and support tickets submitted by current authenticated user.
   * GET /api/v1/feedback/my
   */
  getMyFeedback(params?: MyFeedbackListParams): Observable<FeedbackPaginationResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.status && params.status !== 'ALL') httpParams = httpParams.set('status', params.status);
      if (params.feedback_type && params.feedback_type !== 'ALL') {
        httpParams = httpParams.set('feedback_type', params.feedback_type);
      }
      if (params.priority && params.priority !== 'ALL') httpParams = httpParams.set('priority', params.priority);
      if (params.category && params.category.trim() !== '') {
        httpParams = httpParams.set('category', params.category.trim());
      }
    }

    return this.http.get<FeedbackPaginationResponse>(`${this.baseUrl}/my`, { params: httpParams });
  }

  /**
   * List and filter all feedback and support tickets across the platform (Admin / Official).
   * GET /api/v1/feedback
   */
  getAllFeedback(params?: AdminFeedbackListParams): Observable<FeedbackPaginationResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.status && params.status !== 'ALL') httpParams = httpParams.set('status', params.status);
      if (params.feedback_type && params.feedback_type !== 'ALL') {
        httpParams = httpParams.set('feedback_type', params.feedback_type);
      }
      if (params.priority && params.priority !== 'ALL') httpParams = httpParams.set('priority', params.priority);
      if (params.category && params.category.trim() !== '') {
        httpParams = httpParams.set('category', params.category.trim());
      }
      if (params.user_id !== undefined) httpParams = httpParams.set('user_id', params.user_id.toString());
      if (params.start_date) httpParams = httpParams.set('start_date', params.start_date);
      if (params.end_date) httpParams = httpParams.set('end_date', params.end_date);
      if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
      if (params.sort_order) httpParams = httpParams.set('sort_order', params.sort_order);
    }

    return this.http.get<FeedbackPaginationResponse>(this.baseUrl, { params: httpParams });
  }

  /**
   * Get feedback/support ticket details by ID.
   * GET /api/v1/feedback/{id}
   */
  getFeedbackById(id: number): Observable<FeedbackRead> {
    return this.http.get<FeedbackRead>(`${this.baseUrl}/${id}`);
  }

  /**
   * Get ticket lifecycle and resolution history.
   * GET /api/v1/feedback/{id}/history
   */
  getFeedbackHistory(id: number): Observable<FeedbackHistoryResponse> {
    return this.http.get<FeedbackHistoryResponse>(`${this.baseUrl}/${id}/history`);
  }

  /**
   * Update feedback status, priority or triage data (Admin / Official).
   * PUT /api/v1/feedback/{id}/status
   */
  updateFeedbackStatus(id: number, payload: FeedbackUpdate): Observable<FeedbackRead> {
    return this.http.put<FeedbackRead>(`${this.baseUrl}/${id}/status`, payload);
  }

  /**
   * Post official resolution remarks to ticket (Admin / Official).
   * POST /api/v1/feedback/{id}/resolve
   */
  resolveFeedback(id: number, payload: FeedbackResolve): Observable<FeedbackRead> {
    return this.http.post<FeedbackRead>(`${this.baseUrl}/${id}/resolve`, payload);
  }
}
