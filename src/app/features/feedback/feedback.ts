import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Auth } from '../../core/services/auth';
import { FeedbackService } from '../../core/services/feedback.service';
import {
  AdminFeedbackListParams,
  FeedbackCreate,
  FeedbackHistoryItem,
  FeedbackPriority,
  FeedbackRead,
  FeedbackResolve,
  FeedbackStatus,
  FeedbackType,
  FeedbackUpdate,
  MyFeedbackListParams,
} from '../../models/feedback.model';
import { Role } from '../../models/role.model';

@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './feedback.html',
  styleUrl: './feedback.css',
})
export class Feedback implements OnInit {
  protected readonly auth = inject(Auth);
  private readonly feedbackService = inject(FeedbackService);

  // Enum references for template bindings
  readonly FeedbackType = FeedbackType;
  readonly FeedbackPriority = FeedbackPriority;
  readonly FeedbackStatus = FeedbackStatus;

  // Role Checks
  get isOfficialOrAdmin(): boolean {
    return this.auth.hasRole([Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL]);
  }

  // Active Scope for Admins: 'my' | 'all'
  activeScope = signal<'my' | 'all'>('my');

  // Feedback types list for dropdowns
  readonly typeOptions: { label: string; value: FeedbackType }[] = [
    { label: 'General Feedback', value: FeedbackType.FEEDBACK },
    { label: 'Technical Issue / Bug', value: FeedbackType.ISSUE },
    { label: 'Support Request', value: FeedbackType.SUPPORT },
    { label: 'General Inquiry', value: FeedbackType.INQUIRY },
    { label: 'Feature Suggestion', value: FeedbackType.SUGGESTION },
    { label: 'Grievance / Complaint', value: FeedbackType.COMPLAINT },
  ];

  readonly priorityOptions: { label: string; value: FeedbackPriority }[] = [
    { label: 'Low', value: FeedbackPriority.LOW },
    { label: 'Medium', value: FeedbackPriority.MEDIUM },
    { label: 'High', value: FeedbackPriority.HIGH },
    { label: 'Urgent', value: FeedbackPriority.URGENT },
  ];

  readonly statusOptions: { label: string; value: string }[] = [
    { label: 'All Statuses', value: 'ALL' },
    { label: 'Open', value: FeedbackStatus.OPEN },
    { label: 'Submitted', value: FeedbackStatus.SUBMITTED },
    { label: 'In Progress', value: FeedbackStatus.IN_PROGRESS },
    { label: 'In Review', value: FeedbackStatus.IN_REVIEW },
    { label: 'Resolved', value: FeedbackStatus.RESOLVED },
    { label: 'Closed', value: FeedbackStatus.CLOSED },
  ];

  // --- Tickets List State ---
  tickets = signal<FeedbackRead[]>([]);
  totalCount = signal<number>(0);
  page = signal<number>(1);
  pageSize = signal<number>(10);
  totalPages = signal<number>(1);
  isLoading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  // Filters State
  selectedStatus = signal<string>('ALL');
  selectedType = signal<string>('ALL');
  selectedPriority = signal<string>('ALL');
  categoryFilter = signal<string>('');

  // --- Create Feedback Modal State ---
  showCreateModal = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);
  submitErrorMsg = signal<string | null>(null);
  submitSuccessMsg = signal<string | null>(null);

  // Form Fields
  formSubject = signal<string>('');
  formContent = signal<string>('');
  formFeedbackType = signal<FeedbackType>(FeedbackType.FEEDBACK);
  formPriority = signal<FeedbackPriority>(FeedbackPriority.MEDIUM);
  formCategory = signal<string>('');
  formReferenceId = signal<string>('');
  formRating = signal<number | null>(null);

  // --- Ticket Detail & History Drawer State ---
  showDetailDrawer = signal<boolean>(false);
  selectedTicket = signal<FeedbackRead | null>(null);
  isLoadingDetails = signal<boolean>(false);
  detailsErrorMsg = signal<string | null>(null);

  ticketHistory = signal<FeedbackHistoryItem[]>([]);
  isLoadingHistory = signal<boolean>(false);
  historyErrorMsg = signal<string | null>(null);

  // --- Admin Triage & Resolution State ---
  editStatus = signal<FeedbackStatus>(FeedbackStatus.IN_PROGRESS);
  editPriority = signal<FeedbackPriority>(FeedbackPriority.MEDIUM);
  isUpdatingTriage = signal<boolean>(false);
  triageSuccessMsg = signal<string | null>(null);
  triageErrorMsg = signal<string | null>(null);

  adminResolutionNote = signal<string>('');
  isResolving = signal<boolean>(false);
  resolveSuccessMsg = signal<string | null>(null);
  resolveErrorMsg = signal<string | null>(null);

  ngOnInit(): void {
    if (this.isOfficialOrAdmin) {
      this.activeScope.set('all');
    }
    this.loadTickets();
  }

  setScope(scope: 'my' | 'all'): void {
    if (this.activeScope() !== scope) {
      this.activeScope.set(scope);
      this.page.set(1);
      this.loadTickets();
    }
  }

  /**
   * Load tickets based on current role and active scope
   */
  loadTickets(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const baseParams: MyFeedbackListParams = {
      page: this.page(),
      page_size: this.pageSize(),
      status: this.selectedStatus(),
      feedback_type: this.selectedType(),
      priority: this.selectedPriority(),
      category: this.categoryFilter(),
    };

    const request$ =
      this.isOfficialOrAdmin && this.activeScope() === 'all'
        ? this.feedbackService.getAllFeedback(baseParams as AdminFeedbackListParams)
        : this.feedbackService.getMyFeedback(baseParams);

    request$.subscribe({
      next: (res) => {
        this.tickets.set(res.results || []);
        this.totalCount.set(res.total_count || 0);
        this.page.set(res.page || 1);
        this.pageSize.set(res.page_size || 10);
        this.totalPages.set(res.total_pages || 1);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.formatApiError(err, 'Failed to load support tickets. Please try again.'));
      },
    });
  }

  // --- Filter and Pagination Actions ---
  onFilterChange(): void {
    this.page.set(1);
    this.loadTickets();
  }

  resetFilters(): void {
    this.selectedStatus.set('ALL');
    this.selectedType.set('ALL');
    this.selectedPriority.set('ALL');
    this.categoryFilter.set('');
    this.page.set(1);
    this.loadTickets();
  }

  goToPage(pageNum: number): void {
    if (pageNum >= 1 && pageNum <= this.totalPages() && pageNum !== this.page()) {
      this.page.set(pageNum);
      this.loadTickets();
    }
  }

  // --- Modal Operations ---
  openCreateModal(): void {
    this.resetForm();
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    if (!this.isSubmitting()) {
      this.showCreateModal.set(false);
      this.resetForm();
    }
  }

  resetForm(): void {
    this.formSubject.set('');
    this.formContent.set('');
    this.formFeedbackType.set(FeedbackType.FEEDBACK);
    this.formPriority.set(FeedbackPriority.MEDIUM);
    this.formCategory.set('');
    this.formReferenceId.set('');
    this.formRating.set(null);
    this.submitErrorMsg.set(null);
    this.submitSuccessMsg.set(null);
  }

  setRating(stars: number): void {
    if (this.formRating() === stars) {
      this.formRating.set(null);
    } else {
      this.formRating.set(stars);
    }
  }

  /**
   * Submit new citizen feedback / support request
   */
  submitFeedback(): void {
    const subject = this.formSubject().trim();
    if (!subject) {
      this.submitErrorMsg.set('Please provide a subject for your request.');
      return;
    }

    const content = this.formContent().trim();
    if (!content) {
      this.submitErrorMsg.set('Please provide details or a description for your request.');
      return;
    }

    this.isSubmitting.set(true);
    this.submitErrorMsg.set(null);
    this.submitSuccessMsg.set(null);

    const payload: FeedbackCreate = {
      subject,
      content,
      description: content,
      feedback_type: this.formFeedbackType(),
      type: this.formFeedbackType(),
      priority: this.formPriority(),
      category: this.formCategory().trim() || null,
      reference_id: this.formReferenceId().trim() || null,
      rating: this.formRating(),
    };

    this.feedbackService.submitFeedback(payload).subscribe({
      next: (res) => {
        this.isSubmitting.set(false);
        this.submitSuccessMsg.set(`Ticket #${res.id} submitted successfully!`);
        setTimeout(() => {
          this.closeCreateModal();
          this.loadTickets();
        }, 1200);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.submitErrorMsg.set(this.formatApiError(err, 'Failed to submit feedback. Please check your input.'));
      },
    });
  }

  // --- Ticket Details & History Drawer ---
  viewTicketDetails(ticket: FeedbackRead): void {
    this.selectedTicket.set(ticket);
    this.showDetailDrawer.set(true);
    this.detailsErrorMsg.set(null);
    this.historyErrorMsg.set(null);
    this.triageSuccessMsg.set(null);
    this.triageErrorMsg.set(null);
    this.resolveSuccessMsg.set(null);
    this.resolveErrorMsg.set(null);
    this.adminResolutionNote.set('');

    // Pre-populate admin triage dropdowns
    this.editStatus.set(this.parseFeedbackStatus(ticket.status));
    this.editPriority.set(this.parseFeedbackPriority(ticket.priority));

    // Fetch fresh details by ID
    this.isLoadingDetails.set(true);
    this.feedbackService.getFeedbackById(ticket.id).subscribe({
      next: (freshTicket) => {
        this.selectedTicket.set(freshTicket);
        this.editStatus.set(this.parseFeedbackStatus(freshTicket.status));
        this.editPriority.set(this.parseFeedbackPriority(freshTicket.priority));
        this.isLoadingDetails.set(false);
      },
      error: (err) => {
        this.isLoadingDetails.set(false);
        this.detailsErrorMsg.set(this.formatApiError(err, 'Unable to load ticket details.'));
      },
    });

    // Fetch live lifecycle history
    this.refreshTicketHistory(ticket.id);
  }

  private refreshTicketHistory(ticketId: number): void {
    this.isLoadingHistory.set(true);
    this.feedbackService.getFeedbackHistory(ticketId).subscribe({
      next: (historyRes) => {
        this.ticketHistory.set(historyRes.history || []);
        this.isLoadingHistory.set(false);
      },
      error: (err) => {
        this.isLoadingHistory.set(false);
        this.historyErrorMsg.set(this.formatApiError(err, 'Unable to load ticket history.'));
      },
    });
  }

  closeTicketDetails(): void {
    this.showDetailDrawer.set(false);
    this.selectedTicket.set(null);
    this.ticketHistory.set([]);
  }

  // --- Admin Status / Priority Triage Action ---
  updateTicketTriage(): void {
    const ticket = this.selectedTicket();
    if (!ticket) return;

    this.isUpdatingTriage.set(true);
    this.triageSuccessMsg.set(null);
    this.triageErrorMsg.set(null);

    const payload: FeedbackUpdate = {
      status: this.editStatus(),
      priority: this.editPriority(),
    };

    this.feedbackService.updateFeedbackStatus(ticket.id, payload).subscribe({
      next: (updated) => {
        this.isUpdatingTriage.set(false);
        this.selectedTicket.set(updated);
        this.triageSuccessMsg.set('Ticket status & priority updated successfully.');
        this.refreshTicketHistory(ticket.id);
        this.loadTickets();
      },
      error: (err) => {
        this.isUpdatingTriage.set(false);
        this.triageErrorMsg.set(this.formatApiError(err, 'Failed to update ticket status.'));
      },
    });
  }

  // --- Admin Resolve Action ---
  resolveTicket(): void {
    const ticket = this.selectedTicket();
    if (!ticket) return;

    const resolution = this.adminResolutionNote().trim();
    if (!resolution) {
      this.resolveErrorMsg.set('Please provide official resolution remarks or notes.');
      return;
    }

    this.isResolving.set(true);
    this.resolveSuccessMsg.set(null);
    this.resolveErrorMsg.set(null);

    const payload: FeedbackResolve = {
      admin_response: resolution,
      resolution: resolution,
      status: FeedbackStatus.RESOLVED,
    };

    this.feedbackService.resolveFeedback(ticket.id, payload).subscribe({
      next: (resolved) => {
        this.isResolving.set(false);
        this.selectedTicket.set(resolved);
        this.editStatus.set(FeedbackStatus.RESOLVED);
        this.resolveSuccessMsg.set('Ticket marked as Resolved and official response posted!');
        this.adminResolutionNote.set('');
        this.refreshTicketHistory(ticket.id);
        this.loadTickets();
      },
      error: (err) => {
        this.isResolving.set(false);
        this.resolveErrorMsg.set(this.formatApiError(err, 'Failed to post resolution.'));
      },
    });
  }

  // --- Badges and UI Helpers ---
  getStatusBadgeClass(status: string): string {
    switch (status?.toUpperCase()) {
      case 'RESOLVED':
      case 'CLOSED':
        return 'badge-success';
      case 'IN_PROGRESS':
      case 'IN_REVIEW':
        return 'badge-info';
      case 'OPEN':
      case 'SUBMITTED':
      default:
        return 'badge-warning';
    }
  }

  getPriorityBadgeClass(priority: string): string {
    switch (priority?.toUpperCase()) {
      case 'URGENT':
        return 'badge-danger';
      case 'HIGH':
        return 'badge-warning';
      case 'MEDIUM':
        return 'badge-primary';
      case 'LOW':
      default:
        return 'badge-neutral';
    }
  }

  getTypeIcon(type: string): string {
    switch (type?.toUpperCase()) {
      case 'ISSUE':
        return 'bug_report';
      case 'SUPPORT':
        return 'contact_support';
      case 'INQUIRY':
        return 'help_outline';
      case 'SUGGESTION':
        return 'lightbulb';
      case 'COMPLAINT':
        return 'report_problem';
      case 'FEEDBACK':
      default:
        return 'rate_review';
    }
  }

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

  /**
   * Parse error payloads safely to human-readable text
   */
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

  private parseFeedbackStatus(statusStr: string): FeedbackStatus {
    const upper = statusStr?.toUpperCase();
    if (Object.values(FeedbackStatus).includes(upper as FeedbackStatus)) {
      return upper as FeedbackStatus;
    }
    return FeedbackStatus.OPEN;
  }

  private parseFeedbackPriority(prioStr: string): FeedbackPriority {
    const upper = prioStr?.toUpperCase();
    if (Object.values(FeedbackPriority).includes(upper as FeedbackPriority)) {
      return upper as FeedbackPriority;
    }
    return FeedbackPriority.MEDIUM;
  }
}
