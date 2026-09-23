import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Policy } from '../policies/services/policy';
import { Scheme } from '../schemes/services/scheme';
import { Auth } from '../../core/services/auth';
import { PolicyItem } from '../../models/policy.model';
import { SchemeItem } from '../../models/scheme.model';

export interface ReviewQueueItem {
  id: string;
  numericId?: number;
  name: string;
  type: 'Policy' | 'Scheme';
  submittedBy: string;
  submittedDate: string;
  status: 'Under Review' | 'Approved' | 'Rejected' | 'Archived' | 'Draft';
  category: string;
  department: string;
  ministry: string;
  sector?: string;
  description: string;
  originalPolicy?: PolicyItem;
  originalScheme?: SchemeItem;
}

export interface ToastAlert {
  type: 'success' | 'error' | 'info';
  text: string;
}

@Component({
  selector: 'app-approvals',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './approvals.html',
  styleUrl: './approvals.css',
})
export class Approvals implements OnInit {
  protected readonly policyService = inject(Policy);
  protected readonly schemeService = inject(Scheme);
  protected readonly auth = inject(Auth);

  // View state: 'dashboard' (Approval Dashboard & Review Queue) or 'review' (Policy Review Screen)
  protected currentView = signal<'dashboard' | 'review'>('dashboard');

  // Currently reviewed item
  protected activeItem = signal<ReviewQueueItem | null>(null);

  // Search & Filters
  protected searchQuery = signal<string>('');
  protected activeTab = signal<string>('All');

  // Pagination
  protected readonly pageSize = 6;
  protected currentPage = signal<number>(1);

  // Decision Modals State
  protected showApproveModal = signal<boolean>(false);
  protected showRejectModal = signal<boolean>(false);
  protected targetModalItem = signal<ReviewQueueItem | null>(null);
  protected publishOnApprove = signal<boolean>(true);
  protected rejectionReason = signal<string>('');
  protected isSubmittingAction = signal<boolean>(false);

  // Document preview modal
  protected showDocModal = signal<boolean>(false);

  // Toast notifications
  protected toast = signal<ToastAlert | null>(null);
  private toastTimer: any = null;

  ngOnInit(): void {
    this.refreshAll();
  }

  refreshAll(): void {
    this.policyService.refreshPolicies().subscribe();
    this.schemeService.refreshSchemes().subscribe();
  }

  // Capability check
  canApproveReject(): boolean {
    return this.auth.canApproveRejectPolicy();
  }

  // Unified items list from both Policy and Scheme signals
  protected queueItems = computed<ReviewQueueItem[]>(() => {
    const policies = this.policyService.policies();
    const schemes = this.schemeService.schemes();

    const policyItems: ReviewQueueItem[] = policies.map(p => ({
      id: p.id,
      numericId: p.numericId,
      name: p.name,
      type: 'Policy',
      submittedBy: 'Government Official',
      submittedDate: p.submittedAt || p.updatedAt || p.publicationDate || 'Recent',
      status: (p.status as any) || 'Draft',
      category: p.category || 'General',
      department: p.department || 'General Administration',
      ministry: p.ministry || 'Ministry of Public Policy',
      sector: p.sector,
      description: p.description,
      originalPolicy: p
    }));

    const schemeItems: ReviewQueueItem[] = schemes.map(s => {
      let mappedStatus: 'Under Review' | 'Approved' | 'Rejected' | 'Archived' | 'Draft' = 'Approved';
      if (s.status === 'Draft') mappedStatus = 'Draft';
      else if (s.status === 'Archived') mappedStatus = 'Archived';
      else if (s.status === 'Active') mappedStatus = 'Approved';
      else if (s.status === 'Under Review') mappedStatus = 'Under Review';

      return {
        id: s.id,
        numericId: s.numericId,
        name: s.name,
        type: 'Scheme',
        submittedBy: 'Government Official',
        submittedDate: s.updatedAt || s.createdAt || s.startDate || 'Recent',
        status: mappedStatus,
        category: s.category || 'Welfare',
        department: s.department || 'Department of Welfare',
        ministry: s.ministry || 'Ministry of Social Justice',
        sector: s.sector,
        description: s.description,
        originalScheme: s
      };
    });

    // Sort: "Under Review" items first, then by date/id
    const combined = [...policyItems, ...schemeItems];
    return combined.sort((a, b) => {
      if (a.status === 'Under Review' && b.status !== 'Under Review') return -1;
      if (b.status === 'Under Review' && a.status !== 'Under Review') return 1;
      return 0;
    });
  });

  // KPI Metrics computed live from queue items
  protected metrics = computed(() => {
    const items = this.queueItems();
    const pendingReview = items.filter(i => i.status === 'Under Review').length;
    const approved = items.filter(i => i.status === 'Approved').length;
    const rejected = items.filter(i => i.status === 'Rejected').length;
    const archived = items.filter(i => i.status === 'Archived').length;

    return {
      pendingReview,
      approved,
      rejected,
      archived
    };
  });

  // Filtered queue based on active tab and search query
  protected filteredQueue = computed(() => {
    let items = this.queueItems();
    const tab = this.activeTab();
    const query = this.searchQuery().trim().toLowerCase();

    // Tab filter
    if (tab === 'Policies') {
      items = items.filter(i => i.type === 'Policy');
    } else if (tab === 'Schemes') {
      items = items.filter(i => i.type === 'Scheme');
    } else if (tab === 'Under Review') {
      items = items.filter(i => i.status === 'Under Review');
    } else if (tab === 'Approved') {
      items = items.filter(i => i.status === 'Approved');
    } else if (tab === 'Rejected') {
      items = items.filter(i => i.status === 'Rejected');
    }

    // Search query filter
    if (query) {
      items = items.filter(i =>
        i.name.toLowerCase().includes(query) ||
        i.id.toLowerCase().includes(query) ||
        i.category.toLowerCase().includes(query) ||
        i.ministry.toLowerCase().includes(query) ||
        i.department.toLowerCase().includes(query) ||
        i.description.toLowerCase().includes(query)
      );
    }

    return items;
  });

  // Paginated queue items
  protected paginatedQueue = computed(() => {
    const all = this.filteredQueue();
    const start = (this.currentPage() - 1) * this.pageSize;
    return all.slice(start, start + this.pageSize);
  });

  // Total pages
  protected totalPages = computed(() => {
    const total = this.filteredQueue().length;
    return Math.max(1, Math.ceil(total / this.pageSize));
  });

  // Showing range
  protected showingRange = computed(() => {
    const total = this.filteredQueue().length;
    if (total === 0) return { start: 0, end: 0, total: 0 };
    const start = (this.currentPage() - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage() * this.pageSize, total);
    return { start, end, total };
  });

  // Pagination array
  protected pagesArray = computed(() => {
    const total = this.totalPages();
    return Array.from({ length: total }, (_, i) => i + 1);
  });

  // Tab Selection
  selectTab(tab: string): void {
    this.activeTab.set(tab);
    this.currentPage.set(1);
  }

  onSearchChange(): void {
    this.currentPage.set(1);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
    }
  }

  // Navigation into Policy Review Screen
  openReview(item: ReviewQueueItem): void {
    this.activeItem.set(item);
    this.currentView.set('review');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  backToQueue(): void {
    this.currentView.set('dashboard');
    this.activeItem.set(null);
  }

  // Direct and modal actions
  openApproveModal(item?: ReviewQueueItem, event?: MouseEvent): void {
    if (event) event.stopPropagation();
    const target = item || this.activeItem();
    if (!target) return;
    this.targetModalItem.set(target);
    this.publishOnApprove.set(true);
    this.showApproveModal.set(true);
  }

  closeApproveModal(): void {
    this.showApproveModal.set(false);
    this.targetModalItem.set(null);
  }

  openRejectModal(item?: ReviewQueueItem, event?: MouseEvent): void {
    if (event) event.stopPropagation();
    const target = item || this.activeItem();
    if (!target) return;
    this.targetModalItem.set(target);
    this.rejectionReason.set('');
    this.showRejectModal.set(true);
  }

  closeRejectModal(): void {
    this.showRejectModal.set(false);
    this.targetModalItem.set(null);
    this.rejectionReason.set('');
  }

  confirmApprove(): void {
    const target = this.targetModalItem();
    if (!target) return;

    this.isSubmittingAction.set(true);
    const publish = this.publishOnApprove();

    if (target.type === 'Policy') {
      this.policyService.approvePolicyAsync(target.id, publish).subscribe({
        next: (updated) => {
          this.isSubmittingAction.set(false);
          this.closeApproveModal();
          this.showToastAlert('success', `Policy "${target.name}" was successfully approved${publish ? ' and published' : ''}!`);
          
          // Update active review item if in review view
          if (this.activeItem()?.id === target.id) {
            this.activeItem.set({
              ...target,
              status: 'Approved',
              originalPolicy: updated
            });
          }
        },
        error: (err) => {
          this.isSubmittingAction.set(false);
          this.closeApproveModal();
          this.showToastAlert('error', `Failed to approve policy: ${err.message || 'Unknown server error'}`);
        }
      });
    } else {
      // Scheme approval
      this.schemeService.updateAsync(target.id, { status: 'Active' }).subscribe({
        next: (updated) => {
          this.isSubmittingAction.set(false);
          this.closeApproveModal();
          this.showToastAlert('success', `Scheme "${target.name}" was successfully approved!`);
          if (this.activeItem()?.id === target.id) {
            this.activeItem.set({
              ...target,
              status: 'Approved',
              originalScheme: updated
            });
          }
        },
        error: (err) => {
          this.isSubmittingAction.set(false);
          this.closeApproveModal();
          this.showToastAlert('error', `Failed to approve scheme: ${err.message || 'Unknown server error'}`);
        }
      });
    }
  }

  confirmReject(): void {
    const target = this.targetModalItem();
    const reason = this.rejectionReason().trim();
    if (!target || !reason) return;

    this.isSubmittingAction.set(true);

    if (target.type === 'Policy') {
      this.policyService.rejectPolicyAsync(target.id, reason).subscribe({
        next: (updated) => {
          this.isSubmittingAction.set(false);
          this.closeRejectModal();
          this.showToastAlert('info', `Policy "${target.name}" was marked as Rejected.`);
          
          if (this.activeItem()?.id === target.id) {
            this.activeItem.set({
              ...target,
              status: 'Rejected',
              originalPolicy: updated
            });
          }
        },
        error: (err) => {
          this.isSubmittingAction.set(false);
          this.closeRejectModal();
          this.showToastAlert('error', `Failed to reject policy: ${err.message || 'Unknown server error'}`);
        }
      });
    } else {
      // Scheme rejection (move to Closed/Draft)
      this.schemeService.updateAsync(target.id, { status: 'Closed' }).subscribe({
        next: (updated) => {
          this.isSubmittingAction.set(false);
          this.closeRejectModal();
          this.showToastAlert('info', `Scheme "${target.name}" was closed.`);
          if (this.activeItem()?.id === target.id) {
            this.activeItem.set({
              ...target,
              status: 'Rejected',
              originalScheme: updated
            });
          }
        },
        error: (err) => {
          this.isSubmittingAction.set(false);
          this.closeRejectModal();
          this.showToastAlert('error', `Failed to update scheme: ${err.message || 'Unknown server error'}`);
        }
      });
    }
  }

  openDocModal(): void {
    this.showDocModal.set(true);
  }

  closeDocModal(): void {
    this.showDocModal.set(false);
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'Under Review':
        return 'badge-under-review';
      case 'Approved':
        return 'badge-approved';
      case 'Rejected':
        return 'badge-rejected';
      case 'Archived':
        return 'badge-archived';
      case 'Draft':
        return 'badge-draft';
      default:
        return 'badge-draft';
    }
  }

  private showToastAlert(type: 'success' | 'error' | 'info', text: string): void {
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toast.set({ type, text });
    this.toastTimer = setTimeout(() => {
      this.toast.set(null);
    }, 4500);
  }
}
