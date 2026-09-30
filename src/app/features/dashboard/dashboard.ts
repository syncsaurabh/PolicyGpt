import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { AuthService } from '../../core/services/auth.service';
import { normalizeRole, Role } from '../../models/role.model';
import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard.component';
import { GovernmentDashboardComponent } from './government-dashboard/government-dashboard.component';
import { CitizenDashboardComponent } from './citizen-dashboard/citizen-dashboard.component';
import { AnalyticsService } from '../../core/services/analytics.service';
import { OverviewAnalyticsResponse } from '../../models/analytics.model';
import { KpiCardComponent } from './components/kpi-card/kpi-card.component';
import { DistributionChartComponent } from './components/distribution-chart/distribution-chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    AdminDashboardComponent,
    GovernmentDashboardComponent,
    CitizenDashboardComponent,
    KpiCardComponent,
    DistributionChartComponent
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  protected readonly auth = inject(Auth);
  private readonly authService = inject(AuthService);
  private readonly analyticsService = inject(AnalyticsService);
  private readonly router = inject(Router);

  // Role tracking
  readonly currentRole = computed(() => {
    const user = this.auth.getCurrentUser();
    if (!user || !user.role) return 'CITIZEN';
    return normalizeRole(user.role);
  });

  // Analytics for Researcher/Organization views
  protected readonly overviewData = signal<OverviewAnalyticsResponse | null>(null);
  protected readonly analyticsLoading = signal<boolean>(false);
  protected readonly analyticsError = signal<string | null>(null);

  ngOnInit(): void {
    // If user is authenticated, refresh latest profile
    if (this.authService.isAuthenticated()) {
      this.authService.fetchProfile().subscribe();
    }

    // If researcher/organization/guest, load platform overview analytics
    if (['RESEARCHER', 'ORGANIZATION', 'GUEST_USER', 'GUEST'].includes(this.currentRole())) {
      this.loadOverviewAnalytics();
    }
  }

  loadOverviewAnalytics(): void {
    this.analyticsLoading.set(true);
    this.analyticsError.set(null);
    this.analyticsService.getOverview().subscribe({
      next: (data) => {
        this.overviewData.set(data);
        this.analyticsLoading.set(false);
      },
      error: (err) => {
        this.analyticsLoading.set(false);
        this.analyticsError.set(err.error?.detail || 'Failed to load platform analytics overview.');
      }
    });
  }
}
