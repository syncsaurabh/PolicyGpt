import { Component, input, output, signal, computed } from '@angular/core';
import { RouterLink } from '@angular/router';

export interface SchemeItem {
  id: string;
  title: string;
  category: string;
  tagline: string;
  description: string;
  bookmarked?: boolean;
}

@Component({
  selector: 'app-citizen-schemes',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './citizen-schemes.component.html',
  styleUrl: './citizen-schemes.component.css'
})
export class CitizenSchemesComponent {
  readonly searchQuery = input<string>('');
  readonly selectedCategory = input<string | null>(null);

  readonly resetFilters = output<void>();

  // Popular Government Schemes definition
  protected schemes = signal<SchemeItem[]>([
    {
      id: 'pm-kisan',
      title: 'PM-KISAN',
      category: 'Agriculture',
      tagline: 'Financial support for eligible farmers.',
      description: 'Financial support for eligible farmers to support their agricultural needs.',
      bookmarked: false
    },
    {
      id: 'ayushman-bharat',
      title: 'Ayushman Bharat',
      category: 'Healthcare',
      tagline: 'Healthcare support for eligible families.',
      description: 'Healthcare support and financial protection for eligible families',
      bookmarked: false
    },
    {
      id: 'national-scholarship-portal',
      title: 'National Scholarship Portal',
      category: 'Education',
      tagline: 'Access scholarships and financial support for eligible students',
      description: 'A platform to access and apply for scholarships for eligible students.',
      bookmarked: false
    }
  ]);

  protected activeSchemeModal = signal<SchemeItem | null>(null);

  protected filteredSchemes = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const cat = this.selectedCategory()?.toLowerCase();
    
    return this.schemes().filter(scheme => {
      const matchesQuery = !q || 
        scheme.title.toLowerCase().includes(q) || 
        scheme.description.toLowerCase().includes(q) || 
        scheme.category.toLowerCase().includes(q);

      const matchesCategory = !cat || scheme.category.toLowerCase() === cat;

      return matchesQuery && matchesCategory;
    });
  });

  toggleBookmark(schemeId: string): void {
    this.schemes.update(current => 
      current.map(s => s.id === schemeId ? { ...s, bookmarked: !s.bookmarked } : s)
    );
  }

  viewDetails(scheme: SchemeItem): void {
    this.activeSchemeModal.set(scheme);
  }

  closeModal(): void {
    this.activeSchemeModal.set(null);
  }

  onReset(): void {
    this.resetFilters.emit();
  }
}
