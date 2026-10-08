import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../../../core/services/dashboard.service';
import { AuditLogItem } from '../../../models/dashboard.model';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-logs.html',
  styleUrl: './audit-logs.css',
})
export class AuditLogs implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  // Reactive State
  protected readonly auditLogs = signal<AuditLogItem[]>([]);
  protected readonly loading = signal<boolean>(true);
  protected readonly refreshing = signal<boolean>(false);
  protected readonly errorMessage = signal<string | null>(null);

  // Search & Filter State
  protected readonly searchQuery = signal<string>('');
  protected readonly selectedAction = signal<string>('All');
  protected readonly selectedEntityType = signal<string>('All');
  protected readonly selectedActor = signal<string>('All');

  // Pagination State
  protected readonly currentPage = signal<number>(1);
  protected readonly pageSize = signal<number>(10);
  protected readonly pageSizeOptions = [10, 20, 50, 100];

  // Modal State
  protected readonly activeLogModal = signal<AuditLogItem | null>(null);
  protected readonly copiedToast = signal<boolean>(false);

  ngOnInit(): void {
    this.fetchAuditLogs();
  }

  fetchAuditLogs(isRefresh = false): void {
    if (isRefresh) {
      this.refreshing.set(true);
    } else {
      this.loading.set(true);
    }
    this.errorMessage.set(null);

    this.dashboardService.getAdminDashboard().subscribe({
      next: (res) => {
        this.auditLogs.set(res.audit_logs || []);
        this.loading.set(false);
        this.refreshing.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.refreshing.set(false);
        this.errorMessage.set(
          err.error?.detail || 'Failed to load audit logs. Please try again.'
        );
      }
    });
  }

  // Dynamic filter option lists computed from data
  protected readonly distinctActions = computed(() => {
    const set = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.action) set.add(log.action);
    }
    return ['All', ...Array.from(set).sort()];
  });

  protected readonly distinctEntityTypes = computed(() => {
    const set = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.entity_type) set.add(log.entity_type);
    }
    return ['All', ...Array.from(set).sort()];
  });

  protected readonly distinctActors = computed(() => {
    const set = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.user_email) set.add(log.user_email);
    }
    return ['All', ...Array.from(set).sort()];
  });

  // Metrics KPI Computed
  protected readonly totalCount = computed(() => this.auditLogs().length);

  protected readonly uniqueActorsCount = computed(() => {
    const actors = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.user_email) actors.add(log.user_email);
    }
    return actors.size;
  });

  protected readonly actionTypesCount = computed(() => {
    const actions = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.action) actions.add(log.action);
    }
    return actions.size;
  });

  protected readonly uniqueEntitiesCount = computed(() => {
    const entities = new Set<string>();
    for (const log of this.auditLogs()) {
      if (log.entity_type) {
        entities.add(`${log.entity_type}:${log.entity_id || ''}`);
      }
    }
    return entities.size;
  });

  // Active filters flag
  protected readonly hasActiveFilters = computed(() => {
    return (
      this.searchQuery().trim() !== '' ||
      this.selectedAction() !== 'All' ||
      this.selectedEntityType() !== 'All' ||
      this.selectedActor() !== 'All'
    );
  });

  // Filtered dataset
  protected readonly filteredLogs = computed(() => {
    const query = this.searchQuery().trim().toLowerCase();
    const action = this.selectedAction();
    const entityType = this.selectedEntityType();
    const actor = this.selectedActor();

    return this.auditLogs().filter((log) => {
      // Action match
      if (action !== 'All' && log.action !== action) {
        return false;
      }

      // Entity type match
      if (entityType !== 'All' && log.entity_type !== entityType) {
        return false;
      }

      // Actor match
      if (actor !== 'All' && log.user_email !== actor) {
        return false;
      }

      // Search query across multiple fields
      if (query) {
        const email = (log.user_email || '').toLowerCase();
        const act = (log.action || '').toLowerCase();
        const entType = (log.entity_type || '').toLowerCase();
        const entId = (log.entity_id || '').toLowerCase();
        const ip = (log.ip_address || '').toLowerCase();
        const details = (log.details || '').toLowerCase();
        const id = String(log.id);

        const match =
          email.includes(query) ||
          act.includes(query) ||
          entType.includes(query) ||
          entId.includes(query) ||
          ip.includes(query) ||
          details.includes(query) ||
          id.includes(query);

        if (!match) return false;
      }

      return true;
    });
  });

  // Paginated dataset
  protected readonly totalPages = computed(() => {
    const total = this.filteredLogs().length;
    return Math.max(1, Math.ceil(total / this.pageSize()));
  });

  protected readonly paginatedLogs = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize();
    return this.filteredLogs().slice(start, start + this.pageSize());
  });

  protected readonly paginationSummary = computed(() => {
    const total = this.filteredLogs().length;
    if (total === 0) return 'Showing 0 of 0 logs';
    const start = (this.currentPage() - 1) * this.pageSize() + 1;
    const end = Math.min(start + this.pageSize() - 1, total);
    return `Showing ${start}-${end} of ${total} logs`;
  });

  // Filter handlers
  onFilterChange(): void {
    this.currentPage.set(1);
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.selectedAction.set('All');
    this.selectedEntityType.set('All');
    this.selectedActor.set('All');
    this.currentPage.set(1);
  }

  // Pagination handlers
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
    }
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update((p) => p + 1);
    }
  }

  prevPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update((p) => p - 1);
    }
  }

  onPageSizeChange(size: number): void {
    this.pageSize.set(size);
    this.currentPage.set(1);
  }

  // Modal View Details
  openLogModal(log: AuditLogItem): void {
    this.activeLogModal.set(log);
  }

  closeLogModal(): void {
    this.activeLogModal.set(null);
  }

  copyLogJson(log: AuditLogItem): void {
    try {
      const dataStr = JSON.stringify(log, null, 2);
      navigator.clipboard.writeText(dataStr).then(() => {
        this.copiedToast.set(true);
        setTimeout(() => this.copiedToast.set(false), 2000);
      });
    } catch {}
  }

  // Export to CSV
  exportToCsv(): void {
    const logs = this.filteredLogs();
    if (logs.length === 0) return;

    const headers = ['ID', 'Timestamp', 'Actor Email', 'User ID', 'Action', 'Entity Type', 'Entity ID', 'IP Address', 'Details'];
    const rows = logs.map((l) => [
      l.id,
      `"${this.formatDate(l.created_at)}"`,
      `"${l.user_email || 'System'}"`,
      l.user_id || '',
      `"${l.action}"`,
      `"${l.entity_type || ''}"`,
      `"${l.entity_id || ''}"`,
      `"${l.ip_address || ''}"`,
      `"${(l.details || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Formatting helpers
  formatDate(dateStr: string | undefined): string {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return dateStr;
    }
  }

  formatRelativeDate(dateStr: string | undefined): string {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return '';
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return '';
    } catch {
      return '';
    }
  }

  getActionBadgeClass(action: string): string {
    const act = (action || '').toUpperCase();
    if (act.includes('CREATE') || act.includes('RESOLVED') || act.includes('APPROVED')) {
      return 'action-badge badge-success';
    }
    if (act.includes('UPDATE') || act.includes('EDIT')) {
      return 'action-badge badge-info';
    }
    if (act.includes('PUBLISH')) {
      return 'action-badge badge-purple';
    }
    if (act.includes('SUBMIT') || act.includes('REVIEW') || act.includes('PENDING')) {
      return 'action-badge badge-warning';
    }
    if (act.includes('DELETE') || act.includes('ARCHIVE') || act.includes('REJECT') || act.includes('FAIL')) {
      return 'action-badge badge-danger';
    }
    return 'action-badge badge-neutral';
  }
}
