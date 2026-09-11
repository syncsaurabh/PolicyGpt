import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-citizen-hero',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './citizen-hero.component.html',
  styleUrl: './citizen-hero.component.scss'
})
export class CitizenHeroComponent {
  readonly searchQuery = input<string>('');
  readonly selectedCategory = input<string | null>(null);

  readonly searchChange = output<string>();
  readonly categorySelect = output<string>();

  onSearchInput(value: string): void {
    this.searchChange.emit(value);
  }

  onFilterClick(category: string): void {
    this.categorySelect.emit(category);
  }
}
