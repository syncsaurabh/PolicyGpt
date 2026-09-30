import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { DashboardService } from '../../../core/services/dashboard.service';
import {
  ApplicationStatusItem,
  CitizenDashboardResponse,
  CitizenNotificationItem,
  CitizenSearchHistoryItem,
  SavedPolicyItem,
  SchemeEligibilityResult
} from '../../../models/dashboard.model';
import { KpiCardComponent } from '../components/kpi-card/kpi-card.component';
import { ApplicationModalComponent } from '../components/application-modal/application-modal.component';

@Component({
  selector: 'app-citizen-dashboard-feature',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    KpiCardComponent,
    ApplicationModalComponent
  ],
  templateUrl: './citizen-dashboard.component.html',
  styleUrl: './citizen-dashboard.component.css'
})
export class CitizenDashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly router = inject(Router);

  // Reactive state
  protected readonly loading = signal<boolean>(true);
  protected readonly refreshing = signal<boolean>(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly successToast = signal<string | null>(null);
  protected readonly data = signal<CitizenDashboardResponse | null>(null);

  // Active section tab
  protected activeTab = signal<'eligible' | 'saved' | 'applications' | 'notifications' | 'history'>('eligible');

  // Application Modal state
  protected isAppModalOpen = signal<boolean>(false);
  protected selectedSchemeForApp = signal<SchemeEligibilityResult | null>(null);

  // Deleting bookmark state
  protected deletingPolicyId = signal<number | null>(null);

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

    this.dashboardService.getCitizenDashboard().subscribe({
      next: (resp: CitizenDashboardResponse) => {
        this.data.set(resp);
        this.loading.set(false);
        this.refreshing.set(false);
      },
      error: (err: any) => {
        this.loading.set(false);
        this.refreshing.set(false);
        this.errorMessage.set(err.error?.detail || 'Failed to load citizen dashboard data. Please check connection.');
      }
    });
  }

  setTab(tab: 'eligible' | 'saved' | 'applications' | 'notifications' | 'history'): void {
    this.activeTab.set(tab);
  }

  openApplicationModal(scheme?: SchemeEligibilityResult): void {
    this.selectedSchemeForApp.set(scheme || null);
    this.isAppModalOpen.set(true);
  }

  closeApplicationModal(): void {
    this.isAppModalOpen.set(false);
    this.selectedSchemeForApp.set(null);
  }

  onApplicationSubmitted(): void {
    this.showToast('Scheme application submitted successfully!');
    this.loadData(true);
  }

  isSchemeBookmarked(schemeId: number): boolean {
    const saved = this.data()?.saved_policies;
    if (!saved || saved.length === 0) return false;
    return saved.some(
      (s: SavedPolicyItem) =>
        s.scheme_id === schemeId ||
        (s.item_type === 'scheme' && s.id === schemeId) ||
        s.policy_id === schemeId
    );
  }

  toggleSchemeBookmark(scheme: SchemeEligibilityResult, event?: Event): void {
    if (event) event.stopPropagation();

    const isBookmarked = this.isSchemeBookmarked(scheme.scheme_id);
    if (isBookmarked) {
      // Find matching item
      const saved = this.data()?.saved_policies;
      const match = saved?.find(
        (s: SavedPolicyItem) =>
          s.scheme_id === scheme.scheme_id ||
          s.policy_id === scheme.scheme_id ||
          s.id === scheme.scheme_id
      );
      const targetId = match?.scheme_id || match?.policy_id || scheme.scheme_id;
      this.removeBookmark(targetId);
    } else {
      // Add bookmark
      this.dashboardService.savePolicy({ scheme_id: scheme.scheme_id }).subscribe({
        next: (savedItem: SavedPolicyItem) => {
          this.showToast(`"${scheme.scheme_name}" added to saved bookmarks!`);
          const current = this.data();
          if (current) {
            const currentSaved = current.saved_policies || [];
            const newItem: SavedPolicyItem = {
              id: savedItem.id || Date.now(),
              scheme_id: scheme.scheme_id,
              policy_id: null,
              item_type: 'scheme',
              title: scheme.scheme_name,
              category: scheme.category || 'General Welfare',
              department: scheme.department || null,
              status: 'ACTIVE',
              saved_at: new Date().toISOString()
            };
            this.data.set({
              ...current,
              saved_policies: [newItem, ...currentSaved]
            });
          }
        },
        error: (err: any) => {
          this.errorMessage.set(err.error?.detail || 'Failed to save scheme bookmark.');
        }
      });
    }
  }

  removeBookmark(targetId: number, event?: Event): void {
    if (event) event.stopPropagation();
    if (!confirm('Are you sure you want to remove this bookmark?')) return;

    this.deletingPolicyId.set(targetId);
    this.dashboardService.removeSavedPolicy(targetId).subscribe({
      next: () => {
        this.deletingPolicyId.set(null);
        this.showToast('Bookmark removed successfully.');
        // Optimistically update local data
        const current = this.data();
        if (current && current.saved_policies) {
          const updated = current.saved_policies.filter(
            (p: SavedPolicyItem) =>
              p.policy_id !== targetId &&
              p.scheme_id !== targetId &&
              p.id !== targetId
          );
          this.data.set({ ...current, saved_policies: updated });
        }
      },
      error: (err: any) => {
        this.deletingPolicyId.set(null);
        this.errorMessage.set(err.error?.detail || 'Failed to remove saved bookmark.');
      }
    });
  }

  repeatSearch(query: string): void {
    this.router.navigate(['/policies'], { queryParams: { keyword: query } });
  }

  showToast(msg: string): void {
    this.successToast.set(msg);
    setTimeout(() => this.successToast.set(null), 4000);
  }

  formatDate(dateStr?: string | null): string {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  }

  get unreadNotificationsCount(): number {
    return this.data()?.recent_notifications?.filter((n: CitizenNotificationItem) => !n.is_read).length || 0;
  }
}
