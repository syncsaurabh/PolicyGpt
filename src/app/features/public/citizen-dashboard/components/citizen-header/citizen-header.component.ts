import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Auth } from '../../../../../core/services/auth';

@Component({
  selector: 'app-citizen-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './citizen-header.component.html',
  styleUrl: './citizen-header.component.scss'
})
export class CitizenHeaderComponent {
  protected readonly auth = inject(Auth);
  protected readonly mobileMenuOpen = signal(false);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }
}
