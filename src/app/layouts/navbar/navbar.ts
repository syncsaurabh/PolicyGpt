import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { LayoutService } from '../../core/services/layout.service';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class Navbar {
  protected readonly auth = inject(Auth);
  protected readonly layoutService = inject(LayoutService);
  protected readonly themeService = inject(ThemeService);
  private readonly router = inject(Router);

  logout(): void {
    this.auth.logout();
  }
}
