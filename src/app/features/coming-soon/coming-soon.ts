import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-coming-soon',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './coming-soon.html',
  styleUrl: './coming-soon.css',
})
export class ComingSoonComponent {
  @Input() featureTitle = 'Feature Coming Soon';
  @Input() description = 'This feature is currently under development. We’re working to bring this functionality to you.';
}
