import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { SchemeEligibilityResult } from '../../../../models/dashboard.model';

@Component({
  selector: 'app-application-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './application-modal.component.html',
  styleUrl: './application-modal.component.css'
})
export class ApplicationModalComponent {
  private readonly dashboardService = inject(DashboardService);

  @Input() isOpen: boolean = false;
  @Input() selectedScheme: SchemeEligibilityResult | null = null;
  @Input() availableSchemes: SchemeEligibilityResult[] = [];

  @Output() close = new EventEmitter<void>();
  @Output() applicationSubmitted = new EventEmitter<void>();

  schemeId: number | null = null;
  remarks: string = '';
  submitting: boolean = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  ngOnChanges(): void {
    if (this.selectedScheme) {
      this.schemeId = this.selectedScheme.scheme_id;
    } else if (this.availableSchemes.length > 0 && !this.schemeId) {
      this.schemeId = this.availableSchemes[0].scheme_id;
    }
  }

  onSubmit(): void {
    if (!this.schemeId) {
      this.errorMessage = 'Please select a scheme to apply for.';
      return;
    }

    this.submitting = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.dashboardService.submitSchemeApplication({
      scheme_id: this.schemeId,
      remarks: this.remarks.trim() || undefined,
      details_json: JSON.stringify({
        submitted_via: 'Citizen Dashboard Portal',
        timestamp: new Date().toISOString()
      })
    }).subscribe({
      next: (res) => {
        this.submitting = false;
        this.successMessage = `Application ${res.application_number} submitted successfully!`;
        setTimeout(() => {
          this.applicationSubmitted.emit();
          this.onClose();
        }, 1200);
      },
      error: (err) => {
        this.submitting = false;
        this.errorMessage = err.error?.detail || 'Failed to submit scheme application. Please try again.';
      }
    });
  }

  onClose(): void {
    this.remarks = '';
    this.errorMessage = null;
    this.successMessage = null;
    this.close.emit();
  }
}
