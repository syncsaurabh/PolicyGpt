import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './kpi-card.component.html',
  styleUrl: './kpi-card.component.css'
})
export class KpiCardComponent {
  @Input() title: string = '';
  @Input() value: string | number | null | undefined = '--';
  @Input() subtext?: string;
  @Input() badge?: string;
  @Input() badgeType: 'success' | 'warning' | 'info' | 'primary' | 'neutral' = 'primary';
  @Input() icon: string = 'analytics';
  @Input() color: 'primary' | 'emerald' | 'violet' | 'amber' | 'cyan' | 'rose' = 'primary';
  @Input() loading: boolean = false;
}
