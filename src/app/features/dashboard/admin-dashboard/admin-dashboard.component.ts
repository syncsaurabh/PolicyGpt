import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../../../core/services/dashboard.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { AdminDashboardResponse, AuditLogItem } from '../../../models/dashboard.model';
import { DepartmentAnalyticsResponse, SearchAnalytics } from '../../../models/analytics.model';
import { KpiCardComponent } from '../components/kpi-card/kpi-card.component';
import { DistributionChartComponent } from '../components/distribution-chart/distribution-chart.component';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    KpiCardComponent,
    DistributionChartComponent
  ],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css'
})
export class AdminDashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly analyticsService = inject(AnalyticsService);

  // Reactive state
  protected readonly loading = signal<boolean>(true);
  protected readonly refreshing = signal<boolean>(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly data = signal<AdminDashboardResponse | null>(null);
  protected readonly searchAnalytics = signal<SearchAnalytics | null>(null);
  protected readonly departmentAnalytics = signal<DepartmentAnalyticsResponse | null>(null);

  ngOnInit(): void {
    this.loadData();
  }

  loadData(isRefresh = false): void {
    if (isRefresh) {
      this.refreshing.set(true);
    } else {
      this.loading.set(true);
    }
    this.errorMessage.set(null);

    this.dashboardService.getAdminDashboard().subscribe({
      next: (resp: AdminDashboardResponse) => {
        this.data.set(resp);
        this.loading.set(false);
        this.refreshing.set(false);
      },
      error: (err: any) => {
        this.loading.set(false);
        this.refreshing.set(false);
        this.errorMessage.set(err.error?.detail || 'Failed to load administrator dashboard data. Please check connection.');
      }
    });

    // Optional auxiliary analytics
    this.analyticsService.getSearch().subscribe({
      next: (s: SearchAnalytics) => this.searchAnalytics.set(s),
      error: () => {}
    });

    this.analyticsService.getDepartments().subscribe({
      next: (d: DepartmentAnalyticsResponse) => this.departmentAnalytics.set(d),
      error: () => {}
    });
  }

  get policyStatusDistribution() {
    const p = this.data()?.policy_management;
    if (!p) return [];
    return [
      { name: 'Published', count: p.published_count },
      { name: 'Pending Approval', count: p.pending_approval_count },
      { name: 'Drafts', count: p.draft_count },
      { name: 'Approved', count: p.approved_count },
      { name: 'Rejected', count: p.rejected_count },
      { name: 'Archived', count: p.archived_count }
    ].filter(i => i.count > 0);
  }

  formatDate(dateStr?: string | null): string {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }
}
