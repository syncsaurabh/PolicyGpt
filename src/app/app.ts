import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AssistantPopupComponent } from './features/assistant/assistant-popup/assistant-popup.component';

@Component({
  imports: [RouterOutlet, AssistantPopupComponent],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('policy-gpt-frontend');
}

