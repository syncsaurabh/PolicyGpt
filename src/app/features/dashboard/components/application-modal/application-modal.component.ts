import { Component, EventEmitter, Input, Output, inject, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApplicationService } from '../../../../core/services/application.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ApplicationReadDto } from '../../../../models/application.model';
import { SchemeEligibilityResult } from '../../../../models/dashboard.model';

@Component({
  selector: 'app-application-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './application-modal.component.html',
  styleUrl: './application-modal.component.css'
})
export class ApplicationModalComponent implements OnInit, OnChanges {
  private readonly applicationService = inject(ApplicationService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  @Input() isOpen: boolean = false;
  @Input() selectedScheme: SchemeEligibilityResult | { scheme_id?: number; id?: string | number; name?: string; scheme_name?: string; department?: string; benefits?: string; category?: string } | null = null;
  @Input() availableSchemes: (SchemeEligibilityResult | any)[] = [];

  @Output() close = new EventEmitter<void>();
  @Output() applicationSubmitted = new EventEmitter<ApplicationReadDto>();

  // Multi-step form: 'form' -> 'review' -> 'success'
  currentStep: 'form' | 'review' | 'success' = 'form';

  // Form Fields
  schemeId: number | null = null;
  applicantName: string = '';
  applicantEmail: string = '';
  applicantPhone: string = '';
  applicantState: string = '';
  applicantAadhaar: string = '';
  annualIncome: string = '';
  category: string = 'General';
  remarks: string = '';
  agreeDeclaration: boolean = true;

  // Submitting and Result State
  submitting: boolean = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;
  createdApplication: ApplicationReadDto | null = null;
  copiedId: boolean = false;

  ngOnInit(): void {
    this.populateUserProfile();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['isOpen'] && this.isOpen) {
      this.resetFlow();
      this.populateUserProfile();
    }
    this.resolveSchemeId();
  }

  private populateUserProfile(): void {
    const user = this.authService.getCurrentUser();
    if (user) {
      this.applicantName = user.name || '';
      this.applicantEmail = user.email || '';
      this.applicantPhone = (user as any).phone_number || '';
      this.applicantState = (user as any).state || '';
    }
  }

  private resolveSchemeId(): void {
    if (this.selectedScheme) {
      const s = this.selectedScheme as any;
      this.schemeId = s.scheme_id || (typeof s.id === 'number' ? s.id : parseInt(String(s.id).replace(/\D/g, ''), 10)) || null;
    } else if (this.availableSchemes && this.availableSchemes.length > 0 && !this.schemeId) {
      const first = this.availableSchemes[0];
      this.schemeId = first.scheme_id || (typeof first.id === 'number' ? first.id : parseInt(String(first.id).replace(/\D/g, ''), 10)) || null;
    }
  }

  get selectedSchemeObject(): any {
    if (this.selectedScheme) {
      return this.selectedScheme;
    }
    if (this.schemeId && this.availableSchemes) {
      return this.availableSchemes.find(
        (s: any) =>
          s.scheme_id === this.schemeId ||
          s.id === this.schemeId ||
          parseInt(String(s.id).replace(/\D/g, ''), 10) === this.schemeId
      );
    }
    return null;
  }

  get selectedSchemeDisplayName(): string {
    const s = this.selectedSchemeObject;
    return s?.scheme_name || s?.name || (this.schemeId ? `Scheme #${this.schemeId}` : 'Selected Scheme');
  }

  get selectedSchemeDepartment(): string {
    const s = this.selectedSchemeObject;
    return s?.department || 'Department of Public Welfare';
  }

  get selectedSchemeBenefits(): string {
    const s = this.selectedSchemeObject;
    return s?.benefits || 'Financial assistance and welfare provisions as per guidelines';
  }

  goToReview(): void {
    if (!this.schemeId) {
      this.errorMessage = 'Please select a scheme to apply for.';
      return;
    }
    if (!this.applicantName.trim()) {
      this.errorMessage = 'Please provide applicant full name.';
      return;
    }
    if (!this.agreeDeclaration) {
      this.errorMessage = 'You must confirm the truthfulness declaration before proceeding.';
      return;
    }

    this.errorMessage = null;
    this.currentStep = 'review';
  }

  backToForm(): void {
    this.currentStep = 'form';
    this.errorMessage = null;
  }

  onSubmit(): void {
    if (!this.schemeId) {
      this.errorMessage = 'Please select a scheme to apply for.';
      return;
    }

    this.submitting = true;
    this.errorMessage = null;

    const details = {
      applicant_name: this.applicantName.trim(),
      applicant_email: this.applicantEmail.trim(),
      applicant_phone: this.applicantPhone.trim(),
      applicant_state: this.applicantState.trim(),
      applicant_aadhaar_last4: this.applicantAadhaar.trim().slice(-4) || undefined,
      annual_income: this.annualIncome.trim() || undefined,
      category: this.category,
      declaration_accepted: true,
      submitted_at: new Date().toISOString()
    };

    this.applicationService.createApplication({
      scheme_id: this.schemeId,
      remarks: this.remarks.trim() || undefined,
      details_json: JSON.stringify(details)
    }).subscribe({
      next: (res: ApplicationReadDto) => {
        this.submitting = false;
        this.createdApplication = res;
        this.currentStep = 'success';
        this.applicationSubmitted.emit(res);
      },
      error: (err: any) => {
        this.submitting = false;
        this.errorMessage = err.error?.detail || 'Failed to submit scheme application. Please verify details and try again.';
      }
    });
  }

  copyAppId(): void {
    if (this.createdApplication?.application_number) {
      navigator.clipboard.writeText(this.createdApplication.application_number);
      this.copiedId = true;
      setTimeout(() => (this.copiedId = false), 2500);
    }
  }

  viewInDashboard(): void {
    this.onClose();
    this.router.navigate(['/dashboard/citizen'], { queryParams: { tab: 'applications' } });
  }

  resetFlow(): void {
    this.currentStep = 'form';
    this.remarks = '';
    this.errorMessage = null;
    this.successMessage = null;
    this.createdApplication = null;
    this.copiedId = false;
  }

  onClose(): void {
    this.resetFlow();
    this.close.emit();
  }

  formatDate(dateStr?: string): string {
    if (!dateStr) return new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
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
