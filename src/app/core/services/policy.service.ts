import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  PolicyApprovalActionDto,
  PolicyCreateDto,
  PolicyPaginationResponseDto,
  PolicyReadDto,
  PolicyUpdateDto
} from '../../models/policy.model';

export interface SystemHealth {
  status: string;
  timestamp?: string;
  version?: string;
}

export interface PolicyListParams {
  page?: number;
  page_size?: number;
  category?: string;
  status?: string;
  department?: string;
  state?: string;
  keyword?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PolicySearchParams extends PolicyListParams {
  ministry?: string;
  sector?: string;
  publication_date?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PolicyService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;
  private readonly healthUrl = environment.apiUrl.replace('/api/v1', '');

  /**
   * Health check endpoint GET /health
   */
  checkHealth(): Observable<SystemHealth> {
    return this.http.get<SystemHealth>(`${this.healthUrl}/health`);
  }

  /**
   * List policies with pagination, sorting, and filters GET /api/v1/policies
   */
  listPolicies(params?: PolicyListParams): Observable<PolicyPaginationResponseDto> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.category && params.category !== 'All') httpParams = httpParams.set('category', params.category);
      if (params.status && params.status !== 'All') httpParams = httpParams.set('status', params.status);
      if (params.department && params.department !== 'All') httpParams = httpParams.set('department', params.department);
      if (params.state && params.state !== 'All') httpParams = httpParams.set('state', params.state);
      if (params.keyword) httpParams = httpParams.set('keyword', params.keyword);
      if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
      if (params.sort_order) httpParams = httpParams.set('sort_order', params.sort_order);
    }
    return this.http.get<PolicyPaginationResponseDto>(`${this.apiUrl}/policies`, { params: httpParams });
  }

  /**
   * Retrieve single policy by ID GET /api/v1/policies/{id}
   */
  getPolicy(id: number | string): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.get<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}`);
  }

  /**
   * Create a new policy POST /api/v1/policies
   */
  createPolicy(payload: PolicyCreateDto): Observable<PolicyReadDto> {
    return this.http.post<PolicyReadDto>(`${this.apiUrl}/policies`, payload);
  }

  /**
   * Update existing policy PUT /api/v1/policies/{id}
   */
  updatePolicy(id: number | string, payload: PolicyUpdateDto): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.put<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}`, payload);
  }

  /**
   * Soft-delete / archive policy DELETE /api/v1/policies/{id}
   */
  archivePolicy(id: number | string): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.delete<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}`);
  }

  /**
   * Submit policy for review/approval POST /api/v1/policies/{id}/submit
   */
  submitForApproval(id: number | string): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.post<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}/submit`, {});
  }

  /**
   * Approve a pending policy POST /api/v1/policies/{id}/approve
   */
  approvePolicy(id: number | string, action?: PolicyApprovalActionDto): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.post<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}/approve`, action || {});
  }

  /**
   * Reject a pending policy POST /api/v1/policies/{id}/reject
   */
  rejectPolicy(id: number | string, action?: PolicyApprovalActionDto): Observable<PolicyReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.post<PolicyReadDto>(`${this.apiUrl}/policies/${cleanId}/reject`, action || {});
  }

  /**
   * Search policies with multi-field filters GET /api/v1/search/policies
   */
  searchPolicies(params: PolicySearchParams): Observable<PolicyPaginationResponseDto> {
    let httpParams = new HttpParams();
    if (params.keyword) httpParams = httpParams.set('keyword', params.keyword);
    if (params.category && params.category !== 'All') httpParams = httpParams.set('category', params.category);
    if (params.state && params.state !== 'All') httpParams = httpParams.set('state', params.state);
    if (params.ministry && params.ministry !== 'All') httpParams = httpParams.set('ministry', params.ministry);
    if (params.department && params.department !== 'All') httpParams = httpParams.set('department', params.department);
    if (params.sector && params.sector !== 'All') httpParams = httpParams.set('sector', params.sector);
    if (params.status && params.status !== 'All') httpParams = httpParams.set('status', params.status);
    if (params.publication_date) httpParams = httpParams.set('publication_date', params.publication_date);
    if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
    if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
    if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
    if (params.sort_order) httpParams = httpParams.set('sort_order', params.sort_order);

    return this.http.get<PolicyPaginationResponseDto>(`${this.apiUrl}/search/policies`, { params: httpParams });
  }

  /**
   * Helper to parse integer ID from strings like "2", "POL-002", etc.
   */
  private extractNumericId(id: number | string): number {
    if (typeof id === 'number') return id;
    const digits = id.replace(/\D/g, '');
    const parsed = parseInt(digits, 10);
    return isNaN(parsed) ? parseInt(id, 10) || 1 : parsed;
  }
}
