import { Component } from '@angular/core';
import { ComingSoonComponent } from '../../coming-soon/coming-soon';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class Users {}
