import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './auth-layout.html',
  styleUrl: './auth-layout.css'
})
export class AuthLayoutComponent {
  protected readonly themeService = inject(ThemeService);
}