import { Component } from '@angular/core';
import { ComingSoonComponent } from '../../coming-soon/coming-soon';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [ComingSoonComponent],
  templateUrl: './audit-logs.html',
  styleUrl: './audit-logs.css',
})
export class AuditLogs {}
