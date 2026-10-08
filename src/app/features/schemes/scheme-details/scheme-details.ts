import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Scheme } from '../services/scheme';
import { SchemeItem, SchemeStatus } from '../../../models/scheme.model';
import { Auth } from '../../../core/services/auth';
import { ApplicationModalComponent } from '../../dashboard/components/application-modal/application-modal.component';

@Component({
  selector: 'app-scheme-details',
  standalone: true,
  imports: [CommonModule, ApplicationModalComponent],
  templateUrl: './scheme-details.html',
  styleUrl: './scheme-details.css',
})
export class SchemeDetails implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly schemeService = inject(Scheme);
  protected readonly auth = inject(Auth);

  scheme = signal<SchemeItem | null>(null);
  notFound = signal<boolean>(false);

  // Application Modal state
  showApplyModal = signal<boolean>(false);
  successToast = signal<string | null>(null);

  // Modal State for Archive/Delete confirmation
  showConfirmModal = signal<boolean>(false);
  isDeleting = signal<boolean>(false);

  canEditScheme(): boolean {
    return this.auth.canEditScheme();
  }

  canArchiveScheme(): boolean {
    return this.auth.canArchiveScheme();
  }

  get isCitizenOrPublic(): boolean {
    const user = this.auth.getCurrentUser();
    if (!user) return true;
    const r = user.role;
    return r === 'CITIZEN' || r === 'Citizen' || r === 'RESEARCHER' || r === 'ORGANIZATION' || r === 'GUEST_USER';
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const found = this.schemeService.getById(id);
      if (found) {
        this.scheme.set(found);
      }

      this.schemeService.fetchById(id).subscribe({
        next: (item) => {
          if (item) {
            this.scheme.set(item);
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

  backToSchemes(): void {
    this.router.navigate(['/schemes']);
  }

  editScheme(): void {
    const s = this.scheme();
    if (s) {
      this.router.navigate(['/schemes', s.id, 'edit']);
    }
  }

  openApplyModal(): void {
    if (!this.auth.isAuthenticated()) {
      this.router.navigate(['/login'], { queryParams: { redirectUrl: this.router.url } });
      return;
    }
    this.showApplyModal.set(true);
  }

  closeApplyModal(): void {
    this.showApplyModal.set(false);
  }

  onApplicationSubmitted(res: any): void {
    this.showToast(`Application ${res?.application_number || ''} submitted successfully!`);
  }

  showToast(msg: string): void {
    this.successToast.set(msg);
    setTimeout(() => this.successToast.set(null), 4000);
  }

  openConfirmModal(): void {
    this.showConfirmModal.set(true);
  }

  closeConfirmModal(): void {
    this.showConfirmModal.set(false);
    this.isDeleting.set(false);
  }

  confirmArchiveOrDelete(): void {
    const s = this.scheme();
    if (!s) return;

    this.isDeleting.set(true);
    if (s.status === 'Archived') {
      this.schemeService.delete(s.id);
      this.router.navigate(['/schemes']);
    } else {
      this.schemeService.archiveAsync(s.id).subscribe({
        next: (updated) => {
          this.scheme.set(updated);
          this.closeConfirmModal();
        },
        error: (err) => {
          console.error('Failed to archive scheme:', err);
          this.closeConfirmModal();
        }
      });
    }
  }

  restoreScheme(): void {
    const s = this.scheme();
    if (!s) return;

    this.schemeService.restore(s.id);
    const updated = this.schemeService.getById(s.id);
    if (updated) {
      this.scheme.set(updated);
    }
  }

  getStatusClass(status: SchemeStatus): string {
    switch (status) {
      case 'Active':
        return 'badge-published';
      case 'Under Review':
        return 'badge-under-review';
      case 'Draft':
        return 'badge-draft';
      case 'Closed':
        return 'badge-closed';
      case 'Archived':
        return 'badge-archived';
      default:
        return 'badge-published';
    }
  }
}
