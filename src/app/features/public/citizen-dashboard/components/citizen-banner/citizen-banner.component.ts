import { Component, output } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-citizen-banner',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './citizen-banner.component.html',
  styleUrl: './citizen-banner.component.css'
})
export class CitizenBannerComponent {
  readonly exploreClick = output<void>();

  onExplore(): void {
    this.exploreClick.emit();
  }
}
