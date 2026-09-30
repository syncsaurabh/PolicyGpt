import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  DepartmentReportParams,
  ExportFormat,
  PolicyReportParams,
  ReportDataResponse,
  ReportHistoryParams,
  ReportPaginationResponse,
  SchemeReportParams,
  UserActivityReportParams,
} from '../../models/reports.model';

@Injectable({
  providedIn: 'root',
})
export class ReportsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reports`;

  /**
   * List generated reports history.
   * GET /api/v1/reports
   */
  getReportsHistory(params?: ReportHistoryParams): Observable<ReportPaginationResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page.toString());
      if (params.page_size !== undefined) httpParams = httpParams.set('page_size', params.page_size.toString());
      if (params.report_type && params.report_type !== 'ALL') {
        httpParams = httpParams.set('report_type', params.report_type);
      }
    }
    return this.http.get<ReportPaginationResponse>(this.baseUrl, { params: httpParams });
  }

  /**
   * Get policy dataset report in JSON format.
   * GET /api/v1/reports/policies
   */
  getPolicyReport(params?: PolicyReportParams): Observable<ReportDataResponse> {
    const httpParams = this.buildFilterParams(params);
    return this.http.get<ReportDataResponse>(`${this.baseUrl}/policies`, { params: httpParams });
  }

  /**
   * Get scheme dataset report in JSON format.
   * GET /api/v1/reports/schemes
   */
  getSchemeReport(params?: SchemeReportParams): Observable<ReportDataResponse> {
    const httpParams = this.buildFilterParams(params);
    return this.http.get<ReportDataResponse>(`${this.baseUrl}/schemes`, { params: httpParams });
  }

  /**
   * Get department metrics report in JSON format.
   * GET /api/v1/reports/departments
   */
  getDepartmentReport(params?: DepartmentReportParams): Observable<ReportDataResponse> {
    let httpParams = new HttpParams();
    if (params?.department && params.department.trim() !== '') {
      httpParams = httpParams.set('department', params.department.trim());
    }
    return this.http.get<ReportDataResponse>(`${this.baseUrl}/departments`, { params: httpParams });
  }

  /**
   * Get user activity log report in JSON format.
   * GET /api/v1/reports/user-activity
   */
  getUserActivityReport(params?: UserActivityReportParams): Observable<ReportDataResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.start_date) httpParams = httpParams.set('start_date', params.start_date);
      if (params.end_date) httpParams = httpParams.set('end_date', params.end_date);
      if (params.event_type && params.event_type !== 'ALL') {
        httpParams = httpParams.set('event_type', params.event_type);
      }
    }
    return this.http.get<ReportDataResponse>(`${this.baseUrl}/user-activity`, { params: httpParams });
  }

  /**
   * Export policy report as downloadable PDF or Excel file.
   * GET /api/v1/reports/export/policies
   */
  exportPolicyReport(params: PolicyReportParams & { format: ExportFormat }): Observable<HttpResponse<Blob>> {
    const httpParams = this.buildFilterParams(params);
    return this.http.get(`${this.baseUrl}/export/policies`, {
      params: httpParams,
      responseType: 'blob',
      observe: 'response',
    });
  }

  /**
   * Export scheme report as downloadable PDF or Excel file.
   * GET /api/v1/reports/export/schemes
   */
  exportSchemeReport(params: SchemeReportParams & { format: ExportFormat }): Observable<HttpResponse<Blob>> {
    const httpParams = this.buildFilterParams(params);
    return this.http.get(`${this.baseUrl}/export/schemes`, {
      params: httpParams,
      responseType: 'blob',
      observe: 'response',
    });
  }

  /**
   * Export department report as downloadable PDF or Excel file.
   * GET /api/v1/reports/export/departments
   */
  exportDepartmentReport(params: DepartmentReportParams & { format: ExportFormat }): Observable<HttpResponse<Blob>> {
    let httpParams = new HttpParams().set('format', params.format);
    if (params.department && params.department.trim() !== '') {
      httpParams = httpParams.set('department', params.department.trim());
    }
    return this.http.get(`${this.baseUrl}/export/departments`, {
      params: httpParams,
      responseType: 'blob',
      observe: 'response',
    });
  }

  /**
   * Export user activity report as downloadable PDF or Excel file.
   * GET /api/v1/reports/export/user-activity
   */
  exportUserActivityReport(params: UserActivityReportParams & { format: ExportFormat }): Observable<HttpResponse<Blob>> {
    let httpParams = new HttpParams().set('format', params.format);
    if (params.start_date) httpParams = httpParams.set('start_date', params.start_date);
    if (params.end_date) httpParams = httpParams.set('end_date', params.end_date);
    if (params.event_type && params.event_type !== 'ALL') {
      httpParams = httpParams.set('event_type', params.event_type);
    }
    return this.http.get(`${this.baseUrl}/export/user-activity`, {
      params: httpParams,
      responseType: 'blob',
      observe: 'response',
    });
  }

  /**
   * Utility helper to trigger browser download from HttpResponse<Blob>
   */
  saveBlobFile(response: HttpResponse<Blob>, defaultFilename: string): void {
    const blob = response.body;
    if (!blob) return;

    let filename = defaultFilename;
    const disposition = response.headers.get('Content-Disposition');
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '');
      }
    }

    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  }

  private buildFilterParams(params?: Record<string, any>): HttpParams {
    let httpParams = new HttpParams();
    if (!params) return httpParams;

    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== null && val !== '' && val !== 'ALL') {
        httpParams = httpParams.set(key, val.toString());
      }
    }
    return httpParams;
  }
}
