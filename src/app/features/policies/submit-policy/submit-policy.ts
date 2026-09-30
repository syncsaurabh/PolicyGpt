import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyItem } from '../../../models/policy.model';

@Component({
  selector: 'app-submit-policy',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './submit-policy.html',
  styleUrl: './submit-policy.css',
})
export class SubmitPolicy implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly policyService = inject(Policy);

  policy = signal<PolicyItem | null>(null);
  notFound = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);
  errorMessage = signal<string>('');

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

  submitForReview(): void {
    const p = this.policy();
    if (!p) return;

    this.isSubmitting.set(true);
    this.errorMessage.set('');

    this.policyService.submitForReviewAsync(p.id).subscribe({
      next: (updated) => {
        this.isSubmitting.set(false);
        this.router.navigate(['/policies', updated.id, 'submitted']);
      },
      error: (e) => {
        this.errorMessage.set(e?.error?.detail || e?.message || 'Error occurred while submitting.');
        this.isSubmitting.set(false);
      }
    });
  }
}
