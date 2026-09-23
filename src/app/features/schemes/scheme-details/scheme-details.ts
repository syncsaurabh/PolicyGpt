import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Scheme } from '../services/scheme';
import { SchemeItem, SchemeStatus } from '../../../models/scheme.model';
import { Auth } from '../../../core/services/auth';

@Component({
  selector: 'app-scheme-details',
  standalone: true,
  imports: [CommonModule],
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

  // Modal State for Archive/Delete confirmation
  showConfirmModal = signal<boolean>(false);
  isDeleting = signal<boolean>(false);

  canEditScheme(): boolean {
    return this.auth.canEditScheme();
  }

  canArchiveScheme(): boolean {
    return this.auth.canArchiveScheme();
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
