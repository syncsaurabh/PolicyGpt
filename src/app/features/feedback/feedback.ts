import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './feedback.html',
  styleUrl: './feedback.css',
})
export class Feedback {}
