import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface SchemeItem {
  id: string | number;
  title: string;
  category: string;
  description: string;
  department?: string;
  eligibilitySnippet?: string;
  benefits?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SchemeService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl.replace('/api/v1', '');

  /**
   * Check system health from /health endpoint.
   */
  checkHealth(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/health`);
  }

  /**
   * Get beneficiary schemes.
   */
  getSchemes(category?: string): Observable<SchemeItem[]> {
    return of([]);
  }
}
