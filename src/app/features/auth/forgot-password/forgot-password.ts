import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.css',
})
export class ForgotPassword {
  protected email = '';
  protected isSubmitting = false;
  protected errorMessage = '';

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  onSubmit(): void {
    this.errorMessage = '';
    const targetEmail = this.email.trim();

    if (!targetEmail) {
      this.errorMessage = 'Please enter your registered email address.';
      this.cdr.detectChanges();
      return;
    }

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.forgotPassword({ email: targetEmail }).subscribe({
      next: (response) => {
        this.isSubmitting = false;
        this.cdr.detectChanges();
        this.router.navigate(['/reset-password'], {
          queryParams: {
            email: targetEmail,
            token: response.reset_token || ''
          }
        });
      },
      error: (err) => {
        this.isSubmitting = false;
        if (err.status === 0) {
          // Dev fallback
          this.router.navigate(['/reset-password'], {
            queryParams: { email: targetEmail }
          });
        } else {
          this.errorMessage = err.error?.detail || 'Failed to request password reset. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }
}
