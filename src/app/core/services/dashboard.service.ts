import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AdminDashboardResponse,
  ApplicationStatusItem,
  CitizenDashboardResponse,
  GovernmentDashboardResponse,
  SavedPolicyCreate,
  SavedPolicyItem,
  SchemeApplicationCreate
} from '../../models/dashboard.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/dashboard`;

  /**
   * Get Administrator Dashboard data
   * GET /api/v1/dashboard/admin
   */
  getAdminDashboard(): Observable<AdminDashboardResponse> {
    return this.http.get<AdminDashboardResponse>(`${this.apiUrl}/admin`);
  }

  /**
   * Get Government Official Dashboard data
   * GET /api/v1/dashboard/government
   */
  getGovernmentDashboard(): Observable<GovernmentDashboardResponse> {
    return this.http.get<GovernmentDashboardResponse>(`${this.apiUrl}/government`);
  }

  /**
   * Get Citizen Dashboard data
   * GET /api/v1/dashboard/citizen
   */
  getCitizenDashboard(): Observable<CitizenDashboardResponse> {
    return this.http.get<CitizenDashboardResponse>(`${this.apiUrl}/citizen`);
  }

  /**
   * Bookmark a Policy for citizen
   * POST /api/v1/dashboard/citizen/saved-policies
   */
  savePolicy(payload: SavedPolicyCreate): Observable<SavedPolicyItem> {
    return this.http.post<SavedPolicyItem>(`${this.apiUrl}/citizen/saved-policies`, payload);
  }

  /**
   * Remove a Policy Bookmark for citizen
   * DELETE /api/v1/dashboard/citizen/saved-policies/{policy_id}
   */
  removeSavedPolicy(policyId: number): Observable<{ message?: string; [key: string]: any }> {
    return this.http.delete<{ message?: string; [key: string]: any }>(`${this.apiUrl}/citizen/saved-policies/${policyId}`);
  }

  /**
   * Submit Scheme Application for citizen
   * POST /api/v1/dashboard/citizen/applications
   */
  submitSchemeApplication(payload: SchemeApplicationCreate): Observable<ApplicationStatusItem> {
    return this.http.post<ApplicationStatusItem>(`${this.apiUrl}/citizen/applications`, payload);
  }
}
