import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AdminNotificationListParams,
  AdminNotificationPaginationResponse,
  MessageResponse,
  NotificationBroadcast,
  NotificationCreate,
  NotificationListParams,
  NotificationPaginationResponse,
  NotificationPreferenceRead,
  NotificationPreferenceUpdate,
  NotificationRead,
  NotificationUnreadCountResponse,
} from '../../models/notification.model';

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/notifications`;

  /**
   * Reactive signal holding current unread count for badges and popovers.
   */
  readonly unreadCount = signal<number>(0);

  /**
   * Cached recent notifications for topbar quick-view.
   */
  readonly recentNotifications = signal<NotificationRead[]>([]);

  /**
   * List notifications for current authenticated user with filters and pagination.
   * GET /api/v1/notifications
   */
  getNotifications(params?: NotificationListParams): Observable<NotificationPaginationResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.unread_only !== undefined) httpParams = httpParams.set('unread_only', params.unread_only.toString());
      if (params.notification_type && params.notification_type !== 'ALL') {
        httpParams = httpParams.set('notification_type', params.notification_type);
      }
      if (params.channel && params.channel !== 'ALL') {
        httpParams = httpParams.set('channel', params.channel);
      }
    }

    return this.http.get<NotificationPaginationResponse>(this.baseUrl, { params: httpParams }).pipe(
      tap((res) => {
        if (res.unread_count !== undefined) {
          this.unreadCount.set(res.unread_count);
        }
      })
    );
  }

  /**
   * Fetch unread notification count badge.
   * GET /api/v1/notifications/unread-count
   */
  getUnreadCount(): Observable<NotificationUnreadCountResponse> {
    return this.http.get<NotificationUnreadCountResponse>(`${this.baseUrl}/unread-count`).pipe(
      tap((res) => {
        this.unreadCount.set(res.unread_count);
      })
    );
  }

  /**
   * Trigger refresh of unread count.
   */
  refreshUnreadCount(): void {
    this.getUnreadCount().subscribe({
      next: () => {},
      error: () => {}
    });
  }

  /**
   * Load quick recent notifications for topbar dropdown.
   */
  loadRecentForDropdown(): Observable<NotificationPaginationResponse> {
    return this.getNotifications({ page: 1, page_size: 5 }).pipe(
      tap((res) => {
        this.recentNotifications.set(res.results || []);
      })
    );
  }

  /**
   * Get single notification details by ID.
   * GET /api/v1/notifications/{id}
   */
  getNotification(id: number): Observable<NotificationRead> {
    return this.http.get<NotificationRead>(`${this.baseUrl}/${id}`);
  }

  /**
   * Mark a specific notification as read.
   * PATCH /api/v1/notifications/{id}/read
   */
  markAsRead(id: number): Observable<NotificationRead> {
    return this.http.patch<NotificationRead>(`${this.baseUrl}/${id}/read`, {}).pipe(
      tap(() => {
        // Decrement unread count locally and reload
        this.unreadCount.update((c) => Math.max(0, c - 1));
        this.recentNotifications.update((list) =>
          list.map((item) => (item.id === id ? { ...item, is_read: true } : item))
        );
      })
    );
  }

  /**
   * Mark all pending notifications as read for current user.
   * PUT /api/v1/notifications/mark-all-read
   */
  markAllAsRead(): Observable<MessageResponse> {
    return this.http.put<MessageResponse>(`${this.baseUrl}/mark-all-read`, {}).pipe(
      tap(() => {
        this.unreadCount.set(0);
        this.recentNotifications.update((list) =>
          list.map((item) => ({ ...item, is_read: true }))
        );
      })
    );
  }

  /**
   * Delete a notification.
   * DELETE /api/v1/notifications/{id}
   */
  deleteNotification(id: number): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${this.baseUrl}/${id}`).pipe(
      tap(() => {
        this.recentNotifications.update((list) => list.filter((item) => item.id !== id));
        this.refreshUnreadCount();
      })
    );
  }

  /**
   * Get current user's notification preferences.
   * GET /api/v1/notifications/preferences
   */
  getPreferences(): Observable<NotificationPreferenceRead> {
    return this.http.get<NotificationPreferenceRead>(`${this.baseUrl}/preferences`);
  }

  /**
   * Update notification preferences.
   * PUT /api/v1/notifications/preferences
   */
  updatePreferences(pref: NotificationPreferenceUpdate): Observable<NotificationPreferenceRead> {
    return this.http.put<NotificationPreferenceRead>(`${this.baseUrl}/preferences`, pref);
  }

  /**
   * Create targeted notification for specific user (Admin / Official).
   * POST /api/v1/notifications
   */
  createTargetedNotification(data: NotificationCreate): Observable<NotificationRead> {
    return this.http.post<NotificationRead>(this.baseUrl, data);
  }

  /**
   * Broadcast notification to users across roles (Admin only).
   * POST /api/v1/notifications/broadcast
   */
  broadcastNotification(data: NotificationBroadcast): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.baseUrl}/broadcast`, data);
  }

  /**
   * List all system notifications across users (Admin only).
   * GET /api/v1/notifications/admin/all
   */
  getAdminNotifications(params?: AdminNotificationListParams): Observable<AdminNotificationPaginationResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.user_id !== undefined && params.user_id !== null) {
        httpParams = httpParams.set('user_id', params.user_id.toString());
      }
      if (params.status_filter && params.status_filter !== 'ALL') {
        httpParams = httpParams.set('status_filter', params.status_filter);
      }
      if (params.notification_type && params.notification_type !== 'ALL') {
        httpParams = httpParams.set('notification_type', params.notification_type);
      }
      if (params.channel && params.channel !== 'ALL') {
        httpParams = httpParams.set('channel', params.channel);
      }
    }

    return this.http.get<AdminNotificationPaginationResponse>(`${this.baseUrl}/admin/all`, { params: httpParams });
  }

  /**
   * Trigger background check for scheme deadlines and dispatch reminders (Admin only).
   * POST /api/v1/notifications/deadline-check
   */
  triggerDeadlineCheck(): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.baseUrl}/deadline-check`, {});
  }
}
