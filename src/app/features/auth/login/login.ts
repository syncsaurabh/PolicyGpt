import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { Auth } from '../../../core/services/auth';
import { Role } from '../../../models/role.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login implements OnInit {
  protected email = 'citizen@policygpt.gov.in';
  protected password = 'CitizenPass123!';
  protected selectedRole = Role.CITIZEN;
  protected rememberMe = true;
  protected showPassword = false;
  protected isSubmitting = false;
  protected errorMessage = '';
  protected infoMessage = '';
  protected successMessage = '';

  // List of roles from model for the simulator dropdown
  protected readonly roles = Object.values(Role);

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    if (this.route.snapshot.queryParams['sessionExpired']) {
      this.infoMessage = 'Your session has expired. Please log in again.';
    }
    if (this.route.snapshot.queryParams['registered']) {
      this.successMessage = 'Registration successful! Please enter your password to sign in.';
      const registeredEmail = this.route.snapshot.queryParams['email'];
      if (registeredEmail) {
        this.email = registeredEmail;
        this.password = '';
      }
    }
    this.cdr.detectChanges();
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
    this.cdr.detectChanges();
  }

  /**
   * Submit credentials to FastAPI POST /api/v1/auth/login.
   */
  onSubmit(): void {
    this.errorMessage = '';
    this.infoMessage = '';
    this.successMessage = '';

    const email = this.email.trim();
    const password = this.password;

    if (!email || !password) {
      this.errorMessage = 'Please enter both email and password.';
      this.cdr.detectChanges();
      return;
    }

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.login({ email, password }).subscribe({
      next: (token) => {
        this.isSubmitting = false;
        this.cdr.detectChanges();
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
        this.router.navigateByUrl(returnUrl);
      },
      error: (err) => {
        this.isSubmitting = false;

        if (err.status === 401) {
          this.errorMessage = typeof err.error?.detail === 'string' 
            ? err.error.detail 
            : 'Incorrect email or password.';
        } else if (err.status === 422) {
          if (Array.isArray(err.error?.detail)) {
            this.errorMessage = err.error.detail.map((d: any) => d.msg).join(', ');
          } else {
            this.errorMessage = 'Please provide a valid email format and password.';
          }
        } else if (err.status === 0) {
          this.errorMessage = 'Unable to connect to the backend server. Please check your network or ensure the backend is running.';
        } else {
          this.errorMessage = typeof err.error?.detail === 'string'
            ? err.error.detail
            : (err.message || 'Login failed. Please try again.');
        }

        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Quick-action login as a Government Official.
   */
  loginAsGovernmentOfficial(): void {
    this.email = 'official@policygpt.gov.in';
    this.password = 'OfficialPass123!';
    this.selectedRole = Role.GOVERNMENT_OFFICIAL;
    this.onSubmit();
  }

  /**
   * Quick-action login as an Administrator.
   */
  loginAsAdministrator(): void {
    this.email = 'admin@policygpt.gov.in';
    this.password = 'AdminPass123!';
    this.selectedRole = Role.ADMINISTRATOR;
    this.onSubmit();
  }
}
