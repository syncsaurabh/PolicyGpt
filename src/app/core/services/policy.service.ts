import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface SystemHealth {
  status: string;
  timestamp?: string;
  version?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PolicyService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl.replace('/api/v1', '');

  /**
   * Check system health from /health endpoint.
   */
  checkHealth(): Observable<SystemHealth> {
    return this.http.get<SystemHealth>(`${this.baseUrl}/health`);
  }

  /**
   * Placeholder for policy intelligence and document search.
   */
  getPolicies(query?: string): Observable<any[]> {
    return of([]);
  }
}
