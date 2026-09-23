import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, map, catchError, of } from 'rxjs';
import {
  PolicyApprovalActionDto,
  PolicyCreateDto,
  PolicyHistoryStep,
  PolicyItem,
  PolicyReadDto,
  PolicyStatus,
  PolicyUpdateDto,
  INITIAL_POLICIES
} from '../../../models/policy.model';
import { PolicyListParams, PolicySearchParams, PolicyService } from '../../../core/services/policy.service';

@Injectable({
  providedIn: 'root'
})
export class Policy {
  private readonly policyApiService = inject(PolicyService);

  private readonly _policies = signal<PolicyItem[]>([]);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  /** Read-only reactive signal of all policies */
  public readonly policies = this._policies.asReadonly();
  public readonly isLoading = this._isLoading.asReadonly();
  public readonly error = this._error.asReadonly();

  /** Total count computed */
  public readonly totalPolicies = computed(() => this._policies().length);

  /** Active (non-archived) policies computed */
  public readonly activePolicies = computed(() =>
    this._policies().filter(p => p.status !== 'Archived')
  );

  /** Archived policies computed */
  public readonly archivedPolicies = computed(() =>
    this._policies().filter(p => p.status === 'Archived')
  );

  constructor() {
    this.refreshPolicies().subscribe();
  }

  /**
   * Fetch all policies from live FastAPI backend and update signals.
   */
  refreshPolicies(params?: PolicyListParams): Observable<PolicyItem[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.policyApiService.listPolicies({
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
        const items = (response.results || []).map(r => this.mapDtoToPolicyItem(r));
        this._policies.set(items);
        this._isLoading.set(false);
        return items;
      }),
      catchError(err => {
        console.warn('Backend policies fetch failed, falling back to local cache or defaults:', err.message);
        this._isLoading.set(false);
        this._error.set(err.message || 'Failed to load policies');
        if (this._policies().length === 0) {
          this._policies.set([...INITIAL_POLICIES]);
        }
        return of(this._policies());
      })
    );
  }

  /**
   * Returns all current policies in memory.
   */
  getAll(): PolicyItem[] {
    return this._policies();
  }

  /**
   * Find a policy by ID (matches numeric id, string id or "POL-00X").
   */
  getById(id: string): PolicyItem | undefined {
    if (!id) return undefined;
    const normalized = id.trim().toLowerCase();
    const digits = id.replace(/\D/g, '');
    const num = digits ? parseInt(digits, 10) : NaN;

    return this._policies().find(p =>
      p.id.toLowerCase() === normalized ||
      (p.numericId !== undefined && p.numericId === num) ||
      (`pol-${String(p.numericId || p.id).padStart(3, '0')}`.toLowerCase() === normalized)
    );
  }

  /**
   * Fetch a single policy by ID from the live backend API.
   */
  fetchById(id: string): Observable<PolicyItem | null> {
    return this.policyApiService.getPolicy(id).pipe(
      map(dto => {
        const item = this.mapDtoToPolicyItem(dto);
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
   * Create a new policy via FastAPI backend POST /api/v1/policies.
   */
  createAsync(newPolicy: Omit<PolicyItem, 'updatedAt'>): Observable<PolicyItem> {
    const payload: PolicyCreateDto = {
      title: newPolicy.name,
      description: newPolicy.description,
      category: newPolicy.category,
      department: newPolicy.department,
      ministry: newPolicy.ministry,
      state: newPolicy.state || 'Central',
      sector: newPolicy.sector,
      status: this.mapFrontendStatusToBackend(newPolicy.status),
      is_active: newPolicy.status !== 'Archived'
    };

    return this.policyApiService.createPolicy(payload).pipe(
      map(dto => {
        const createdItem = this.mapDtoToPolicyItem(dto);
        this._policies.update(current => [createdItem, ...current]);
        return createdItem;
      })
    );
  }

  /**
   * Synchronous creation for existing components.
   */
  create(newPolicy: Omit<PolicyItem, 'updatedAt'>): PolicyItem {
    const tempId = `TEMP-${Date.now()}`;
    const today = this.formatDate(new Date());
    const optimisticItem: PolicyItem = {
      ...newPolicy,
      id: tempId,
      updatedAt: today
    };

    // Optimistically add to UI
    this._policies.update(current => [optimisticItem, ...current]);

    // Send to backend
    this.createAsync(newPolicy).subscribe({
      next: (savedItem) => {
        this._policies.update(current =>
          current.map(p => p.id === tempId ? savedItem : p)
        );
      },
      error: (err) => {
        console.error('Failed to create policy on backend:', err);
      }
    });

    return optimisticItem;
  }

  /**
   * Update existing policy via FastAPI backend PUT /api/v1/policies/{id}.
   */
  updateAsync(id: string, updates: Partial<PolicyItem>): Observable<PolicyItem> {
    const payload: PolicyUpdateDto = {
      title: updates.name,
      description: updates.description,
      category: updates.category,
      department: updates.department,
      ministry: updates.ministry,
      state: updates.state,
      sector: updates.sector,
      status: updates.status ? this.mapFrontendStatusToBackend(updates.status) : undefined,
      is_active: updates.status ? updates.status !== 'Archived' : undefined
    };

    return this.policyApiService.updatePolicy(id, payload).pipe(
      map(dto => {
        const updated = this.mapDtoToPolicyItem(dto);
        this.updateLocalState(updated);
        return updated;
      })
    );
  }

  /**
   * Synchronous update for existing components.
   */
  update(id: string, updates: Partial<PolicyItem>): PolicyItem | undefined {
    let found: PolicyItem | undefined;
    const today = this.formatDate(new Date());

    this._policies.update(current =>
      current.map(p => {
        if (p.id.toLowerCase() === id.trim().toLowerCase() || (p.numericId && String(p.numericId) === id)) {
          found = { ...p, ...updates, updatedAt: today };
          return found;
        }
        return p;
      })
    );

    this.updateAsync(id, updates).subscribe({
      next: (synced) => {
        this.updateLocalState(synced);
      },
      error: (err) => {
        console.error('Failed to sync policy update to backend:', err);
      }
    });

    return found;
  }

  /**
   * Submit policy for review POST /api/v1/policies/{id}/submit
   */
  submitForReviewAsync(id: string): Observable<PolicyItem> {
    return this.policyApiService.submitForApproval(id).pipe(
      map(dto => {
        const item = this.mapDtoToPolicyItem(dto);
        this.updateLocalState(item);
        return item;
      })
    );
  }

  /**
   * Synchronous submit for existing components.
   */
  submitForReview(id: string): PolicyItem | undefined {
    const policy = this.getById(id);
    if (!policy) return undefined;

    const today = this.formatDate(new Date());
    const optimistic: PolicyItem = {
      ...policy,
      status: 'Under Review',
      submittedAt: today,
      nextStep: 'Awaiting approval from the designated government official'
    };
    this.updateLocalState(optimistic);

    this.submitForReviewAsync(id).subscribe({
      next: (synced) => this.updateLocalState(synced),
      error: (err) => console.error('Failed to submit policy for review on backend:', err)
    });

    return optimistic;
  }

  /**
   * Approve a pending policy POST /api/v1/policies/{id}/approve
   */
  approvePolicyAsync(id: string, publish: boolean = false): Observable<PolicyItem> {
    return this.policyApiService.approvePolicy(id, { publish }).pipe(
      map(dto => {
        const item = this.mapDtoToPolicyItem(dto);
        this.updateLocalState(item);
        return item;
      })
    );
  }

  /**
   * Reject a pending policy POST /api/v1/policies/{id}/reject
   */
  rejectPolicyAsync(id: string, reason?: string): Observable<PolicyItem> {
    return this.policyApiService.rejectPolicy(id, { reason }).pipe(
      map(dto => {
        const item = this.mapDtoToPolicyItem(dto);
        this.updateLocalState(item);
        return item;
      })
    );
  }

  /**
   * Archive a policy DELETE /api/v1/policies/{id}
   */
  archiveAsync(id: string): Observable<PolicyItem> {
    return this.policyApiService.archivePolicy(id).pipe(
      map(dto => {
        const item = this.mapDtoToPolicyItem(dto);
        this.updateLocalState(item);
        return item;
      })
    );
  }

  /**
   * Synchronous archive for existing components.
   */
  archive(id: string): PolicyItem | undefined {
    const policy = this.getById(id);
    if (!policy) return undefined;

    const optimistic: PolicyItem = {
      ...policy,
      status: 'Archived',
      nextStep: 'Policy archived'
    };
    this.updateLocalState(optimistic);

    this.archiveAsync(id).subscribe({
      next: (synced) => this.updateLocalState(synced),
      error: (err) => console.error('Failed to archive policy on backend:', err)
    });

    return optimistic;
  }

  /**
   * Delete a policy locally or refresh after archive.
   */
  delete(id: string): boolean {
    this.archive(id);
    return true;
  }

  /**
   * Filter and search in-memory policies.
   */
  filterAndSearch(query: string = '', category: string = 'All', status?: string): PolicyItem[] {
    let list = this._policies();

    if (status) {
      list = list.filter(p => p.status.toLowerCase() === status.toLowerCase());
    } else {
      list = list.filter(p => p.status !== 'Archived');
    }

    if (category && category !== 'All') {
      list = list.filter(p => p.category.toLowerCase() === category.toLowerCase());
    }

    if (query && query.trim()) {
      const q = query.trim().toLowerCase();
      list = list.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        p.ministry.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    return list;
  }

  /**
   * Helper to map backend PolicyReadDto to frontend PolicyItem
   */
  public mapDtoToPolicyItem(dto: PolicyReadDto): PolicyItem {
    const status = this.mapBackendStatusToFrontend(dto.status);
    const pubDate = dto.publication_date
      ? this.formatDateString(dto.publication_date)
      : this.formatDateString(dto.created_at);
    const effDate = this.formatDateString(dto.created_at);
    const idStr = String(dto.id);

    return {
      id: idStr,
      numericId: dto.id,
      name: dto.title,
      description: dto.description || '',
      ministry: dto.ministry || 'Ministry of Public Policy',
      department: dto.department || 'Department of Policy Management',
      category: dto.category || 'General',
      sector: dto.sector || dto.category || 'Public Sector',
      state: dto.state || 'Central',
      publicationDate: pubDate,
      effectiveDate: effDate,
      expiryDate: '—',
      tags: [dto.category || 'General', dto.sector || 'Policy'].filter(Boolean),
      document: {
        name: `${dto.title.replace(/[^a-zA-Z0-9_-]/g, '_')}.pdf`,
        size: '2.4 MB',
        type: 'PDF'
      },
      status: status,
      updatedAt: this.formatDateString(dto.updated_at),
      submittedAt: status === 'Under Review' ? this.formatDateString(dto.updated_at) : undefined,
      nextStep: status === 'Under Review'
        ? 'Awaiting approval from the designated government official'
        : (status === 'Archived' ? 'Policy archived' : undefined),
      rejectionReason: dto.rejection_reason || undefined,
      history: this.buildHistory(status, pubDate, dto.rejection_reason)
    };
  }

  private mapBackendStatusToFrontend(status: string): PolicyStatus {
    const clean = status ? status.trim().toUpperCase() : 'DRAFT';
    switch (clean) {
      case 'DRAFT': return 'Draft';
      case 'PENDING_APPROVAL': return 'Under Review';
      case 'APPROVED': return 'Approved';
      case 'PUBLISHED': return 'Published';
      case 'ARCHIVED': return 'Archived';
      case 'REJECTED': return 'Rejected';
      default: return 'Draft';
    }
  }

  private mapFrontendStatusToBackend(status: PolicyStatus | string): string {
    switch (status) {
      case 'Draft': return 'DRAFT';
      case 'Under Review': return 'PENDING_APPROVAL';
      case 'Approved': return 'APPROVED';
      case 'Published': return 'PUBLISHED';
      case 'Archived': return 'ARCHIVED';
      case 'Rejected': return 'REJECTED';
      default: return 'DRAFT';
    }
  }

  private buildHistory(status: PolicyStatus, date: string, rejectionReason?: string | null): PolicyHistoryStep[] {
    return [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: date,
        completed: true,
        current: status === 'Draft'
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: status === 'Under Review' ? 'Awaiting reviewer feedback' : 'Submitted for approval',
        date: date,
        completed: status === 'Approved' || status === 'Published' || status === 'Under Review',
        current: status === 'Under Review'
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: status === 'Published' ? 'Approved by committee' : (status === 'Rejected' ? `Rejected: ${rejectionReason || 'Requires revisions'}` : 'Awaiting approval'),
        date: date,
        completed: status === 'Approved' || status === 'Published',
        current: status === 'Approved'
      },
      {
        status: 'Published',
        label: 'Published',
        description: status === 'Published' ? 'Policy published in national repository' : 'Awaiting publication',
        date: date,
        completed: status === 'Published',
        current: status === 'Published'
      }
    ];
  }

  private updateLocalState(item: PolicyItem): void {
    this._policies.update(current => {
      const idx = current.findIndex(p => p.id === item.id || (p.numericId && p.numericId === item.numericId));
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
