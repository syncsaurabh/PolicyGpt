import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-policies',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './policies.html',
  styleUrl: './policies.css',
})
export class Policies {}
