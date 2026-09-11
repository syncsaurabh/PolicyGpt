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

  login(usernameOrEmail: string, role: Role | UserRole): boolean {
    if (!usernameOrEmail || !role) {
      return false;
    }

    const isEmail = usernameOrEmail.includes('@');
    const username = isEmail ? usernameOrEmail.split('@')[0] : usernameOrEmail;
    const email = isEmail ? usernameOrEmail : `${username.toLowerCase().replace(/\s+/g, '')}@example.com`;

    const mockUser: User = {
      id: Math.random().toString(36).substring(2, 9),
      username: username,
      email: email,
      role: role,
      token: `mock-jwt-token-for-${username.toLowerCase()}-${role.toString().toLowerCase().replace(/\s+/g, '-')}`
    };

    this.authService.setToken(mockUser.token!);
    this.authService.setCurrentUser(mockUser);
    return true;
  }

  register(name: string, email: string, role: Role | UserRole): boolean {
    if (!name || !email || !role) {
      return false;
    }

    const mockUser: User = {
      id: Math.random().toString(36).substring(2, 9),
      username: name,
      email: email,
      role: role,
      token: `mock-jwt-token-for-${name.toLowerCase().replace(/\s+/g, '-')}-${role.toString().toLowerCase().replace(/\s+/g, '-')}`
    };

    this.authService.setToken(mockUser.token!);
    this.authService.setCurrentUser(mockUser);
    return true;
  }

  logout(): void {
    this.authService.logout(true);
  }

  hasRole(allowedRoles: (Role | UserRole | string)[]): boolean {
    return this.authService.hasRole(allowedRoles);
  }
}
