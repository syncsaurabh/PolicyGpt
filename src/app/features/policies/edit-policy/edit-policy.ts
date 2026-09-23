import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyDocument, PolicyItem } from '../../../models/policy.model';

@Component({
  selector: 'app-edit-policy',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './edit-policy.html',
  styleUrl: './edit-policy.css',
})
export class EditPolicy implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly policyService = inject(Policy);

  policy = signal<PolicyItem | null>(null);
  notFound = signal<boolean>(false);

  // Form Fields
  policyName = signal<string>('');
  policyId = signal<string>('');
  description = signal<string>('');
  ministry = signal<string>('');
  department = signal<string>('');
  category = signal<string>('');
  sector = signal<string>('');
  publicationDate = signal<string>('');
  effectiveDate = signal<string>('');
  expiryDate = signal<string>('');
  tags = signal<string>('');

  // Document Info
  currentDocument = signal<PolicyDocument>({
    name: 'document.pdf',
    size: '2.4 MB',
    type: 'PDF'
  });

  errorMessage = signal<string>('');
  isSaving = signal<boolean>(false);

  readonly ministries = [
    'Ministry of Education',
    'Ministry of Finance',
    'Ministry of Health',
    'Ministry of Health & Family Welfare',
    'Ministry of Electronics & IT',
    'Ministry of Agriculture',
    'Ministry of Labour',
    'Ministry of Housing & Uraban Affairs',
    'Ministry of Housing & Urban Affairs'
  ];

  readonly departments = [
    'Department of School Education',
    'Department of Higher Education',
    'Department of Economic Affairs',
    'Department of Public Health',
    'Department of Agriculture & Farmers Welfare',
    'Department of Employment & Training',
    'Department of Urban Housing',
    'Digital Governance Division'
  ];

  readonly categories = [
    'Education',
    'Healthcare',
    'Agriculture',
    'Employment',
    'Finance',
    'Housing',
    'Public Policy',
    'Governance',
    'Regulatory Framework',
    'Social Welfare'
  ];

  readonly sectors = [
    'Education',
    'Public Sector',
    'Social Development',
    'Education & Research',
    'Energy & Power',
    'Information Technology',
    'Agriculture & Rural Development',
    'Labour & Employment',
    'Urban Infrastructure',
    'Public Health'
  ];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const found = this.policyService.getById(id);
      if (found) {
        this.policy.set(found);
        this.populateForm(found);
      }

      this.policyService.fetchById(id).subscribe({
        next: (item) => {
          if (item) {
            this.policy.set(item);
            this.populateForm(item);
            this.notFound.set(false);
          } else if (!this.policy()) {
            this.notFound.set(true);
          }
        },
        error: () => {
          if (!this.policy()) {
            this.notFound.set(true);
          }
        }
      });
    } else {
      this.notFound.set(true);
    }
  }

  private populateForm(p: PolicyItem): void {
    this.policyName.set(p.name);
    this.policyId.set(p.id);
    this.description.set(p.description);
    this.ministry.set(p.ministry);
    this.department.set(p.department);
    this.category.set(p.category);
    this.sector.set(p.sector);
    this.publicationDate.set(p.publicationDate);
    this.effectiveDate.set(p.effectiveDate);
    this.expiryDate.set(p.expiryDate && p.expiryDate !== '—' ? p.expiryDate : '');
    this.tags.set(p.tags ? p.tags.join(', ') : '');
    if (p.document) {
      this.currentDocument.set(p.document);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      const ext = file.name.split('.').pop()?.toUpperCase() || 'PDF';
      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      this.currentDocument.set({
        name: file.name,
        size: `${sizeMb} MB`,
        type: ext
      });
    }
  }

  cancel(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id]);
    } else {
      this.router.navigate(['/policies']);
    }
  }

  saveChanges(): void {
    const p = this.policy();
    if (!p) return;

    if (!this.policyName().trim()) {
      this.errorMessage.set('Policy Name is required.');
      return;
    }
    if (!this.description().trim()) {
      this.errorMessage.set('Description is required.');
      return;
    }

    const tagsArray = this.tags()
      ? this.tags().split(',').map(t => t.trim()).filter(Boolean)
      : p.tags;

    this.isSaving.set(true);
    this.errorMessage.set('');

    const updates: Partial<PolicyItem> = {
      name: this.policyName().trim(),
      description: this.description().trim(),
      ministry: this.ministry() || p.ministry,
      department: this.department() || p.department,
      category: this.category() || p.category,
      sector: this.sector() || p.sector,
      publicationDate: this.publicationDate() || p.publicationDate,
      effectiveDate: this.effectiveDate() || p.effectiveDate,
      expiryDate: this.expiryDate() || '—',
      tags: tagsArray,
      document: this.currentDocument()
    };

    this.policyService.updateAsync(p.id, updates).subscribe({
      next: (updated) => {
        this.isSaving.set(false);
        this.router.navigate(['/policies', updated.id]);
      },
      error: (e) => {
        this.errorMessage.set(e?.error?.detail || e?.message || 'Error updating policy.');
        this.isSaving.set(false);
      }
    });
  }
}
