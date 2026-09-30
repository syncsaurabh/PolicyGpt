import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Auth } from '../../../../../core/services/auth';
import { ThemeService } from '../../../../../core/services/theme.service';
import { AssistantService } from '../../../../../core/services/assistant.service';

@Component({
  selector: 'app-citizen-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './citizen-header.component.html',
  styleUrl: './citizen-header.component.css'
})
export class CitizenHeaderComponent {
  protected readonly auth = inject(Auth);
  protected readonly themeService = inject(ThemeService);
  protected readonly assistantService = inject(AssistantService);
  protected readonly mobileMenuOpen = signal(false);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }

  openAssistant(): void {
    this.assistantService.openPopup();
    this.closeMobileMenu();
  }
}

