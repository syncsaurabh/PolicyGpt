import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyItem, PolicyStatus } from '../../../models/policy.model';
import { Auth } from '../../../core/services/auth';

@Component({
  selector: 'app-policy-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './policy-details.html',
  styleUrl: './policy-details.css',
})
export class PolicyDetails implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly policyService = inject(Policy);
  protected readonly auth = inject(Auth);

  policy = signal<PolicyItem | null>(null);
  notFound = signal<boolean>(false);
  showDocumentModal = signal<boolean>(false);
  isProcessing = signal<boolean>(false);
  actionError = signal<string | null>(null);

  canEditPolicy(): boolean {
    return this.auth.canEditPolicy();
  }

  canSubmitPolicy(): boolean {
    return this.auth.canSubmitPolicy();
  }

  canApproveRejectPolicy(): boolean {
    return this.auth.canApproveRejectPolicy();
  }

  canArchivePolicy(): boolean {
    return this.auth.canArchivePolicy();
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const found = this.policyService.getById(id);
      if (found) {
        this.policy.set(found);
      }

      this.policyService.fetchById(id).subscribe({
        next: (item) => {
          if (item) {
            this.policy.set(item);
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

  backToPolicies(): void {
    this.router.navigate(['/policies']);
  }

  editPolicy(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id, 'edit']);
    }
  }

  submitForReview(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id, 'submit']);
    }
  }

  approvePolicy(): void {
    const p = this.policy();
    if (!p) return;

    this.isProcessing.set(true);
    this.actionError.set(null);

    this.policyService.approvePolicyAsync(p.id, true).subscribe({
      next: (updated) => {
        this.policy.set(updated);
        this.isProcessing.set(false);
      },
      error: (err) => {
        this.actionError.set(err.error?.detail || 'Failed to approve policy.');
        this.isProcessing.set(false);
      }
    });
  }

  rejectPolicy(): void {
    const p = this.policy();
    if (!p) return;

    const reason = window.prompt('Please provide a reason for policy rejection:', 'Requires updates and alignment with current policy framework');
    if (reason === null) return;

    this.isProcessing.set(true);
    this.actionError.set(null);

    this.policyService.rejectPolicyAsync(p.id, reason).subscribe({
      next: (updated) => {
        this.policy.set(updated);
        this.isProcessing.set(false);
      },
      error: (err) => {
        this.actionError.set(err.error?.detail || 'Failed to reject policy.');
        this.isProcessing.set(false);
      }
    });
  }

  viewStatusHistory(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id, 'status']);
    }
  }

  archivePolicy(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id, 'archive']);
    }
  }

  openDocumentPreview(): void {
    this.showDocumentModal.set(true);
  }

  closeDocumentPreview(): void {
    this.showDocumentModal.set(false);
  }

  getStatusClass(status: PolicyStatus): string {
    switch (status) {
      case 'Published':
        return 'badge-published';
      case 'Approved':
        return 'badge-approved';
      case 'Under Review':
        return 'badge-under-review';
      case 'Draft':
        return 'badge-draft';
      case 'Archived':
        return 'badge-archived';
      case 'Rejected':
        return 'badge-rejected';
      default:
        return 'badge-published';
    }
  }
}
