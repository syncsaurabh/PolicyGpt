import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Scheme } from './services/scheme';
import { SchemeItem, SchemeStatus, SCHEME_CATEGORIES, SCHEME_STATES } from '../../models/scheme.model';
import { Auth } from '../../core/services/auth';

@Component({
  selector: 'app-schemes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './schemes.html',
  styleUrl: './schemes.css',
})
export class Schemes implements OnInit {
  private readonly router = inject(Router);
  protected readonly schemeService = inject(Scheme);
  protected readonly auth = inject(Auth);

  ngOnInit(): void {
    this.schemeService.refreshSchemes().subscribe();
  }

  // Search & Filter State
  protected searchQuery = signal<string>('');
  protected selectedCategory = signal<string>('All');
  protected selectedState = signal<string>('All');
  protected selectedMinistry = signal<string>('All');
  protected selectedDepartment = signal<string>('All');
  protected selectedStatus = signal<string>('All');
  protected showArchived = signal<boolean>(false);

  canCreateScheme(): boolean {
    return this.auth.canCreateScheme();
  }

  canEditScheme(): boolean {
    return this.auth.canEditScheme();
  }

  canArchiveScheme(): boolean {
    return this.auth.canArchiveScheme();
  }

  // Modal State for Delete/Archive confirmation
  protected confirmModalScheme = signal<SchemeItem | null>(null);
  protected isDeleting = signal<boolean>(false);

  // Categories list
  protected readonly categories: string[] = ['All', ...SCHEME_CATEGORIES];

  // States list
  protected readonly states: string[] = ['All', ...SCHEME_STATES];

  // Dynamic Ministries list from current data
  protected readonly ministries = computed(() => {
    const all = this.schemeService.getAll();
    const set = new Set<string>();
    all.forEach(s => {
      if (s.ministry) set.add(s.ministry);
    });
    return ['All', ...Array.from(set).sort()];
  });

  // Dynamic Departments list from current data
  protected readonly departments = computed(() => {
    const all = this.schemeService.getAll();
    const set = new Set<string>();
    all.forEach(s => {
      if (s.department) set.add(s.department);
    });
    return ['All', ...Array.from(set).sort()];
  });

  // Statuses list
  protected readonly statuses: string[] = ['All', 'Active', 'Draft', 'Under Review', 'Closed'];

  // Pagination State
  protected readonly pageSize = 5;
  protected currentPage = signal<number>(1);

  // Active action menu row ID
  protected activeMenuSchemeId = signal<string | null>(null);

  // Active filters check
  protected hasActiveFilters = computed(() => {
    return (
      this.searchQuery().trim() !== '' ||
      this.selectedCategory() !== 'All' ||
      this.selectedState() !== 'All' ||
      this.selectedMinistry() !== 'All' ||
      this.selectedDepartment() !== 'All' ||
      this.selectedStatus() !== 'All'
    );
  });

  // Computed filtered schemes
  protected filteredSchemes = computed(() => {
    const query = this.searchQuery().trim();
    const cat = this.selectedCategory();
    const st = this.selectedState();
    const min = this.selectedMinistry();
    const dept = this.selectedDepartment();
    const isArchived = this.showArchived();

    let statusParam: string | undefined;
    if (isArchived) {
      statusParam = 'Archived';
    } else if (this.selectedStatus() !== 'All') {
      statusParam = this.selectedStatus();
    }

    return this.schemeService.filterAndSearch(
      query,
      cat,
      st,
      min,
      dept,
      statusParam
    );
  });

  // Paginated schemes
  protected paginatedSchemes = computed(() => {
    const all = this.filteredSchemes();
    const start = (this.currentPage() - 1) * this.pageSize;
    return all.slice(start, start + this.pageSize);
  });

  // Total pages
  protected totalPages = computed(() => {
    const total = this.filteredSchemes().length;
    return Math.max(1, Math.ceil(total / this.pageSize));
  });

  // Showing range calculation
  protected showingRange = computed(() => {
    const total = this.filteredSchemes().length;
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
    this.activeMenuSchemeId.set(null);
  }

  onFilterChange(): void {
    this.currentPage.set(1);
    this.activeMenuSchemeId.set(null);
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.selectedCategory.set('All');
    this.selectedState.set('All');
    this.selectedMinistry.set('All');
    this.selectedDepartment.set('All');
    this.selectedStatus.set('All');
    this.currentPage.set(1);
    this.activeMenuSchemeId.set(null);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
      this.activeMenuSchemeId.set(null);
    }
  }

  toggleArchivedView(): void {
    this.showArchived.update(v => !v);
    this.currentPage.set(1);
    this.activeMenuSchemeId.set(null);
  }

  toggleActionMenu(schemeId: string, event: MouseEvent): void {
    event.stopPropagation();
    if (this.activeMenuSchemeId() === schemeId) {
      this.activeMenuSchemeId.set(null);
    } else {
      this.activeMenuSchemeId.set(schemeId);
    }
  }

  closeActionMenu(): void {
    this.activeMenuSchemeId.set(null);
  }

  navigateToCreate(): void {
    this.router.navigate(['/schemes/create']);
  }

  navigateToDetails(scheme: SchemeItem): void {
    this.closeActionMenu();
    this.router.navigate(['/schemes', scheme.id]);
  }

  navigateToEdit(scheme: SchemeItem): void {
    this.closeActionMenu();
    this.router.navigate(['/schemes', scheme.id, 'edit']);
  }

  openConfirmModal(scheme: SchemeItem, event?: MouseEvent): void {
    if (event) {
      event.stopPropagation();
    }
    this.closeActionMenu();
    this.confirmModalScheme.set(scheme);
  }

  closeConfirmModal(): void {
    this.confirmModalScheme.set(null);
    this.isDeleting.set(false);
  }

  confirmArchiveOrDelete(): void {
    const s = this.confirmModalScheme();
    if (!s) return;

    this.isDeleting.set(true);
    if (s.status === 'Archived') {
      this.schemeService.delete(s.id);
    } else {
      this.schemeService.archive(s.id);
    }
    this.closeConfirmModal();
  }

  restoreScheme(scheme: SchemeItem, event?: MouseEvent): void {
    if (event) {
      event.stopPropagation();
    }
    this.closeActionMenu();
    this.schemeService.restore(scheme.id);
  }

  getStatusClass(status: SchemeStatus): string {
    switch (status) {
      case 'Active':
        return 'badge-published'; // green badge
      case 'Under Review':
        return 'badge-under-review'; // amber badge
      case 'Draft':
        return 'badge-draft'; // slate badge
      case 'Closed':
        return 'badge-closed'; // red/gray badge
      case 'Archived':
        return 'badge-archived'; // outline badge
      default:
        return 'badge-draft';
    }
  }
}
