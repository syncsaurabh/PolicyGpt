import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Policy } from './services/policy';
import { PolicyItem, PolicyStatus } from '../../models/policy.model';
import { Auth } from '../../core/services/auth';
import { DashboardService } from '../../core/services/dashboard.service';

@Component({
  selector: 'app-policies',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './policies.html',
  styleUrl: './policies.css',
})
export class Policies implements OnInit {
  private readonly router = inject(Router);
  protected readonly policyService = inject(Policy);
  protected readonly auth = inject(Auth);
  protected readonly dashboardService = inject(DashboardService);

  // Bookmarked policy IDs
  protected bookmarkedPolicyIds = signal<Set<string>>(new Set());

  ngOnInit(): void {
    this.policyService.refreshPolicies().subscribe();
    this.initBookmarks();
  }

  private initBookmarks(): void {
    try {
      const stored = localStorage.getItem('policy_bookmarks');
      if (stored) {
        this.bookmarkedPolicyIds.set(new Set(JSON.parse(stored)));
      }
    } catch {}

    if (this.auth.isAuthenticated()) {
      this.dashboardService.getCitizenDashboard().subscribe({
        next: (dash) => {
          if (dash.saved_policies) {
            const set = new Set(this.bookmarkedPolicyIds());
            dash.saved_policies.forEach(sp => {
              if (sp.policy_id) set.add(String(sp.policy_id));
              if (sp.id) set.add(String(sp.id));
            });
            this.bookmarkedPolicyIds.set(set);
            try {
              localStorage.setItem('policy_bookmarks', JSON.stringify(Array.from(set)));
            } catch {}
          }
        },
        error: () => {}
      });
    }
  }

  isPolicyBookmarked(policyId: string | number): boolean {
    const idStr = String(policyId);
    const numDigits = idStr.replace(/\D/g, '');
    return this.bookmarkedPolicyIds().has(idStr) || (numDigits ? this.bookmarkedPolicyIds().has(numDigits) : false);
  }

  toggleBookmarkPolicy(policy: PolicyItem, event: Event): void {
    event.stopPropagation();
    this.closeActionMenu();

    const idStr = String(policy.id);
    const numId = typeof policy.id === 'number' ? policy.id : parseInt(String(policy.id).replace(/\D/g, ''), 10);
    const currentlyBookmarked = this.isPolicyBookmarked(policy.id);
    const set = new Set(this.bookmarkedPolicyIds());

    if (currentlyBookmarked) {
      set.delete(idStr);
      if (numId) set.delete(String(numId));
      this.bookmarkedPolicyIds.set(set);
      try {
        localStorage.setItem('policy_bookmarks', JSON.stringify(Array.from(set)));
      } catch {}

      if (numId && this.auth.isAuthenticated()) {
        this.dashboardService.removeSavedPolicy(numId).subscribe({
          next: () => {},
          error: () => {}
        });
      }
    } else {
      set.add(idStr);
      if (numId) set.add(String(numId));
      this.bookmarkedPolicyIds.set(set);
      try {
        localStorage.setItem('policy_bookmarks', JSON.stringify(Array.from(set)));
      } catch {}

      if (numId && this.auth.isAuthenticated()) {
        this.dashboardService.savePolicy({ policy_id: numId }).subscribe({
          next: () => {},
          error: () => {}
        });
      }
    }
  }

  // Search & Filter State
  protected searchQuery = signal<string>('');
  protected selectedCategory = signal<string>('All');
  protected showArchived = signal<boolean>(false);

  canCreatePolicy(): boolean {
    return this.auth.canCreatePolicy();
  }

  canEditPolicy(): boolean {
    return this.auth.canEditPolicy();
  }

  canSubmitPolicy(): boolean {
    return this.auth.canSubmitPolicy();
  }

  canArchivePolicy(): boolean {
    return this.auth.canArchivePolicy();
  }

  // Categories list
  protected readonly categories: string[] = [
    'All',
    'Education',
    'Healthcare',
    'Agriculture',
    'Employment',
    'Finance',
    'Housing'
  ];

  // Pagination State
  protected readonly pageSize = 5;
  protected currentPage = signal<number>(1);

  // Active action menu row ID
  protected activeMenuPolicyId = signal<string | null>(null);

  // Computed filtered policies
  protected filteredPolicies = computed(() => {
    const query = this.searchQuery().trim();
    const cat = this.selectedCategory();
    const isArchived = this.showArchived();

    return this.policyService.filterAndSearch(
      query,
      cat,
      isArchived ? 'Archived' : undefined
    );
  });

  // Paginated policies
  protected paginatedPolicies = computed(() => {
    const all = this.filteredPolicies();
    const start = (this.currentPage() - 1) * this.pageSize;
    return all.slice(start, start + this.pageSize);
  });

  // Total pages
  protected totalPages = computed(() => {
    const total = this.filteredPolicies().length;
    return Math.max(1, Math.ceil(total / this.pageSize));
  });

  // Showing range calculation
  protected showingRange = computed(() => {
    const total = this.filteredPolicies().length;
    if (total === 0) return { start: 0, end: 0, total: 0 };
    const start = (this.currentPage() - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage() * this.pageSize, total);
    return { start, end, total };
  });

  // Pages array for pagination controls
  protected pagesArray = computed(() => {
    const total = this.totalPages();
    return Array.from({ length: total }, (_, i) => i + 1);
  });

  selectCategory(category: string): void {
    this.selectedCategory.set(category);
    this.currentPage.set(1);
    this.activeMenuPolicyId.set(null);
  }

  onSearchChange(): void {
    this.currentPage.set(1);
    this.activeMenuPolicyId.set(null);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
      this.activeMenuPolicyId.set(null);
    }
  }

  toggleArchivedView(): void {
    this.showArchived.update(v => !v);
    this.currentPage.set(1);
    this.activeMenuPolicyId.set(null);
  }

  toggleActionMenu(policyId: string, event: MouseEvent): void {
    event.stopPropagation();
    if (this.activeMenuPolicyId() === policyId) {
      this.activeMenuPolicyId.set(null);
    } else {
      this.activeMenuPolicyId.set(policyId);
    }
  }

  closeActionMenu(): void {
    this.activeMenuPolicyId.set(null);
  }

  navigateToUpload(): void {
    this.router.navigate(['/policies/upload']);
  }

  navigateToDetails(policy: PolicyItem): void {
    this.closeActionMenu();
    this.router.navigate(['/policies', policy.id]);
  }

  navigateToEdit(policy: PolicyItem): void {
    this.closeActionMenu();
    this.router.navigate(['/policies', policy.id, 'edit']);
  }

  navigateToSubmit(policy: PolicyItem): void {
    this.closeActionMenu();
    this.router.navigate(['/policies', policy.id, 'submit']);
  }

  navigateToStatus(policy: PolicyItem): void {
    this.closeActionMenu();
    this.router.navigate(['/policies', policy.id, 'status']);
  }

  navigateToArchive(policy: PolicyItem): void {
    this.closeActionMenu();
    this.router.navigate(['/policies', policy.id, 'archive']);
  }

  getStatusClass(status: PolicyStatus): string {
    switch (status) {
      case 'Published':
        return 'badge-published';
      case 'Approved':
        return 'badge-approved';
      case 'Under Review':
        return 'badge-under-review';
      case 'Draft':
        return 'badge-draft';
      case 'Archived':
        return 'badge-archived';
      default:
        return 'badge-draft';
    }
  }
}
