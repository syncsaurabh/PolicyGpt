import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { UserService } from '../../../core/services/user.service';
import { AuthService } from '../../../core/services/auth.service';
import { UserRead } from '../../../models/user.models';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class Users implements OnInit {
  private readonly userService = inject(UserService);
  private readonly authService = inject(AuthService);

  protected currentProfile: UserRead | null = null;
  protected adminTestResult: string | null = null;
  protected govtTestResult: string | null = null;
  protected editName = '';
  protected isUpdating = false;
  protected updateSuccess = false;
  protected errorMessage = '';
  protected loading = false;

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.loading = true;
    this.userService.getMe().subscribe({
      next: (profile) => {
        this.loading = false;
        this.currentProfile = profile;
        this.editName = profile.name || '';
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Failed to load user profile from backend.';
      }
    });
  }

  runAdminRbacTest(): void {
    this.adminTestResult = 'Verifying Administrator RBAC...';
    this.userService.testAdminRbac().subscribe({
      next: (res) => {
        this.adminTestResult = res?.message || 'Access granted: 200 OK (ADMINISTRATOR role verified)';
      },
      error: (err) => {
        this.adminTestResult = `Access denied (${err.status}): ${err.error?.detail || 'Forbidden'}`;
      }
    });
  }

  runGovtRbacTest(): void {
    this.govtTestResult = 'Verifying Government RBAC...';
    this.userService.testGovernmentRbac().subscribe({
      next: (res) => {
        this.govtTestResult = res?.message || 'Access granted: 200 OK (GOVERNMENT_OFFICIAL role verified)';
      },
      error: (err) => {
        this.govtTestResult = `Access denied (${err.status}): ${err.error?.detail || 'Forbidden'}`;
      }
    });
  }

  saveProfileName(): void {
    if (!this.editName.trim()) return;

    this.isUpdating = true;
    this.updateSuccess = false;
    this.errorMessage = '';

    this.userService.updateMe({ name: this.editName.trim() }).subscribe({
      next: (updated) => {
        this.isUpdating = false;
        this.updateSuccess = true;
        this.currentProfile = updated;
        this.authService.fetchProfile().subscribe();
        setTimeout(() => this.updateSuccess = false, 4000);
      },
      error: (err) => {
        this.isUpdating = false;
        this.errorMessage = err.error?.detail || 'Failed to update profile name.';
      }
    });
  }
}
