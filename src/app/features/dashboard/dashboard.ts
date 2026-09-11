import { Component, inject, OnInit } from '@angular/core';
import { Auth } from '../../core/services/auth';
import { AuthService } from '../../core/services/auth.service';
import { UserService } from '../../core/services/user.service';
import { PolicyService, SystemHealth } from '../../core/services/policy.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  protected readonly auth = inject(Auth);
  private readonly authService = inject(AuthService);
  private readonly userService = inject(UserService);
  private readonly policyService = inject(PolicyService);

  protected systemHealth: SystemHealth | null = null;
  protected backendConnected = false;

  ngOnInit(): void {
    // 1. Refresh live profile from GET /api/v1/users/me if authenticated
    if (this.authService.isAuthenticated()) {
      this.userService.getMe().subscribe({
        next: (profile) => {
          // Updates currentUser with latest backend fields
          this.authService.fetchProfile().subscribe();
        },
        error: (err) => {
          console.warn('Could not fetch latest user profile', err);
        }
      });
    }

    // 2. Check live backend health
    this.policyService.checkHealth().subscribe({
      next: (health) => {
        this.systemHealth = health;
        this.backendConnected = true;
      },
      error: () => {
        this.backendConnected = false;
      }
    });
  }
}
