import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-approvals',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './approvals.html',
  styleUrl: './approvals.css',
})
export class Approvals {}
