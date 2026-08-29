import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-compare',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './compare.html',
  styleUrl: './compare.css',
})
export class Compare {}
