import { Component, input, output } from '@angular/core';

export interface CategoryItem {
  id: string;
  name: string;
  icon: string;
  description: string;
}

@Component({
  selector: 'app-citizen-categories',
  standalone: true,
  templateUrl: './citizen-categories.component.html',
  styleUrl: './citizen-categories.component.css'
})
export class CitizenCategoriesComponent {
  readonly selectedCategory = input<string | null>(null);
  readonly categorySelect = output<string>();

  readonly categories: CategoryItem[] = [
    {
      id: 'education',
      name: 'Education',
      icon: '🎓',
      description: 'Scholarships, education support and student schemes'
    },
    {
      id: 'employment',
      name: 'Employment',
      icon: '💼',
      description: 'Jobs, skill development and employment support'
    },
    {
      id: 'agriculture',
      name: 'Agriculture',
      icon: '🌾',
      description: 'Farming support, subsidies and agricultural schemes'
    },
    {
      id: 'women',
      name: 'Women',
      icon: '👩',
      description: 'Women empowerment, safety and welfare schemes'
    },
    {
      id: 'housing',
      name: 'Housing',
      icon: '🏠',
      description: 'Affordable housing, home loans and housing assistance'
    },
    {
      id: 'healthcare',
      name: 'Healthcare',
      icon: '🏥',
      description: 'Health insurance, medical support and healthcare schemes'
    }
  ];

  onSelect(name: string): void {
    this.categorySelect.emit(name);
  }
}
