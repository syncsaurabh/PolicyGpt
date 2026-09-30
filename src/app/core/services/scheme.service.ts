import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  EligibilityCheckRequest,
  EligibilityCheckResponse,
  EligibilityRuleDto,
  SchemeCreateDto,
  SchemeDetailReadDto,
  SchemePaginationResponseDto,
  SchemeReadDto,
  SchemeUpdateDto
} from '../../models/scheme.model';

export interface SchemeListParams {
  page?: number;
  page_size?: number;
  category?: string;
  status?: string;
  department?: string;
  state?: string;
  policy_id?: number;
  keyword?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SchemeSearchParams extends SchemeListParams {
  ministry?: string;
  sector?: string;
  publication_date?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SchemeService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;
  private readonly healthUrl = environment.apiUrl.replace('/api/v1', '');

  /**
   * Health check endpoint
   */
  checkHealth(): Observable<any> {
    return this.http.get<any>(`${this.healthUrl}/health`);
  }

  /**
   * List schemes with filters and pagination GET /api/v1/schemes
   */
  listSchemes(params?: SchemeListParams): Observable<SchemePaginationResponseDto> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.category && params.category !== 'All') httpParams = httpParams.set('category', params.category);
      if (params.status && params.status !== 'All') httpParams = httpParams.set('status', params.status);
      if (params.department && params.department !== 'All') httpParams = httpParams.set('department', params.department);
      if (params.state && params.state !== 'All') httpParams = httpParams.set('state', params.state);
      if (params.policy_id !== undefined) httpParams = httpParams.set('policy_id', params.policy_id.toString());
      if (params.keyword) httpParams = httpParams.set('keyword', params.keyword);
      if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
      if (params.sort_order) httpParams = httpParams.set('sort_order', params.sort_order);
    }
    return this.http.get<SchemePaginationResponseDto>(`${this.apiUrl}/schemes`, { params: httpParams });
  }

  /**
   * Retrieve scheme details and eligibility rules GET /api/v1/schemes/{id}
   */
  getScheme(id: number | string): Observable<SchemeDetailReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.get<SchemeDetailReadDto>(`${this.apiUrl}/schemes/${cleanId}`);
  }

  /**
   * Register a new public scheme POST /api/v1/schemes
   */
  createScheme(payload: SchemeCreateDto): Observable<SchemeReadDto> {
    return this.http.post<SchemeReadDto>(`${this.apiUrl}/schemes`, payload);
  }

  /**
   * Update scheme details PUT /api/v1/schemes/{id}
   */
  updateScheme(id: number | string, payload: SchemeUpdateDto): Observable<SchemeReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.put<SchemeReadDto>(`${this.apiUrl}/schemes/${cleanId}`, payload);
  }

  /**
   * Soft-delete / archive a scheme DELETE /api/v1/schemes/{id}
   */
  archiveScheme(id: number | string): Observable<SchemeReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.delete<SchemeReadDto>(`${this.apiUrl}/schemes/${cleanId}`);
  }

  /**
   * Add an eligibility rule to a scheme POST /api/v1/schemes/{id}/rules
   */
  addEligibilityRule(schemeId: number | string, rule: EligibilityRuleDto): Observable<EligibilityRuleDto> {
    const cleanId = this.extractNumericId(schemeId);
    return this.http.post<EligibilityRuleDto>(`${this.apiUrl}/schemes/${cleanId}/rules`, rule);
  }

  /**
   * Search public schemes with multi-field filters GET /api/v1/search/schemes
   */
  searchSchemes(params: SchemeSearchParams): Observable<SchemePaginationResponseDto> {
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

    return this.http.get<SchemePaginationResponseDto>(`${this.apiUrl}/search/schemes`, { params: httpParams });
  }

  /**
   * Check citizen eligibility against live schemes POST /api/v1/eligibility/check
   */
  checkEligibility(request: EligibilityCheckRequest): Observable<EligibilityCheckResponse> {
    return this.http.post<EligibilityCheckResponse>(`${this.apiUrl}/eligibility/check`, request);
  }

  /**
   * Helper to parse integer ID from strings like "1", "SCH-001", etc.
   */
  private extractNumericId(id: number | string): number {
    if (typeof id === 'number') return id;
    const digits = id.replace(/\D/g, '');
    const parsed = parseInt(digits, 10);
    return isNaN(parsed) ? parseInt(id, 10) || 1 : parsed;
  }
}
