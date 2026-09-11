import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css',
})
export class ResetPassword implements OnInit {
  protected email = '';
  protected token = '';
  protected resendNotice = '';
  protected showNewPasswordForm = false;
  protected newPassword = '';
  protected confirmPassword = '';
  protected passwordUpdated = false;
  protected showPassword = false;
  protected showConfirmPassword = false;
  protected isSubmitting = false;
  protected errorMessage = '';

  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    const qEmail = this.route.snapshot.queryParams['email'];
    const qToken = this.route.snapshot.queryParams['token'];

    if (qEmail) {
      this.email = qEmail;
    }
    if (qToken) {
      this.token = qToken;
      this.showNewPasswordForm = true;
    }
    this.cdr.detectChanges();
  }

  resendEmail(): void {
    if (!this.email) {
      this.resendNotice = 'Please use the Forgot Password page to enter your email address.';
      this.cdr.detectChanges();
      return;
    }

    this.authService.forgotPassword({ email: this.email }).subscribe({
      next: (res) => {
        this.resendNotice = `A new reset link has been dispatched to ${this.email}.`;
        if (res.reset_token) {
          this.token = res.reset_token;
        }
        this.cdr.detectChanges();
        setTimeout(() => {
          this.resendNotice = '';
          this.cdr.detectChanges();
        }, 6000);
      },
      error: () => {
        this.resendNotice = `Reset instructions sent to ${this.email} if registered.`;
        this.cdr.detectChanges();
      }
    });
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
    this.cdr.detectChanges();
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
    this.cdr.detectChanges();
  }

  submitNewPassword(): void {
    this.errorMessage = '';

    if (!this.token.trim()) {
      this.errorMessage = 'A valid reset token is required. Please check your reset link.';
      this.cdr.detectChanges();
      return;
    }

    if (!this.newPassword || !this.confirmPassword) {
      this.errorMessage = 'Please complete both password fields.';
      this.cdr.detectChanges();
      return;
    }

    if (this.newPassword.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters long.';
      this.cdr.detectChanges();
      return;
    }

    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      this.cdr.detectChanges();
      return;
    }

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.resetPassword({
      token: this.token.trim(),
      new_password: this.newPassword
    }).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.passwordUpdated = true;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isSubmitting = false;
        if (err.status === 422) {
          this.errorMessage = 'Password must be at least 8 characters.';
        } else {
          this.errorMessage = err.error?.detail || 'Invalid or expired reset token. Please request a new link.';
        }
        this.cdr.detectChanges();
      }
    });
  }
}
