import { Injectable, signal, computed } from '@angular/core';
import { Role } from '../../models/role.model';
import { User } from '../../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class Auth {
  private readonly STORAGE_KEY = 'policy_gpt_user';

  // Reactively track the current user.
  private readonly currentUserSignal = signal<User | null>(this.loadUserFromStorage());

  // Expose readonly signal of the current user.
  readonly currentUser = this.currentUserSignal.asReadonly();

  // Expose a computed value for whether the user is authenticated.
  readonly authenticated = computed(() => this.currentUserSignal() !== null);

  constructor() {}

  /**
   * Check whether the user is authenticated.
   */
  isAuthenticated(): boolean {
    return this.authenticated();
  }

  /**
   * Get the currently logged-in user.
   */
  getCurrentUser(): User | null {
    return this.currentUserSignal();
  }

  /**
   * Get the authentication token (if any).
   */
  getToken(): string | null {
    const user = this.currentUserSignal();
    return user?.token || null;
  }

  /**
   * Simulate a login for frontend development and testing.
   */
  login(username: string, role: Role): boolean {
    if (!username || !role) {
      return false;
    }

    const mockUser: User = {
      id: Math.random().toString(36).substring(2, 9),
      username: username,
      email: `${username.toLowerCase().replace(/\s+/g, '')}@example.com`,
      role: role,
      token: `mock-jwt-token-for-${username.toLowerCase()}-${role.toLowerCase().replace(/\s+/g, '-')}`
    };

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(mockUser));
    this.currentUserSignal.set(mockUser);
    return true;
  }

  /**
   * Terminate the session and clear credentials.
   */
  logout(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    this.currentUserSignal.set(null);
  }

  /**
   * Checks if the user has permission based on a list of allowed roles.
   */
  hasRole(allowedRoles: Role[]): boolean {
    const user = this.currentUserSignal();
    if (!user) {
      return false;
    }
    return allowedRoles.includes(user.role);
  }

  /**
   * Helper to load stored credentials from localStorage.
   */
  private loadUserFromStorage(): User | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as User;
      }
    } catch (e) {
      console.error('Failed to parse stored user authentication state', e);
      localStorage.removeItem(this.STORAGE_KEY);
    }
    return null;
  }
}
