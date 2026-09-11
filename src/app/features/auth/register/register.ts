import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { Auth } from '../../../core/services/auth';
import { Role, toBackendRole } from '../../../models/role.model';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {
  protected fullName = '';
  protected email = '';
  protected password = '';
  protected confirmPassword = '';
  protected selectedRole = Role.CITIZEN;
  protected showPassword = false;
  protected showConfirmPassword = false;
  protected isSubmitting = false;
  protected errorMessage = '';
  protected successMessage = '';

  protected readonly roles = Object.values(Role);

  private readonly authService = inject(AuthService);
  private readonly legacyAuth = inject(Auth);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  togglePassword(): void {
    this.showPassword = !this.showPassword;
    this.cdr.detectChanges();
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
    this.cdr.detectChanges();
  }

  onSubmit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    const name = this.fullName.trim();
    const email = this.email.trim();
    const password = this.password;

    if (!name || !email || !password) {
      this.errorMessage = 'Please complete all required fields.';
      this.cdr.detectChanges();
      return;
    }

    if (name.length < 2) {
      this.errorMessage = 'Full Name must be at least 2 characters.';
      this.cdr.detectChanges();
      return;
    }

    if (password.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters long.';
      this.cdr.detectChanges();
      return;
    }

    if (password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match. Please verify.';
      this.cdr.detectChanges();
      return;
    }

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.register({
      name,
      email,
      password,
      role: toBackendRole(this.selectedRole)
    }).subscribe({
      next: (createdUser) => {
        this.successMessage = 'Registration successful! Redirecting to login page...';
        this.cdr.detectChanges();
        setTimeout(() => {
          this.router.navigate(['/login'], {
            queryParams: { registered: 'true', email: email }
          });
        }, 1200);
      },
      error: (err) => {
        this.isSubmitting = false;
        if (err.status === 422) {
          if (Array.isArray(err.error?.detail)) {
            this.errorMessage = err.error.detail.map((d: any) => d.msg).join(', ');
          } else {
            this.errorMessage = 'Invalid registration data. Please verify all fields.';
          }
        } else if (err.status === 400) {
          this.errorMessage = err.error?.detail || 'An account with this email already exists.';
        } else if (err.status === 0) {
          // Offline dev fallback
          this.legacyAuth.register(name, email, this.selectedRole);
          this.successMessage = 'Registration successful! Redirecting to login page...';
          this.cdr.detectChanges();
          setTimeout(() => {
            this.router.navigate(['/login'], {
              queryParams: { registered: 'true', email: email }
            });
          }, 1200);
        } else {
          this.errorMessage = err.error?.detail || 'Registration failed. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }
}
