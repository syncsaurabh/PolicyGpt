import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReportsService } from '../../core/services/reports.service';
import {
  DepartmentReportParams,
  ExportFormat,
  PolicyReportParams,
  ReportDataResponse,
  ReportHistoryParams,
  ReportRead,
  SchemeReportParams,
  UserActivityReportParams,
} from '../../models/reports.model';

export type ReportTab = 'policies' | 'schemes' | 'departments' | 'user-activity' | 'history';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reports.html',
  styleUrl: './reports.css',
})
export class Reports implements OnInit {
  private readonly reportsService = inject(ReportsService);

  // Active Tab
  activeTab = signal<ReportTab>('policies');

  // Common Loading & Error States
  isLoading = signal<boolean>(false);
  isExporting = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  exportSuccessMsg = signal<string | null>(null);

  // --- 1. Policy Report State ---
  policyReport = signal<ReportDataResponse | null>(null);
  policyStartDate = signal<string>('');
  policyEndDate = signal<string>('');
  policyDepartment = signal<string>('');
  policyCategory = signal<string>('');
  policyState = signal<string>('');
  policyStatus = signal<string>('ALL');

  // --- 2. Scheme Report State ---
  schemeReport = signal<ReportDataResponse | null>(null);
  schemeStartDate = signal<string>('');
  schemeEndDate = signal<string>('');
  schemeDepartment = signal<string>('');
  schemeCategory = signal<string>('');
  schemeState = signal<string>('');
  schemeStatus = signal<string>('ALL');

  // --- 3. Department Report State ---
  departmentReport = signal<ReportDataResponse | null>(null);
  deptFilterName = signal<string>('');

  // --- 4. User Activity Report State ---
  activityReport = signal<ReportDataResponse | null>(null);
  activityStartDate = signal<string>('');
  activityEndDate = signal<string>('');
  activityEventType = signal<string>('ALL');

  // --- 5. Report History State ---
  historyList = signal<ReportRead[]>([]);
  historyPage = signal<number>(1);
  historyPageSize = signal<number>(10);
  historyTotalPages = signal<number>(1);
  historyTotalCount = signal<number>(0);
  historyTypeFilter = signal<string>('ALL');

  ngOnInit(): void {
    this.loadActiveTabReport();
  }

  setTab(tab: ReportTab): void {
    if (this.activeTab() !== tab) {
      this.activeTab.set(tab);
      this.errorMessage.set(null);
      this.exportSuccessMsg.set(null);
      this.loadActiveTabReport();
    }
  }

  loadActiveTabReport(): void {
    switch (this.activeTab()) {
      case 'policies':
        this.loadPolicyReport();
        break;
      case 'schemes':
        this.loadSchemeReport();
        break;
      case 'departments':
        this.loadDepartmentReport();
        break;
      case 'user-activity':
        this.loadUserActivityReport();
        break;
      case 'history':
        this.loadHistoryReport();
        break;
    }
  }

  // --- 1. Load Policy Report ---
  loadPolicyReport(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: PolicyReportParams = {
      start_date: this.policyStartDate() || undefined,
      end_date: this.policyEndDate() || undefined,
      department: this.policyDepartment() || undefined,
      category: this.policyCategory() || undefined,
      state: this.policyState() || undefined,
      status_filter: this.policyStatus() !== 'ALL' ? this.policyStatus() : undefined,
    };

    this.reportsService.getPolicyReport(params).subscribe({
      next: (res) => {
        this.policyReport.set(res);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to generate policy dataset report.'));
      },
    });
  }

  resetPolicyFilters(): void {
    this.policyStartDate.set('');
    this.policyEndDate.set('');
    this.policyDepartment.set('');
    this.policyCategory.set('');
    this.policyState.set('');
    this.policyStatus.set('ALL');
    this.loadPolicyReport();
  }

  exportPolicy(format: ExportFormat): void {
    this.isExporting.set(true);
    this.exportSuccessMsg.set(null);
    this.errorMessage.set(null);

    const params = {
      start_date: this.policyStartDate() || undefined,
      end_date: this.policyEndDate() || undefined,
      department: this.policyDepartment() || undefined,
      category: this.policyCategory() || undefined,
      state: this.policyState() || undefined,
      status_filter: this.policyStatus() !== 'ALL' ? this.policyStatus() : undefined,
      format,
    };

    this.reportsService.exportPolicyReport(params).subscribe({
      next: (response) => {
        this.isExporting.set(false);
        const ext = format === 'excel' || format === 'xlsx' ? 'xlsx' : 'pdf';
        this.reportsService.saveBlobFile(response, `policies_report_${Date.now()}.${ext}`);
        this.exportSuccessMsg.set(`Policy report exported as ${format.toUpperCase()} successfully.`);
      },
      error: (err) => {
        this.isExporting.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to export policy report.'));
      },
    });
  }

  // --- 2. Load Scheme Report ---
  loadSchemeReport(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: SchemeReportParams = {
      start_date: this.schemeStartDate() || undefined,
      end_date: this.schemeEndDate() || undefined,
      department: this.schemeDepartment() || undefined,
      category: this.schemeCategory() || undefined,
      state: this.schemeState() || undefined,
      status_filter: this.schemeStatus() !== 'ALL' ? this.schemeStatus() : undefined,
    };

    this.reportsService.getSchemeReport(params).subscribe({
      next: (res) => {
        this.schemeReport.set(res);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to generate scheme dataset report.'));
      },
    });
  }

  resetSchemeFilters(): void {
    this.schemeStartDate.set('');
    this.schemeEndDate.set('');
    this.schemeDepartment.set('');
    this.schemeCategory.set('');
    this.schemeState.set('');
    this.schemeStatus.set('ALL');
    this.loadSchemeReport();
  }

  exportScheme(format: ExportFormat): void {
    this.isExporting.set(true);
    this.exportSuccessMsg.set(null);
    this.errorMessage.set(null);

    const params = {
      start_date: this.schemeStartDate() || undefined,
      end_date: this.schemeEndDate() || undefined,
      department: this.schemeDepartment() || undefined,
      category: this.schemeCategory() || undefined,
      state: this.schemeState() || undefined,
      status_filter: this.schemeStatus() !== 'ALL' ? this.schemeStatus() : undefined,
      format,
    };

    this.reportsService.exportSchemeReport(params).subscribe({
      next: (response) => {
        this.isExporting.set(false);
        const ext = format === 'excel' || format === 'xlsx' ? 'xlsx' : 'pdf';
        this.reportsService.saveBlobFile(response, `schemes_report_${Date.now()}.${ext}`);
        this.exportSuccessMsg.set(`Scheme report exported as ${format.toUpperCase()} successfully.`);
      },
      error: (err) => {
        this.isExporting.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to export scheme report.'));
      },
    });
  }

  // --- 3. Load Department Report ---
  loadDepartmentReport(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: DepartmentReportParams = {
      department: this.deptFilterName() || undefined,
    };

    this.reportsService.getDepartmentReport(params).subscribe({
      next: (res) => {
        this.departmentReport.set(res);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to generate department metrics report.'));
      },
    });
  }

  resetDepartmentFilters(): void {
    this.deptFilterName.set('');
    this.loadDepartmentReport();
  }

  exportDepartment(format: ExportFormat): void {
    this.isExporting.set(true);
    this.exportSuccessMsg.set(null);
    this.errorMessage.set(null);

    const params = {
      department: this.deptFilterName() || undefined,
      format,
    };

    this.reportsService.exportDepartmentReport(params).subscribe({
      next: (response) => {
        this.isExporting.set(false);
        const ext = format === 'excel' || format === 'xlsx' ? 'xlsx' : 'pdf';
        this.reportsService.saveBlobFile(response, `department_report_${Date.now()}.${ext}`);
        this.exportSuccessMsg.set(`Department report exported as ${format.toUpperCase()} successfully.`);
      },
      error: (err) => {
        this.isExporting.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to export department report.'));
      },
    });
  }

  // --- 4. Load User Activity Report ---
  loadUserActivityReport(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: UserActivityReportParams = {
      start_date: this.activityStartDate() || undefined,
      end_date: this.activityEndDate() || undefined,
      event_type: this.activityEventType() !== 'ALL' ? this.activityEventType() : undefined,
    };

    this.reportsService.getUserActivityReport(params).subscribe({
      next: (res) => {
        this.activityReport.set(res);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to generate user activity log report.'));
      },
    });
  }

  resetActivityFilters(): void {
    this.activityStartDate.set('');
    this.activityEndDate.set('');
    this.activityEventType.set('ALL');
    this.loadUserActivityReport();
  }

  exportUserActivity(format: ExportFormat): void {
    this.isExporting.set(true);
    this.exportSuccessMsg.set(null);
    this.errorMessage.set(null);

    const params = {
      start_date: this.activityStartDate() || undefined,
      end_date: this.activityEndDate() || undefined,
      event_type: this.activityEventType() !== 'ALL' ? this.activityEventType() : undefined,
      format,
    };

    this.reportsService.exportUserActivityReport(params).subscribe({
      next: (response) => {
        this.isExporting.set(false);
        const ext = format === 'excel' || format === 'xlsx' ? 'xlsx' : 'pdf';
        this.reportsService.saveBlobFile(response, `user_activity_report_${Date.now()}.${ext}`);
        this.exportSuccessMsg.set(`User activity report exported as ${format.toUpperCase()} successfully.`);
      },
      error: (err) => {
        this.isExporting.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to export user activity report.'));
      },
    });
  }

  // --- 5. Load Report History ---
  loadHistoryReport(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: ReportHistoryParams = {
      page: this.historyPage(),
      page_size: this.historyPageSize(),
      report_type: this.historyTypeFilter() !== 'ALL' ? this.historyTypeFilter() : undefined,
    };

    this.reportsService.getReportsHistory(params).subscribe({
      next: (res) => {
        this.historyList.set(res.results || []);
        this.historyPage.set(res.page || 1);
        this.historyPageSize.set(res.page_size || 10);
        this.historyTotalPages.set(res.total_pages || 1);
        this.historyTotalCount.set(res.total_count || 0);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to load report history.'));
      },
    });
  }

  onHistoryFilterChange(): void {
    this.historyPage.set(1);
    this.loadHistoryReport();
  }

  goToHistoryPage(pageNum: number): void {
    if (pageNum >= 1 && pageNum <= this.historyTotalPages() && pageNum !== this.historyPage()) {
      this.historyPage.set(pageNum);
      this.loadHistoryReport();
    }
  }

  // --- UI Helpers ---
  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }

  getStatusBadgeClass(status: string | undefined): string {
    switch (status?.toUpperCase()) {
      case 'PUBLISHED':
      case 'APPROVED':
      case 'ACTIVE':
      case 'SUCCESS':
      case 'COMPLETED':
        return 'badge-success';
      case 'PENDING_APPROVAL':
      case 'UNDER_REVIEW':
      case 'IN_PROGRESS':
        return 'badge-info';
      case 'DRAFT':
      case 'INACTIVE':
        return 'badge-warning';
      case 'REJECTED':
      case 'ARCHIVED':
      case 'FAILED':
        return 'badge-danger';
      default:
        return 'badge-neutral';
    }
  }

  private formatApiError(err: any, defaultMsg: string): string {
    if (!err) return defaultMsg;
    const detail = err?.error?.detail;
    if (!detail) return err.message || defaultMsg;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d?.msg || d?.message || JSON.stringify(d)).join('; ');
    }
    if (typeof detail === 'object') {
      return detail.msg || detail.message || JSON.stringify(detail);
    }
    return String(detail);
  }
}
