import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { FAQCreatePayload, FAQItem, FAQListResponse, FAQQueryParams, FAQUpdatePayload } from '../../models/faq.model';

@Injectable({
  providedIn: 'root'
})
export class FaqService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/faqs`;

  /**
   * List FAQs with optional category, keyword, and pagination filters
   */
  getFAQs(params?: FAQQueryParams): Observable<FAQListResponse> {
    let httpParams = new HttpParams();

    if (params?.category && params.category !== 'All') {
      httpParams = httpParams.set('category', params.category);
    }
    if (params?.keyword && params.keyword.trim().length > 0) {
      httpParams = httpParams.set('keyword', params.keyword.trim());
    }
    if (params?.page) {
      httpParams = httpParams.set('page', params.page.toString());
    }
    if (params?.page_size) {
      httpParams = httpParams.set('page_size', params.page_size.toString());
    }

    return this.http.get<FAQListResponse>(this.apiUrl, { params: httpParams });
  }

  /**
   * Get single FAQ by ID
   */
  getFAQById(id: number): Observable<FAQItem> {
    return this.http.get<FAQItem>(`${this.apiUrl}/${id}`);
  }

  /**
   * Create a new FAQ entry (Admin / Official)
   */
  createFAQ(payload: FAQCreatePayload): Observable<FAQItem> {
    return this.http.post<FAQItem>(this.apiUrl, payload);
  }

  /**
   * Update an existing FAQ entry (Admin / Official)
   */
  updateFAQ(id: number, payload: FAQUpdatePayload): Observable<FAQItem> {
    return this.http.put<FAQItem>(`${this.apiUrl}/${id}`, payload);
  }

  /**
   * Delete an FAQ entry (Admin only)
   */
  deleteFAQ(id: number): Observable<{ message?: string; success?: boolean }> {
    return this.http.delete<{ message?: string; success?: boolean }>(`${this.apiUrl}/${id}`);
  }
}
