import { Component, inject } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Auth } from '../../../core/services/auth';
import { Role } from '../../../models/role.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  protected username = '';
  protected selectedRole = Role.CITIZEN;
  
  // List of roles from model for the simulator dropdown
  protected readonly roles = Object.values(Role);

  private readonly auth = inject(Auth);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  /**
   * Submit mock login credentials.
   */
  onSubmit(): void {
    if (!this.username.trim()) {
      alert('Please enter a username to log in.');
      return;
    }

    const success = this.auth.login(this.username.trim(), this.selectedRole);
    if (success) {
      // Direct back to initial attempted URL or default to dashboard
      const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
      this.router.navigateByUrl(returnUrl);
    }
  }
}
