import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, map, catchError, of } from 'rxjs';
import {
  SchemeCategory,
  SchemeCreateDto,
  SchemeDetailReadDto,
  SchemeItem,
  SchemeReadDto,
  SchemeStatus,
  SchemeUpdateDto,
  INITIAL_SCHEMES
} from '../../../models/scheme.model';
import { SchemeListParams, SchemeSearchParams, SchemeService } from '../../../core/services/scheme.service';

@Injectable({
  providedIn: 'root'
})
export class Scheme {
  private readonly schemeApiService = inject(SchemeService);

  private readonly _schemes = signal<SchemeItem[]>([]);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  /** Read-only reactive signal of all schemes */
  public readonly schemes = this._schemes.asReadonly();
  public readonly isLoading = this._isLoading.asReadonly();
  public readonly error = this._error.asReadonly();

  /** Total schemes count */
  public readonly totalSchemes = computed(() => this._schemes().length);

  /** Active (non-archived) schemes computed */
  public readonly activeSchemes = computed(() =>
    this._schemes().filter(s => s.status !== 'Archived')
  );

  /** Archived schemes computed */
  public readonly archivedSchemes = computed(() =>
    this._schemes().filter(s => s.status === 'Archived')
  );

  constructor() {
    this.refreshSchemes().subscribe();
  }

  /**
   * Refresh schemes list from FastAPI backend GET /api/v1/schemes
   */
  refreshSchemes(params?: SchemeListParams): Observable<SchemeItem[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.schemeApiService.listSchemes({
      page: params?.page || 1,
      page_size: params?.page_size || 100,
      category: params?.category,
      status: params?.status,
      keyword: params?.keyword,
      department: params?.department,
      state: params?.state,
      sort_by: params?.sort_by || 'created_at',
      sort_order: params?.sort_order || 'desc'
    }).pipe(
      map(response => {
        const items = (response.results || []).map(r => this.mapDtoToSchemeItem(r));
        this._schemes.set(items);
        this._isLoading.set(false);
        return items;
      }),
      catchError(err => {
        console.warn('Backend schemes fetch failed, falling back to cached mock data:', err.message);
        this._isLoading.set(false);
        this._error.set(err.message || 'Failed to load schemes');
        if (this._schemes().length === 0) {
          this._schemes.set([...INITIAL_SCHEMES]);
        }
        return of(this._schemes());
      })
    );
  }

  /**
   * Return all schemes currently in state.
   */
  getAll(): SchemeItem[] {
    return this._schemes();
  }

  /**
   * Find scheme by ID (case-insensitive, matches numeric or string).
   */
  getById(id: string): SchemeItem | undefined {
    if (!id) return undefined;
    const normalized = id.trim().toLowerCase();
    const digits = id.replace(/\D/g, '');
    const num = digits ? parseInt(digits, 10) : NaN;

    return this._schemes().find(s =>
      s.id.toLowerCase() === normalized ||
      (s.numericId !== undefined && s.numericId === num) ||
      (`sch-${String(s.numericId || s.id).padStart(3, '0')}`.toLowerCase() === normalized)
    );
  }

  /**
   * Fetch a single scheme with details and rules from backend.
   */
  fetchById(id: string): Observable<SchemeItem | null> {
    return this.schemeApiService.getScheme(id).pipe(
      map(dto => {
        const item = this.mapDtoToSchemeItem(dto);
        this.updateLocalState(item);
        return item;
      }),
      catchError(err => {
        const cached = this.getById(id);
        return of(cached || null);
      })
    );
  }

  /**
   * Create a new scheme asynchronously via backend POST /api/v1/schemes
   */
  createAsync(newScheme: Omit<SchemeItem, 'updatedAt'>): Observable<SchemeItem> {
    const payload: SchemeCreateDto = {
      name: newScheme.name,
      description: newScheme.description,
      benefits: newScheme.benefits,
      target_audience: newScheme.eligibilityCriteria || newScheme.targetAudience,
      category: newScheme.category,
      department: newScheme.department,
      ministry: newScheme.ministry,
      state: newScheme.state,
      sector: newScheme.sector,
      application_process: newScheme.applicationProcess,
      status: this.mapFrontendStatusToBackend(newScheme.status),
      is_active: newScheme.status !== 'Archived'
    };

    return this.schemeApiService.createScheme(payload).pipe(
      map(dto => {
        const created = this.mapDtoToSchemeItem(dto);
        this._schemes.update(current => [created, ...current]);
        return created;
      })
    );
  }

  /**
   * Synchronous creation for existing components.
   */
  create(newScheme: Omit<SchemeItem, 'updatedAt'>): SchemeItem {
    const tempId = `TEMP-SCH-${Date.now()}`;
    const today = this.formatDate(new Date());
    const optimistic: SchemeItem = {
      ...newScheme,
      id: tempId,
      updatedAt: today,
      createdAt: newScheme.createdAt || today
    };

    this._schemes.update(current => [optimistic, ...current]);

    this.createAsync(newScheme).subscribe({
      next: (synced) => {
        this._schemes.update(current =>
          current.map(s => s.id === tempId ? synced : s)
        );
      },
      error: (err) => console.error('Failed to create scheme on backend:', err)
    });

    return optimistic;
  }

  /**
   * Update an existing scheme via backend PUT /api/v1/schemes/{id}
   */
  updateAsync(id: string, updates: Partial<SchemeItem>): Observable<SchemeItem> {
    const payload: SchemeUpdateDto = {
      name: updates.name,
      description: updates.description,
      benefits: updates.benefits,
      target_audience: updates.eligibilityCriteria || updates.targetAudience,
      category: updates.category,
      department: updates.department,
      ministry: updates.ministry,
      state: updates.state,
      sector: updates.sector,
      application_process: updates.applicationProcess,
      status: updates.status ? this.mapFrontendStatusToBackend(updates.status) : undefined,
      is_active: updates.status ? updates.status !== 'Archived' : undefined
    };

    return this.schemeApiService.updateScheme(id, payload).pipe(
      map(dto => {
        const updated = this.mapDtoToSchemeItem(dto);
        this.updateLocalState(updated);
        return updated;
      })
    );
  }

  /**
   * Synchronous update for existing components.
   */
  update(id: string, updates: Partial<SchemeItem>): SchemeItem | undefined {
    let found: SchemeItem | undefined;
    const today = this.formatDate(new Date());

    this._schemes.update(current =>
      current.map(s => {
        if (s.id.toLowerCase() === id.trim().toLowerCase() || (s.numericId && String(s.numericId) === id)) {
          found = { ...s, ...updates, updatedAt: today };
          return found;
        }
        return s;
      })
    );

    this.updateAsync(id, updates).subscribe({
      next: (synced) => this.updateLocalState(synced),
      error: (err) => console.error('Failed to sync scheme update to backend:', err)
    });

    return found;
  }

  /**
   * Archive a scheme DELETE /api/v1/schemes/{id}
   */
  archiveAsync(id: string): Observable<SchemeItem> {
    return this.schemeApiService.archiveScheme(id).pipe(
      map(dto => {
        const item = this.mapDtoToSchemeItem(dto);
        this.updateLocalState(item);
        return item;
      })
    );
  }

  /**
   * Synchronous archive.
   */
  archive(id: string): SchemeItem | undefined {
    const scheme = this.getById(id);
    if (!scheme) return undefined;

    const optimistic: SchemeItem = {
      ...scheme,
      status: 'Archived'
    };
    this.updateLocalState(optimistic);

    this.archiveAsync(id).subscribe({
      next: (synced) => this.updateLocalState(synced),
      error: (err) => console.error('Failed to archive scheme on backend:', err)
    });

    return optimistic;
  }

  /**
   * Restore an archived scheme to Active.
   */
  restore(id: string): SchemeItem | undefined {
    return this.update(id, {
      status: 'Active'
    });
  }

  /**
   * Delete a scheme permanently or archive.
   */
  delete(id: string): boolean {
    this.archive(id);
    return true;
  }

  /**
   * Frontend multi-criteria filtering.
   */
  filterAndSearch(
    query: string = '',
    category: string = 'All',
    state: string = 'All',
    ministry: string = 'All',
    department: string = 'All',
    status?: string
  ): SchemeItem[] {
    let list = this._schemes();

    if (status) {
      list = list.filter(s => s.status.toLowerCase() === status.toLowerCase());
    } else {
      list = list.filter(s => s.status !== 'Archived');
    }

    if (category && category !== 'All') {
      list = list.filter(s => s.category.toLowerCase() === category.toLowerCase());
    }

    if (state && state !== 'All') {
      list = list.filter(s => s.state.toLowerCase() === state.toLowerCase());
    }

    if (ministry && ministry !== 'All') {
      list = list.filter(s => s.ministry.toLowerCase() === ministry.toLowerCase());
    }

    if (department && department !== 'All') {
      list = list.filter(s => s.department.toLowerCase() === department.toLowerCase());
    }

    if (query && query.trim()) {
      const q = query.trim().toLowerCase();
      list = list.filter(s =>
        s.name.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q) ||
        s.ministry.toLowerCase().includes(q) ||
        s.department.toLowerCase().includes(q) ||
        s.state.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        (s.tags && s.tags.some(t => t.toLowerCase().includes(q)))
      );
    }

    return list;
  }

  /**
   * Helper mapper from backend SchemeReadDto to frontend SchemeItem
   */
  public mapDtoToSchemeItem(dto: SchemeReadDto | SchemeDetailReadDto): SchemeItem {
    const status = this.mapBackendStatusToFrontend(dto.status);
    const pubDate = dto.publication_date
      ? this.formatDateString(dto.publication_date)
      : this.formatDateString(dto.created_at);
    const idStr = String(dto.id);

    return {
      id: idStr,
      numericId: dto.id,
      name: dto.name,
      description: dto.description || '',
      category: (dto.category as SchemeCategory) || 'Scholarships',
      ministry: dto.ministry || 'Ministry of Public Welfare',
      department: dto.department || 'Department of Public Welfare',
      state: dto.state || 'Central / All India',
      sector: dto.sector || undefined,
      targetAudience: dto.target_audience || undefined,
      benefits: dto.benefits || 'Provides direct assistance and welfare provisions to eligible applicants.',
      eligibilityCriteria: dto.target_audience || 'All eligible citizens meeting nodal department criteria.',
      applicationProcess: dto.application_process || 'Apply online through national portal or visit nearest facilitation centre.',
      applicationUrl: 'https://india.gov.in',
      startDate: pubDate,
      endDate: 'Ongoing',
      status: status,
      updatedAt: this.formatDateString(dto.updated_at),
      createdAt: this.formatDateString(dto.created_at),
      policyId: dto.policy_id || undefined,
      tags: [dto.category || 'Welfare', dto.state || 'National'].filter(Boolean)
    };
  }

  private mapBackendStatusToFrontend(status: string): SchemeStatus {
    const clean = status ? status.trim().toUpperCase() : 'ACTIVE';
    switch (clean) {
      case 'ACTIVE': return 'Active';
      case 'DRAFT': return 'Draft';
      case 'CLOSED':
      case 'INACTIVE': return 'Closed';
      case 'ARCHIVED': return 'Archived';
      default: return 'Active';
    }
  }

  private mapFrontendStatusToBackend(status: SchemeStatus | string): string {
    switch (status) {
      case 'Active': return 'ACTIVE';
      case 'Draft': return 'DRAFT';
      case 'Closed': return 'CLOSED';
      case 'Archived': return 'ARCHIVED';
      default: return 'ACTIVE';
    }
  }

  private updateLocalState(item: SchemeItem): void {
    this._schemes.update(current => {
      const idx = current.findIndex(s => s.id === item.id || (s.numericId && s.numericId === item.numericId));
      if (idx >= 0) {
        const next = [...current];
        next[idx] = item;
        return next;
      }
      return [item, ...current];
    });
  }

  private formatDate(d: Date): string {
    const day = String(d.getDate()).padStart(2, '0');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${day} ${months[d.getMonth()]} ${d.getFullYear()}`;
  }

  private formatDateString(dateVal: string): string {
    if (!dateVal) return '';
    try {
      const d = new Date(dateVal);
      if (isNaN(d.getTime())) return dateVal;
      return this.formatDate(d);
    } catch {
      return dateVal;
    }
  }
}
