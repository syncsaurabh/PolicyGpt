import { Component } from '@angular/core';
import { ComingSoonComponent } from '../coming-soon/coming-soon';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './notifications.html',
  styleUrl: './notifications.css',
})
export class Notifications {}
