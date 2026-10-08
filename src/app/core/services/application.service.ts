import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ApplicationCreateDto,
  ApplicationPaginationResponseDto,
  ApplicationReadDto,
  ApplicationStatusUpdateDto,
  ApplicationWithdrawDto
} from '../../models/application.model';

export interface ApplicationListParams {
  page?: number;
  page_size?: number;
  status?: string;
  scheme_id?: number;
  department?: string;
  keyword?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

@Injectable({
  providedIn: 'root'
})
export class ApplicationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  /**
   * Submit a new Scheme Application POST /api/v1/applications
   */
  createApplication(payload: ApplicationCreateDto): Observable<ApplicationReadDto> {
    return this.http.post<ApplicationReadDto>(`${this.apiUrl}/applications`, payload);
  }

  /**
   * List applications with filters and pagination GET /api/v1/applications
   */
  listApplications(params?: ApplicationListParams): Observable<ApplicationPaginationResponseDto> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.status && params.status !== 'All') httpParams = httpParams.set('status', params.status);
      if (params.scheme_id !== undefined) httpParams = httpParams.set('scheme_id', params.scheme_id.toString());
      if (params.department && params.department !== 'All') httpParams = httpParams.set('department', params.department);
      if (params.keyword) httpParams = httpParams.set('keyword', params.keyword);
      if (params.sort_by) httpParams = httpParams.set('sort_by', params.sort_by);
      if (params.sort_order) httpParams = httpParams.set('sort_order', params.sort_order);
    }
    return this.http.get<ApplicationPaginationResponseDto>(`${this.apiUrl}/applications`, { params: httpParams });
  }

  /**
   * Get single application details GET /api/v1/applications/{id}
   */
  getApplication(id: number | string): Observable<ApplicationReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.get<ApplicationReadDto>(`${this.apiUrl}/applications/${cleanId}`);
  }

  /**
   * Update application status (Official / Admin) PATCH /api/v1/applications/{id}/status
   */
  updateStatus(id: number | string, payload: ApplicationStatusUpdateDto): Observable<ApplicationReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.patch<ApplicationReadDto>(`${this.apiUrl}/applications/${cleanId}/status`, payload);
  }

  /**
   * Withdraw application (Citizen) POST /api/v1/applications/{id}/withdraw
   */
  withdrawApplication(id: number | string, payload?: ApplicationWithdrawDto): Observable<ApplicationReadDto> {
    const cleanId = this.extractNumericId(id);
    return this.http.post<ApplicationReadDto>(`${this.apiUrl}/applications/${cleanId}/withdraw`, payload || {});
  }

  /**
   * Helper to parse integer ID from strings like "1", "APP-001", etc.
   */
  private extractNumericId(id: number | string): number {
    if (typeof id === 'number') return id;
    const digits = id.replace(/\D/g, '');
    const parsed = parseInt(digits, 10);
    return isNaN(parsed) ? parseInt(id, 10) || 1 : parsed;
  }
}
