import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyDocument, PolicyItem, PolicyStatus } from '../../../models/policy.model';

@Component({
  selector: 'app-upload-policy',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload-policy.html',
  styleUrl: './upload-policy.css',
})
export class UploadPolicy {
  private readonly router = inject(Router);
  private readonly policyService = inject(Policy);

  // Form Fields
  policyName = signal<string>('');
  policyId = signal<string>(this.generateSuggestedId());
  description = signal<string>('');
  ministry = signal<string>('');
  department = signal<string>('');
  category = signal<string>('');
  sector = signal<string>('');
  publicationDate = signal<string>('');
  effectiveDate = signal<string>('');
  expiryDate = signal<string>('');
  tags = signal<string>('');

  // Selected Document
  selectedFile = signal<File | null>(null);
  selectedFileName = signal<string>('');
  selectedFileSize = signal<string>('');
  selectedFileType = signal<string>('PDF');

  // UI States
  isDragging = signal<boolean>(false);
  errorMessage = signal<string>('');
  isSubmitting = signal<boolean>(false);

  // Available options
  readonly ministries = [
    'Ministry of Education',
    'Ministry of Finance',
    'Ministry of Health & Family Welfare',
    'Ministry of Electronics & IT',
    'Ministry of Agriculture',
    'Ministry of Labour',
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
    'Regulatory Framework',
    'Social Welfare',
    'Infrastructure Development'
  ];

  readonly sectors = [
    'Education & Research',
    'Energy & Power',
    'Information Technology',
    'Agriculture & Rural Development',
    'Labour & Employment',
    'Urban Infrastructure',
    'Public Health'
  ];

  private generateSuggestedId(): string {
    const existing = this.policyService.getAll();
    const count = existing.length + 1;
    return `POL-${String(count).padStart(3, '0')}`;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.handleFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);

    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  private handleFile(file: File): void {
    // Validate file size (10 MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.errorMessage.set('File size exceeds 10 MB limit.');
      return;
    }

    // Validate type (.pdf or .docx)
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      this.errorMessage.set('Only PDF and DOCX files are supported.');
      return;
    }

    this.errorMessage.set('');
    this.selectedFile.set(file);
    this.selectedFileName.set(file.name);
    this.selectedFileSize.set(this.formatFileSize(file.size));
    this.selectedFileType.set(ext.toUpperCase());
  }

  removeFile(): void {
    this.selectedFile.set(null);
    this.selectedFileName.set('');
    this.selectedFileSize.set('');
    this.selectedFileType.set('PDF');
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) {
      return `${mb.toFixed(1)} MB`;
    }
    const kb = bytes / 1024;
    return `${Math.round(kb)} KB`;
  }

  cancel(): void {
    this.router.navigate(['/policies']);
  }

  saveAsDraft(): void {
    this.processPolicySubmission('Draft');
  }

  submitForReview(): void {
    this.processPolicySubmission('Under Review');
  }

  private processPolicySubmission(status: PolicyStatus): void {
    // Basic validation
    if (!this.policyName().trim()) {
      this.errorMessage.set('Policy Name is required.');
      return;
    }
    if (!this.policyId().trim()) {
      this.errorMessage.set('Policy ID is required.');
      return;
    }
    if (!this.description().trim()) {
      this.errorMessage.set('Description is required.');
      return;
    }
    if (!this.ministry()) {
      this.errorMessage.set('Please select a Ministry.');
      return;
    }
    if (!this.department()) {
      this.errorMessage.set('Please select a Department.');
      return;
    }
    if (!this.category()) {
      this.errorMessage.set('Please select a Category.');
      return;
    }
    if (!this.sector()) {
      this.errorMessage.set('Please select a Sector.');
      return;
    }
    if (!this.publicationDate()) {
      this.errorMessage.set('Publication Date is required.');
      return;
    }
    if (!this.effectiveDate()) {
      this.errorMessage.set('Effective Date is required.');
      return;
    }

    // Check if document is uploaded or generate a placeholder
    const docName = this.selectedFileName() || `${this.policyName().trim().replace(/\s+/g, '_')}.pdf`;
    const docSize = this.selectedFileSize() || '2.1 MB';
    const docType = this.selectedFileType() || 'PDF';

    const document: PolicyDocument = {
      name: docName,
      size: docSize,
      type: docType
    };

    const tagsArray = this.tags()
      ? this.tags().split(',').map(t => t.trim()).filter(Boolean)
      : [this.category(), this.sector()];

    const newPolicy: Omit<PolicyItem, 'updatedAt'> = {
      id: this.policyId().trim().toUpperCase(),
      name: this.policyName().trim(),
      description: this.description().trim(),
      ministry: this.ministry(),
      department: this.department(),
      category: this.category(),
      sector: this.sector(),
      publicationDate: this.formatDateString(this.publicationDate()),
      effectiveDate: this.formatDateString(this.effectiveDate()),
      expiryDate: this.expiryDate() ? this.formatDateString(this.expiryDate()) : '—',
      tags: tagsArray,
      document,
      status,
      submittedAt: status === 'Under Review' ? this.formatDateString(new Date().toISOString()) : undefined,
      nextStep: status === 'Under Review' ? 'Awaiting approval from the designated government official' : undefined
    };

    this.isSubmitting.set(true);

    this.policyService.createAsync(newPolicy).subscribe({
      next: (created) => {
        this.isSubmitting.set(false);
        if (status === 'Under Review') {
          this.router.navigate(['/policies', created.id, 'submitted']);
        } else {
          this.router.navigate(['/policies']);
        }
      },
      error: (e) => {
        this.errorMessage.set(e?.error?.detail || e?.message || 'Failed to save policy.');
        this.isSubmitting.set(false);
      }
    });
  }

  private formatDateString(dateVal: string): string {
    if (!dateVal) return '';
    try {
      const d = new Date(dateVal);
      if (isNaN(d.getTime())) return dateVal;
      const day = String(d.getDate()).padStart(2, '0');
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${day} ${months[d.getMonth()]} ${d.getFullYear()}`;
    } catch {
      return dateVal;
    }
  }
}
