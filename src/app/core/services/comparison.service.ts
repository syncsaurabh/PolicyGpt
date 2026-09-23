import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, map, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ComparisonItem,
  ComparisonRequest,
  ComparisonResponse,
  SelectableCompareItem
} from '../../models/comparison.model';
import { PolicyService } from './policy.service';
import { SchemeService } from './scheme.service';

@Injectable({
  providedIn: 'root'
})
export class ComparisonService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;
  private readonly policyService = inject(PolicyService);
  private readonly schemeService = inject(SchemeService);

  /**
   * Dedicated backend endpoint: POST /api/v1/comparison
   * Compares 2 to 3 policies or schemes side-by-side.
   */
  compare(payload: ComparisonRequest): Observable<ComparisonResponse> {
    return this.http.post<ComparisonResponse>(`${this.apiUrl}/comparison`, payload);
  }

  /**
   * Fetches all available policies and schemes from live backend,
   * normalizes them into unified SelectableCompareItem structures for CP-01 / CP-02.
   */
  fetchSelectableItems(): Observable<SelectableCompareItem[]> {
    return forkJoin({
      policies: this.policyService.listPolicies({ page: 1, page_size: 50 }).pipe(
        map(res => res.results || []),
        catchError(() => of([]))
      ),
      schemes: this.schemeService.listSchemes({ page: 1, page_size: 50 }).pipe(
        map(res => res.results || []),
        catchError(() => of([]))
      )
    }).pipe(
      map(({ policies, schemes }) => {
        const mappedPolicies: SelectableCompareItem[] = policies.map((p) => {
          const rawId = typeof p.id === 'number' ? p.id : parseInt(String(p.id).replace(/\D/g, ''), 10) || 1;
          const code = `POL-${String(rawId).padStart(3, '0')}`;
          return {
            id: rawId,
            code,
            name: p.title || 'Untitled Policy',
            type: 'Policy',
            category: p.category || 'General',
            ministry: p.ministry || 'Ministry of Education',
            department: p.department || 'Department of School Education',
            description: p.description || 'Framework and comprehensive guidelines outlining strategic governance priorities.',
            state: p.state || 'Central / All India',
            target_audience: p.sector ? `Target Sector: ${p.sector}` : 'All Citizens & Educational Institutions',
            status: p.status || 'PUBLISHED',
            benefits: 'Provides regulatory framework, strategic standards, and educational reform mandates across states.',
            eligibility: 'Applicable across public institutions, accredited educational centers, and registered agencies.',
            application_process: 'Implemented directly through regional nodal agencies and state institutional authorities.',
            documents_required: 'Not applicable (Governance Policy & Institutional Standard Framework)'
          };
        });

        const mappedSchemes: SelectableCompareItem[] = schemes.map((s) => {
          const rawId = typeof s.id === 'number' ? s.id : parseInt(String(s.id).replace(/\D/g, ''), 10) || 1;
          const code = `SCH-${String(rawId).padStart(3, '0')}`;
          return {
            id: rawId,
            code,
            name: s.name || 'Untitled Scheme',
            type: 'Scheme',
            category: s.category || 'Welfare',
            ministry: s.ministry || 'Ministry of Social Justice & Empowerment',
            department: s.department || 'Department of Public Welfare',
            description: s.description || 'Direct citizen welfare initiative offering structured assistance and subsidies.',
            state: s.state || 'Central / All India',
            target_audience: s.target_audience || 'Eligible students, youth, and low-income families',
            status: s.status || 'ACTIVE',
            benefits: s.benefits || 'Financial assistance, fee concessions, and monthly academic stipends.',
            eligibility: 'Resident citizens meeting age, income ceiling, and institutional admission criteria.',
            application_process: s.application_process || 'Online application through designated state/national portal with verified credentials.',
            documents_required: 'Identity proof (Aadhaar), Income Certificate, Bank Passbook, Academic Credentials'
          };
        });

        return [...mappedPolicies, ...mappedSchemes];
      })
    );
  }

  /**
   * Formats string/array values into structured bullet points or readable strings.
   */
  normalizeTextValue(value: any): string {
    if (!value) return 'Not available';
    if (Array.isArray(value)) {
      if (value.length === 0) return 'Not available';
      return value.map(v => typeof v === 'object' ? JSON.stringify(v) : String(v)).join('\n• ');
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  }
}
