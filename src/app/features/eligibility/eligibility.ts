import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-eligibility',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './eligibility.html',
  styleUrl: './eligibility.css',
})
export class Eligibility {}
