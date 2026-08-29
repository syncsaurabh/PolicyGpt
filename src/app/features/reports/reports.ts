import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './reports.html',
  styleUrl: './reports.css',
})
export class Reports {}
