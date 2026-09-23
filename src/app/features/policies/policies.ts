import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Policy } from './services/policy';
import { PolicyItem, PolicyStatus } from '../../models/policy.model';
import { Auth } from '../../core/services/auth';

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

  ngOnInit(): void {
    this.policyService.refreshPolicies().subscribe();
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
