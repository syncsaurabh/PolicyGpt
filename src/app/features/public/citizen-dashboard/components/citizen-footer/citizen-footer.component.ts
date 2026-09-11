import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-citizen-footer',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './citizen-footer.component.html',
  styleUrl: './citizen-footer.component.scss'
})
export class CitizenFooterComponent {}
