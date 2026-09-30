import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../../../core/services/dashboard.service';
import { GovernmentDashboardResponse } from '../../../models/dashboard.model';
import { KpiCardComponent } from '../components/kpi-card/kpi-card.component';
import { DistributionChartComponent } from '../components/distribution-chart/distribution-chart.component';

@Component({
  selector: 'app-government-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    KpiCardComponent,
    DistributionChartComponent
  ],
  templateUrl: './government-dashboard.component.html',
  styleUrl: './government-dashboard.component.css'
})
export class GovernmentDashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  // Reactive state
  protected readonly loading = signal<boolean>(true);
  protected readonly refreshing = signal<boolean>(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly data = signal<GovernmentDashboardResponse | null>(null);

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

    this.dashboardService.getGovernmentDashboard().subscribe({
      next: (resp: GovernmentDashboardResponse) => {
        this.data.set(resp);
        this.loading.set(false);
        this.refreshing.set(false);
      },
      error: (err: any) => {
        this.loading.set(false);
        this.refreshing.set(false);
        this.errorMessage.set(err.error?.detail || 'Failed to load government official dashboard. Please check connection.');
      }
    });
  }

  get policyPipelineDistribution() {
    const p = this.data()?.policy_statistics;
    if (!p) return [];
    return [
      { name: 'Pending Review', count: p.pending_approval_count },
      { name: 'Draft Stage', count: p.draft_count },
      { name: 'Approved', count: p.approved_count },
      { name: 'Published Active', count: p.published_count },
      { name: 'Rejected', count: p.rejected_count }
    ].filter(i => i.count > 0);
  }

  get schemeStatusDistribution() {
    const s = this.data()?.scheme_usage;
    if (!s) return [];
    return [
      { name: 'Active Programs', count: s.active_count },
      { name: 'Drafts', count: s.draft_count },
      { name: 'Inactive / Pending', count: s.inactive_count },
      { name: 'Archived', count: s.archived_count }
    ].filter(i => i.count > 0);
  }
}
