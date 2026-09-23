import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Scheme } from '../services/scheme';
import {
  SchemeCategory,
  SchemeItem,
  SchemeStatus,
  SCHEME_CATEGORIES,
  SCHEME_STATES
} from '../../../models/scheme.model';

@Component({
  selector: 'app-create-scheme',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-scheme.html',
  styleUrl: './create-scheme.css',
})
export class CreateScheme {
  private readonly router = inject(Router);
  private readonly schemeService = inject(Scheme);

  // Form Fields
  schemeName = signal<string>('');
  schemeId = signal<string>(this.generateSuggestedId());
  description = signal<string>('');
  category = signal<SchemeCategory>('Scholarships');
  ministry = signal<string>('Ministry of Education');
  department = signal<string>('Department of School Education & Literacy');
  state = signal<string>('Central / All India');
  benefits = signal<string>('');
  eligibilityCriteria = signal<string>('');
  applicationProcess = signal<string>('');
  applicationUrl = signal<string>('');
  startDate = signal<string>(this.formatDateForInput(new Date()));
  endDate = signal<string>('Ongoing');
  status = signal<SchemeStatus>('Active');
  tags = signal<string>('');

  // UI state
  errorMessage = signal<string>('');
  isSubmitting = signal<boolean>(false);

  // Options
  readonly categories = SCHEME_CATEGORIES;
  readonly states = SCHEME_STATES;

  readonly ministries = [
    'Ministry of Agriculture & Farmers Welfare',
    'Ministry of Health & Family Welfare',
    'Ministry of Education',
    'Ministry of Housing & Urban Affairs',
    'Ministry of Finance',
    'Ministry of Rural Development',
    'Ministry of Women and Child Development',
    'Ministry of Labour and Employment',
    'Ministry of Social Justice & Empowerment',
    'Ministry of Micro, Small and Medium Enterprises',
    'Ministry of Skill Development & Entrepreneurship',
    'Ministry of Electronics & IT'
  ];

  readonly departments = [
    'Department of School Education & Literacy',
    'Department of Higher Education',
    'Department of Agriculture & Farmers Welfare',
    'National Health Authority',
    'Department of Health & Family Welfare',
    'Urban Housing Mission Division',
    'Department of Financial Services',
    'Department of Rural Development',
    'Department of Women & Child Development',
    'Department of Employment & Training',
    'Department of Empowerment of Persons with Disabilities',
    'Pension Fund Regulatory and Development Authority (PFRDA)'
  ];

  readonly statuses: SchemeStatus[] = ['Active', 'Draft', 'Under Review', 'Closed'];

  private generateSuggestedId(): string {
    const existing = this.schemeService.getAll();
    const count = existing.length + 1;
    return `SCH-${String(count).padStart(3, '0')}`;
  }

  private formatDateForInput(d: Date): string {
    const day = String(d.getDate()).padStart(2, '0');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[d.getMonth()];
    const year = d.getFullYear();
    return `${day} ${month} ${year}`;
  }

  cancel(): void {
    this.router.navigate(['/schemes']);
  }

  saveAsDraft(): void {
    this.processSubmission('Draft');
  }

  submitScheme(): void {
    this.processSubmission(this.status());
  }

  private processSubmission(targetStatus: SchemeStatus): void {
    // Form Validations
    if (!this.schemeName().trim()) {
      this.errorMessage.set('Scheme Name is required.');
      return;
    }
    if (!this.schemeId().trim()) {
      this.errorMessage.set('Scheme ID is required.');
      return;
    }
    if (!this.description().trim()) {
      this.errorMessage.set('Description is required.');
      return;
    }
    if (!this.category()) {
      this.errorMessage.set('Please select a Category.');
      return;
    }
    if (!this.ministry().trim()) {
      this.errorMessage.set('Ministry is required.');
      return;
    }
    if (!this.department().trim()) {
      this.errorMessage.set('Department is required.');
      return;
    }
    if (!this.state()) {
      this.errorMessage.set('Please select a State / Jurisdiction.');
      return;
    }
    if (!this.benefits().trim()) {
      this.errorMessage.set('Benefits description is required.');
      return;
    }
    if (!this.eligibilityCriteria().trim()) {
      this.errorMessage.set('Eligibility Information is required.');
      return;
    }
    if (!this.applicationProcess().trim()) {
      this.errorMessage.set('Application Process details are required.');
      return;
    }
    if (!this.startDate().trim()) {
      this.errorMessage.set('Start Date is required.');
      return;
    }

    const tagsArray = this.tags().trim()
      ? this.tags().split(',').map(t => t.trim()).filter(Boolean)
      : [this.category(), this.state() !== 'Central / All India' ? this.state() : 'Central'];

    const newScheme: Omit<SchemeItem, 'updatedAt'> = {
      id: this.schemeId().trim().toUpperCase(),
      name: this.schemeName().trim(),
      description: this.description().trim(),
      category: this.category(),
      ministry: this.ministry().trim(),
      department: this.department().trim(),
      state: this.state(),
      benefits: this.benefits().trim(),
      eligibilityCriteria: this.eligibilityCriteria().trim(),
      applicationProcess: this.applicationProcess().trim(),
      applicationUrl: this.applicationUrl().trim() || 'https://india.gov.in',
      startDate: this.startDate().trim(),
      endDate: this.endDate().trim() || 'Ongoing',
      status: targetStatus,
      tags: tagsArray,
      createdAt: this.formatDateForInput(new Date())
    };

    this.isSubmitting.set(true);

    this.schemeService.createAsync(newScheme).subscribe({
      next: (created) => {
        this.isSubmitting.set(false);
        this.router.navigate(['/schemes', created.id]);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.errorMessage.set(err?.error?.detail || 'Failed to save scheme. Please check permissions or network.');
      }
    });
  }
}
