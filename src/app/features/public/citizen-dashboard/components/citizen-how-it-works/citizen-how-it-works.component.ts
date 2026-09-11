import { Component } from '@angular/core';

export interface HowItWorksStep {
  step: string;
  icon: string;
  title: string;
  description: string;
}

@Component({
  selector: 'app-citizen-how-it-works',
  standalone: true,
  templateUrl: './citizen-how-it-works.component.html',
  styleUrl: './citizen-how-it-works.component.scss'
})
export class CitizenHowItWorksComponent {
  readonly steps: HowItWorksStep[] = [
    {
      step: '01',
      icon: 'search',
      title: 'Search',
      description: 'Find policies and schemes that match your needs'
    },
    {
      step: '02',
      icon: 'description',
      title: 'Understand',
      description: 'Understand eligibility, benefits and requirements.'
    },
    {
      step: '03',
      icon: 'check',
      title: 'Take Action',
      description: 'Know the application process and next steps.'
    }
  ];
}
