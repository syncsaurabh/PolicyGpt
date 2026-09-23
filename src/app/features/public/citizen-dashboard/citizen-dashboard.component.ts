import { Component, signal } from '@angular/core';
import { CitizenHeaderComponent } from './components/citizen-header/citizen-header.component';
import { CitizenFooterComponent } from './components/citizen-footer/citizen-footer.component';
import { CitizenHeroComponent } from './components/citizen-hero/citizen-hero.component';
import { CitizenCategoriesComponent } from './components/citizen-categories/citizen-categories.component';
import { CitizenSchemesComponent } from './components/citizen-schemes/citizen-schemes.component';
import { CitizenHowItWorksComponent } from './components/citizen-how-it-works/citizen-how-it-works.component';
import { CitizenAssistantComponent } from './components/citizen-assistant/citizen-assistant.component';
import { CitizenBannerComponent } from './components/citizen-banner/citizen-banner.component';

@Component({
  selector: 'app-citizen-dashboard',
  standalone: true,
  imports: [
    CitizenHeaderComponent,
    CitizenFooterComponent,
    CitizenHeroComponent,
    CitizenCategoriesComponent,
    CitizenSchemesComponent,
    CitizenHowItWorksComponent,
    CitizenAssistantComponent,
    CitizenBannerComponent
  ],
  templateUrl: './citizen-dashboard.component.html',
  styleUrl: './citizen-dashboard.component.css'
})
export class CitizenDashboardComponent {
  protected searchQuery = signal<string>('');
  protected selectedCategory = signal<string | null>(null);

  onSearchChange(query: string): void {
    this.searchQuery.set(query);
  }

  onCategorySelect(category: string): void {
    if (this.selectedCategory() === category) {
      this.selectedCategory.set(null);
    } else {
      this.selectedCategory.set(category);
    }
  }

  onResetFilters(): void {
    this.searchQuery.set('');
    this.selectedCategory.set(null);
  }

  scrollToSchemes(): void {
    const el = document.getElementById('popular-schemes');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }
}
