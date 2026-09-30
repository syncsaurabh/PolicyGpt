import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Scheme } from '../services/scheme';
import {
  SchemeCategory,
  SchemeItem,
  SchemeStatus,
  SCHEME_CATEGORIES,
  SCHEME_STATES
} from '../../../models/scheme.model';

@Component({
  selector: 'app-edit-scheme',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './edit-scheme.html',
  styleUrl: './edit-scheme.css',
})
export class EditScheme implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly schemeService = inject(Scheme);

  scheme = signal<SchemeItem | null>(null);
  notFound = signal<boolean>(false);

  // Form Fields
  schemeName = signal<string>('');
  schemeId = signal<string>('');
  description = signal<string>('');
  category = signal<SchemeCategory>('Scholarships');
  ministry = signal<string>('');
  department = signal<string>('');
  state = signal<string>('Central / All India');
  benefits = signal<string>('');
  eligibilityCriteria = signal<string>('');
  applicationProcess = signal<string>('');
  applicationUrl = signal<string>('');
  startDate = signal<string>('');
  endDate = signal<string>('');
  status = signal<SchemeStatus>('Active');
  tags = signal<string>('');

  errorMessage = signal<string>('');
  isSaving = signal<boolean>(false);

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

  readonly statuses: SchemeStatus[] = ['Active', 'Draft', 'Under Review', 'Closed', 'Archived'];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const found = this.schemeService.getById(id);
      if (found) {
        this.scheme.set(found);
        this.populateForm(found);
      }

      this.schemeService.fetchById(id).subscribe({
        next: (item) => {
          if (item) {
            this.scheme.set(item);
            this.populateForm(item);
            this.notFound.set(false);
          } else if (!this.scheme()) {
            this.notFound.set(true);
          }
        },
        error: () => {
          if (!this.scheme()) {
            this.notFound.set(true);
          }
        }
      });
    } else {
      this.notFound.set(true);
    }
  }

  private populateForm(s: SchemeItem): void {
    this.schemeName.set(s.name);
    this.schemeId.set(s.id);
    this.description.set(s.description);
    this.category.set(s.category);
    this.ministry.set(s.ministry);
    this.department.set(s.department);
    this.state.set(s.state);
    this.benefits.set(s.benefits);
    this.eligibilityCriteria.set(s.eligibilityCriteria);
    this.applicationProcess.set(s.applicationProcess);
    this.applicationUrl.set(s.applicationUrl || '');
    this.startDate.set(s.startDate);
    this.endDate.set(s.endDate || 'Ongoing');
    this.status.set(s.status);
    this.tags.set((s.tags || []).join(', '));
  }

  cancel(): void {
    const s = this.scheme();
    if (s) {
      this.router.navigate(['/schemes', s.id]);
    } else {
      this.router.navigate(['/schemes']);
    }
  }

  saveChanges(): void {
    const original = this.scheme();
    if (!original) return;

    // Validate
    if (!this.schemeName().trim()) {
      this.errorMessage.set('Scheme Name is required.');
      return;
    }
    if (!this.description().trim()) {
      this.errorMessage.set('Description is required.');
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
      this.errorMessage.set('Application Process is required.');
      return;
    }
    if (!this.startDate().trim()) {
      this.errorMessage.set('Start Date is required.');
      return;
    }

    const tagsArray = this.tags().trim()
      ? this.tags().split(',').map(t => t.trim()).filter(Boolean)
      : original.tags || [];

    this.isSaving.set(true);

    const updates: Partial<SchemeItem> = {
      name: this.schemeName().trim(),
      description: this.description().trim(),
      category: this.category(),
      ministry: this.ministry().trim(),
      department: this.department().trim(),
      state: this.state(),
      benefits: this.benefits().trim(),
      eligibilityCriteria: this.eligibilityCriteria().trim(),
      applicationProcess: this.applicationProcess().trim(),
      applicationUrl: this.applicationUrl().trim(),
      startDate: this.startDate().trim(),
      endDate: this.endDate().trim() || 'Ongoing',
      status: this.status(),
      tags: tagsArray
    };

    this.schemeService.updateAsync(original.id, updates).subscribe({
      next: (updated) => {
        this.isSaving.set(false);
        this.router.navigate(['/schemes', updated.id]);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.errorMessage.set(err?.error?.detail || 'Failed to save scheme updates. Please try again.');
      }
    });
  }
}
