import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApplicationService } from '../../../../core/services/application.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ApplicationReadDto, ApplicationStatus } from '../../../../models/application.model';
import { UserRole } from '../../../../models/user.models';

@Component({
  selector: 'app-application-details-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './application-details-modal.component.html',
  styleUrl: './application-details-modal.component.css'
})
export class ApplicationDetailsModalComponent {
  private readonly applicationService = inject(ApplicationService);
  protected readonly authService = inject(AuthService);

  @Input() isOpen: boolean = false;
  @Input() application: ApplicationReadDto | any = null;

  @Output() close = new EventEmitter<void>();
  @Output() statusUpdated = new EventEmitter<ApplicationReadDto>();
  @Output() applicationWithdrawn = new EventEmitter<ApplicationReadDto>();

  // Decision state for Admin / Official
  protected selectedStatus: ApplicationStatus = 'UNDER_REVIEW';
  protected remarksInput: string = '';
  protected rejectionReasonInput: string = '';
  protected isUpdating: boolean = false;
  protected errorMessage: string | null = null;
  protected successMessage: string | null = null;

  // Withdraw state for Citizen
  protected isWithdrawing: boolean = false;
  protected showWithdrawConfirm: boolean = false;
  protected withdrawReason: string = '';

  get isOfficialOrAdmin(): boolean {
    return this.authService.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL, 'ADMIN', 'GOVERNMENT']);
  }

  get isCitizen(): boolean {
    const role = this.authService.getCurrentUser()?.role;
    return role === (UserRole.CITIZEN as any) || (role as string) === 'CITIZEN' || this.authService.hasRole([UserRole.CITIZEN, 'CITIZEN']);
  }

  get parsedDetails(): Record<string, any> {
    if (!this.application?.details_json) return {};
    try {
      if (typeof this.application.details_json === 'object') return this.application.details_json;
      return JSON.parse(this.application.details_json);
    } catch {
      return {};
    }
  }

  get canWithdraw(): boolean {
    if (!this.application) return false;
    const s = String(this.application.status).toUpperCase();
    return (s === 'SUBMITTED' || s === 'UNDER_REVIEW') && !this.isOfficialOrAdmin;
  }

  updateStatus(): void {
    if (!this.application?.id) return;

    if (this.selectedStatus === 'REJECTED' && !this.rejectionReasonInput.trim() && !this.remarksInput.trim()) {
      this.errorMessage = 'Please provide a rejection reason.';
      return;
    }

    this.isUpdating = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.applicationService.updateStatus(this.application.id, {
      status: this.selectedStatus,
      remarks: this.remarksInput.trim() || undefined,
      rejection_reason: this.rejectionReasonInput.trim() || undefined
    }).subscribe({
      next: (updated) => {
        this.isUpdating = false;
        this.application = updated;
        this.successMessage = `Application status updated to ${updated.status}!`;
        this.statusUpdated.emit(updated);
        setTimeout(() => (this.successMessage = null), 3000);
      },
      error: (err) => {
        this.isUpdating = false;
        this.errorMessage = err.error?.detail || 'Failed to update application status.';
      }
    });
  }

  confirmWithdraw(): void {
    if (!this.application?.id) return;
    this.isWithdrawing = true;
    this.errorMessage = null;

    this.applicationService.withdrawApplication(this.application.id, {
      reason: this.withdrawReason.trim() || undefined
    }).subscribe({
      next: (updated) => {
        this.isWithdrawing = false;
        this.showWithdrawConfirm = false;
        this.application = updated;
        this.applicationWithdrawn.emit(updated);
        this.successMessage = 'Application withdrawn successfully.';
      },
      error: (err) => {
        this.isWithdrawing = false;
        this.errorMessage = err.error?.detail || 'Failed to withdraw application.';
      }
    });
  }

  getStatusClass(status?: string): string {
    const s = String(status || 'submitted').toLowerCase().replace('_', '-');
    return `status-${s}`;
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
      return String(dateStr);
    }
  }

  onClose(): void {
    this.errorMessage = null;
    this.successMessage = null;
    this.showWithdrawConfirm = false;
    this.close.emit();
  }
}
