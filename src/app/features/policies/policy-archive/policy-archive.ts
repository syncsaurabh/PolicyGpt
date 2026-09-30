import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyItem, PolicyStatus } from '../../../models/policy.model';

@Component({
  selector: 'app-policy-archive',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './policy-archive.html',
  styleUrl: './policy-archive.css',
})
export class PolicyArchive implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly policyService = inject(Policy);

  policy = signal<PolicyItem | null>(null);
  notFound = signal<boolean>(false);
  confirmed = signal<boolean>(false);
  isArchiving = signal<boolean>(false);
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

  cancel(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id]);
    } else {
      this.router.navigate(['/policies']);
    }
  }

  archivePolicy(): void {
    const p = this.policy();
    if (!p || !this.confirmed()) return;

    this.isArchiving.set(true);
    this.errorMessage.set('');
    this.policyService.archiveAsync(p.id).subscribe({
      next: () => {
        this.isArchiving.set(false);
        this.router.navigate(['/policies']);
      },
      error: (e) => {
        this.isArchiving.set(false);
        this.errorMessage.set(e?.error?.detail || 'Failed to archive policy. Please verify permissions.');
      }
    });
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
      default:
        return 'badge-published';
    }
  }
}
