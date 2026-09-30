import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Policy } from '../services/policy';
import { PolicyItem } from '../../../models/policy.model';

@Component({
  selector: 'app-policy-submitted',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './policy-submitted.html',
  styleUrl: './policy-submitted.css',
})
export class PolicySubmitted implements OnInit {
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

  viewPolicyHistory(): void {
    const p = this.policy();
    if (p) {
      this.router.navigate(['/policies', p.id, 'status']);
    }
  }
}
