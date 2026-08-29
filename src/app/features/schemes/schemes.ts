import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-schemes',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './schemes.html',
  styleUrl: './schemes.css',
})
export class Schemes {}
