import { Component, Input, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DistributionItem } from '../../../../models/analytics.model';

@Component({
  selector: 'app-distribution-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './distribution-chart.component.html',
  styleUrl: './distribution-chart.component.css'
})
export class DistributionChartComponent {
  @Input() title: string = '';
  @Input() subtitle?: string;
  @Input() chartType: 'horizontal-bar' | 'donut' | 'badge-list' = 'horizontal-bar';
  @Input() totalLabel: string = 'Total';
  @Input() loading: boolean = false;
  @Input() maxItems: number = 6;
  @Input() emptyMessage: string = 'No distribution data available';

  private readonly _items = signal<DistributionItem[]>([]);

  @Input()
  set items(val: DistributionItem[] | null | undefined) {
    this._items.set(val || []);
  }

  get items(): DistributionItem[] {
    return this._items();
  }

  // Predefined vibrant palette
  private readonly PALETTE = [
    '#2563EB', // Blue
    '#10B981', // Emerald
    '#8B5CF6', // Violet
    '#F59E0B', // Amber
    '#06B6D4', // Cyan
    '#EC4899', // Pink
    '#F43F5E', // Rose
    '#6366F1', // Indigo
    '#14B8A6', // Teal
    '#84CC16'  // Lime
  ];

  total = computed(() => {
    return this._items().reduce((acc, curr) => acc + (curr.count || 0), 0);
  });

  displayItems = computed(() => {
    const list = [...this._items()].sort((a, b) => (b.count || 0) - (a.count || 0));
    const totalVal = this.total() || 1;
    const sliced = list.slice(0, this.maxItems);

    return sliced.map((item, idx) => ({
      name: item.name || 'Unspecified',
      count: item.count,
      percentage: Math.round(((item.count || 0) / totalVal) * 100),
      color: this.PALETTE[idx % this.PALETTE.length]
    }));
  });

  // For donut chart calculation (SVG stroke-dasharray)
  donutSlices = computed(() => {
    const list = this.displayItems();
    const totalVal = this.total() || 1;
    let cumulative = 0;
    const circumference = 2 * Math.PI * 40; // r=40

    return list.map((item) => {
      const sliceLength = (item.count / totalVal) * circumference;
      const strokeDasharray = `${sliceLength} ${circumference - sliceLength}`;
      const strokeDashoffset = -cumulative;
      cumulative += sliceLength;

      return {
        ...item,
        strokeDasharray,
        strokeDashoffset
      };
    });
  });
}
