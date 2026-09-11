import { Component, output } from '@angular/core';

@Component({
  selector: 'app-citizen-banner',
  standalone: true,
  templateUrl: './citizen-banner.component.html',
  styleUrl: './citizen-banner.component.scss'
})
export class CitizenBannerComponent {
  readonly exploreClick = output<void>();

  onExplore(): void {
    this.exploreClick.emit();
  }
}
