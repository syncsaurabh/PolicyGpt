import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { Role } from '../../models/role.model';
import { User } from '../../models/user.model';
import { UserRole } from '../../models/user.models';

@Injectable({
  providedIn: 'root'
})
export class Auth {
  private readonly authService = inject(AuthService);

  readonly currentUser = this.authService.currentUser;
  readonly authenticated = this.authService.authenticated;

  isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  getCurrentUser(): User | null {
    return this.authService.getCurrentUser();
  }

  getToken(): string | null {
    return this.authService.getToken();
  }

  logout(): void {
    this.authService.logout(true);
  }

  hasRole(allowedRoles: (Role | UserRole | string)[]): boolean {
    return this.authService.hasRole(allowedRoles);
  }

  canCreatePolicy(): boolean {
    return this.authService.canCreatePolicy();
  }

  canEditPolicy(): boolean {
    return this.authService.canEditPolicy();
  }

  canSubmitPolicy(): boolean {
    return this.authService.canSubmitPolicy();
  }

  canApproveRejectPolicy(): boolean {
    return this.authService.canApproveRejectPolicy();
  }

  canArchivePolicy(): boolean {
    return this.authService.canArchivePolicy();
  }

  canCreateScheme(): boolean {
    return this.authService.canCreateScheme();
  }

  canEditScheme(): boolean {
    return this.authService.canEditScheme();
  }

  canArchiveScheme(): boolean {
    return this.authService.canArchiveScheme();
  }
}
