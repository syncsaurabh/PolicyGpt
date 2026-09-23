import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Navbar } from '../navbar/navbar';
import { Sidebar } from '../sidebar/sidebar';
import { LayoutService } from '../../core/services/layout.service';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [Navbar, Sidebar, RouterOutlet],
  templateUrl: './dashboard-layout.html',
  styleUrl: './dashboard-layout.css',
})
export class DashboardLayout {
  protected readonly layoutService = inject(LayoutService);
}
