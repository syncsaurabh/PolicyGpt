import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  LoginRequest, 
  Token, 
  UserCreate, 
  VerifyOTPRequest,
  ResendOTPRequest,
  ForgotPasswordRequest, 
  ForgotPasswordResponse, 
  ResetPasswordRequest, 
  MessageResponse 
} from '../../models/auth.models';
import { UserRead, UserRole } from '../../models/user.models';
import { User } from '../../models/user.model';
import { Role, normalizeRole, toDisplayRole, toBackendRole } from '../../models/role.model';
import { AssistantService } from './assistant.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly assistantService = inject(AssistantService);

  private readonly API_URL = environment.apiUrl;
  private readonly TOKEN_KEY = 'policy_gpt_token';
  private readonly USER_KEY = 'policy_gpt_user';

  // Reactively track current user state
  private readonly currentUserSignal = signal<User | null>(this.loadStoredUser());
  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly authenticated = computed(() => this.currentUserSignal() !== null && !!this.getToken());


  /**
   * Authenticate user with email and password via POST /auth/login.
   */
  login(credentials: LoginRequest): Observable<Token> {
    return this.http.post<Token>(`${this.API_URL}/auth/login`, credentials).pipe(
      tap((response) => {
        if (response.access_token) {
          this.setToken(response.access_token);

          // If backend provided user object in Token response
          if (response.user) {
            const user = this.mapUserReadToUser(response.user, response.access_token);
            this.setCurrentUser(user);
          } else {
            // Otherwise construct temporary user and immediately fetch /users/me
            const fallbackUser: User = {
              id: 0,
              name: credentials.email.split('@')[0],
              username: credentials.email.split('@')[0],
              email: credentials.email,
              role: Role.CITIZEN,
              token: response.access_token,
              is_active: true,
              is_verified: true
            };
            this.setCurrentUser(fallbackUser);
            this.fetchProfile().subscribe();
          }
        }
      })
    );
  }

  /**
   * Register a new user via POST /auth/register.
   */
  register(userData: UserCreate): Observable<UserRead> {
    const payload: UserCreate = {
      name: userData.name.trim(),
      email: userData.email.trim(),
      password: userData.password,
      role: userData.role ? toBackendRole(userData.role.toString()) : UserRole.CITIZEN
    };

    return this.http.post<UserRead>(`${this.API_URL}/auth/register`, payload);
  }

  /**
   * Verify email OTP via POST /auth/verify-otp.
   */
  verifyOtp(payload: VerifyOTPRequest): Observable<Token> {
    return this.http.post<Token>(`${this.API_URL}/auth/verify-otp`, payload).pipe(
      tap((response) => {
        if (response.access_token) {
          this.setToken(response.access_token);

          if (response.user) {
            const user = this.mapUserReadToUser(response.user, response.access_token);
            this.setCurrentUser(user);
          } else {
            const fallbackUser: User = {
              id: 0,
              name: payload.email.split('@')[0],
              username: payload.email.split('@')[0],
              email: payload.email,
              role: Role.CITIZEN,
              token: response.access_token,
              is_active: true,
              is_verified: true
            };
            this.setCurrentUser(fallbackUser);
            this.fetchProfile().subscribe();
          }
        }
      })
    );
  }

  /**
   * Resend email OTP via POST /auth/resend-otp.
   */
  resendOtp(payload: ResendOTPRequest): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.API_URL}/auth/resend-otp`, payload);
  }

  /**
   * Initiate password recovery via POST /auth/forgot-password.
   */
  forgotPassword(payload: ForgotPasswordRequest): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>(`${this.API_URL}/auth/forgot-password`, payload);
  }

  /**
   * Complete password reset with token via POST /auth/reset-password.
   */
  resetPassword(payload: ResetPasswordRequest): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.API_URL}/auth/reset-password`, payload);
  }

  /**
   * Fetch current authenticated user profile from GET /users/me.
   */
  fetchProfile(): Observable<UserRead | null> {
    if (!this.getToken()) {
      return of(null);
    }

    return this.http.get<UserRead>(`${this.API_URL}/users/me`).pipe(
      tap((userRead) => {
        const token = this.getToken() || undefined;
        const user = this.mapUserReadToUser(userRead, token);
        this.setCurrentUser(user);
      }),
      catchError((err) => {
        // If 401 or profile fetch fails, handle gracefully
        return of(null);
      })
    );
  }

  /**
   * Check whether user is currently authenticated.
   */
  isAuthenticated(): boolean {
    return this.authenticated();
  }

  /**
   * Get current JWT token.
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Save JWT token to localStorage.
   */
  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get current user object.
   */
  getCurrentUser(): User | null {
    return this.currentUserSignal();
  }

  /**
   * Check if current user possesses one of the allowed roles.
   */
  hasRole(allowedRoles: (Role | UserRole | string)[]): boolean {
    const user = this.currentUserSignal();
    if (!user || !user.role) {
      return false;
    }

    const userRoleNorm = normalizeRole(user.role);
    return allowedRoles.some((role) => normalizeRole(role) === userRoleNorm);
  }

  /** Capability checks according to backend authorization */
  canCreatePolicy(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]);
  }

  canEditPolicy(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]);
  }

  canSubmitPolicy(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]);
  }

  canApproveRejectPolicy(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR]);
  }

  canArchivePolicy(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR]);
  }

  canCreateScheme(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]);
  }

  canEditScheme(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR, UserRole.GOVERNMENT_OFFICIAL]);
  }

  canArchiveScheme(): boolean {
    return this.hasRole([UserRole.ADMINISTRATOR]);
  }

  /**
   * Terminate user session and clear storage.
   */
  logout(redirect: boolean = true): void {
    // Completely reset AI Assistant state to prevent any cross-user session leaks
    this.assistantService.resetSession();

    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUserSignal.set(null);

    if (redirect) {
      this.router.navigate(['/citizen']);
    }
  }

  /**
   * Set and persist the current user state.
   */
  setCurrentUser(user: User | null): void {
    const previousUser = this.currentUserSignal();
    const identityChanged =
      (!previousUser && user) ||
      (previousUser && !user) ||
      (previousUser && user && (previousUser.id !== user.id || previousUser.role !== user.role));

    if (identityChanged) {
      // Identity or role changed: immediately purge assistant state
      this.assistantService.resetSession();
    }

    if (user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.USER_KEY);
    }
    this.currentUserSignal.set(user);
  }


  /**
   * Mapper from backend UserRead model to frontend User interface.
   */
  private mapUserReadToUser(userRead: UserRead, token?: string): User {
    return {
      id: userRead.id,
      name: userRead.name,
      username: userRead.name || userRead.email.split('@')[0],
      email: userRead.email,
      role: toDisplayRole(userRead.role),
      token: token,
      is_active: userRead.is_active,
      is_verified: userRead.is_verified,
      created_at: userRead.created_at,
      updated_at: userRead.updated_at,
      phone_number: userRead.phone_number,
      age: userRead.age,
      state: userRead.state,
      address: userRead.address,
      pincode: userRead.pincode
    };
  }

  /**
   * Helper to load cached user from localStorage on init.
   */
  private loadStoredUser(): User | null {
    try {
      const stored = localStorage.getItem(this.USER_KEY);
      if (stored) {
        return JSON.parse(stored) as User;
      }
    } catch (e) {
      console.error('Failed to load stored user state', e);
      localStorage.removeItem(this.USER_KEY);
    }
    return null;
  }
}
