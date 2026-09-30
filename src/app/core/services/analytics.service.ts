import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  DepartmentAnalyticsResponse,
  NotificationAnalytics,
  OverviewAnalyticsResponse,
  PolicyAnalytics,
  SchemeAnalytics,
  SearchAnalytics,
  UsageStatisticsResponse,
  UserAnalytics
} from '../../models/analytics.model';

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/analytics`;

  /**
   * Get platform overview analytics and KPIs
   * GET /api/v1/analytics/overview
   */
  getOverview(): Observable<OverviewAnalyticsResponse> {
    return this.http.get<OverviewAnalyticsResponse>(`${this.apiUrl}/overview`);
  }

  /**
   * Get policy statistics, status breakdown, and distributions
   * GET /api/v1/analytics/policies
   */
  getPolicies(): Observable<PolicyAnalytics> {
    return this.http.get<PolicyAnalytics>(`${this.apiUrl}/policies`);
  }

  /**
   * Get scheme statistics, operational status, and distributions
   * GET /api/v1/analytics/schemes
   */
  getSchemes(): Observable<SchemeAnalytics> {
    return this.http.get<SchemeAnalytics>(`${this.apiUrl}/schemes`);
  }

  /**
   * Get user management demographics and growth statistics
   * GET /api/v1/analytics/users
   */
  getUsers(): Observable<UserAnalytics> {
    return this.http.get<UserAnalytics>(`${this.apiUrl}/users`);
  }

  /**
   * Get department-level analytics and publication statistics
   * GET /api/v1/analytics/departments
   */
  getDepartments(): Observable<DepartmentAnalyticsResponse> {
    return this.http.get<DepartmentAnalyticsResponse>(`${this.apiUrl}/departments`);
  }

  /**
   * Get search activity and popular queries analytics
   * GET /api/v1/analytics/search
   */
  getSearch(): Observable<SearchAnalytics> {
    return this.http.get<SearchAnalytics>(`${this.apiUrl}/search`);
  }

  /**
   * Get notification delivery and engagement analytics
   * GET /api/v1/analytics/notifications
   */
  getNotifications(): Observable<NotificationAnalytics> {
    return this.http.get<NotificationAnalytics>(`${this.apiUrl}/notifications`);
  }

  /**
   * Get platform usage statistics and event counts
   * GET /api/v1/analytics/usage
   */
  getUsage(): Observable<UsageStatisticsResponse> {
    return this.http.get<UsageStatisticsResponse>(`${this.apiUrl}/usage`);
  }
}
