import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyHistoryStep, PolicyItem, PolicyStatus } from '../../../models/policy.model';

@Component({
  selector: 'app-policy-status',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './policy-status.html',
  styleUrl: './policy-status.css',
})
export class PolicyStatusComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly policyService = inject(Policy);

  policy = signal<PolicyItem | null>(null);
  notFound = signal<boolean>(false);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const found = this.policyService.getById(id);
      if (found) {
        this.policy.set(found);
      } else {
        this.notFound.set(true);
      }
    } else {
      this.notFound.set(true);
    }
  }

  backToPolicies(): void {
    this.router.navigate(['/policies']);
  }

  viewPolicy(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id]);
    }
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
        return 'badge-under-review';
    }
  }

  getTimelineSteps(p: PolicyItem): PolicyHistoryStep[] {
    if (p.history && p.history.length > 0) {
      return p.history;
    }

    // Default fallback 4-step workflow
    return [
      {
        status: 'Draft',
        label: 'Draft',
        description: 'Policy created',
        date: p.publicationDate || p.updatedAt,
        completed: true
      },
      {
        status: 'Under Review',
        label: 'Under Review',
        description: p.status === 'Draft' ? 'Awaiting submission' : 'Policy submitted for approval',
        date: p.submittedAt || (p.status !== 'Draft' ? p.updatedAt : undefined),
        completed: p.status === 'Approved' || p.status === 'Published',
        current: p.status === 'Under Review'
      },
      {
        status: 'Approved',
        label: 'Approved',
        description: p.status === 'Approved' || p.status === 'Published' ? 'Approved by committee' : 'Awaiting approval',
        completed: p.status === 'Published',
        current: p.status === 'Approved'
      },
      {
        status: 'Published',
        label: 'Published',
        description: p.status === 'Published' ? 'Active in national repository' : 'Not yet published',
        completed: p.status === 'Published',
        current: p.status === 'Published'
      }
    ];
  }

  getStepMarkerClass(step: PolicyHistoryStep): string {
    if (step.completed && !step.current) {
      return 'marker-completed';
    }
    if (step.current) {
      if (step.status === 'Under Review') return 'marker-amber';
      if (step.status === 'Approved' || step.status === 'Published') return 'marker-green';
      return 'marker-blue';
    }
    return 'marker-upcoming';
  }
}
