import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AssistantService } from '../../../../../core/services/assistant.service';

@Component({
  selector: 'app-citizen-assistant',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './citizen-assistant.component.html',
  styleUrl: './citizen-assistant.component.css'
})
export class CitizenAssistantComponent {
  private readonly assistantService = inject(AssistantService);

  protected assistantQuery = signal<string>('');
  protected assistantAnswer = signal<string | null>(null);
  protected isAssistantThinking = signal<boolean>(false);

  askAssistant(prompt?: string): void {
    const query = (prompt ?? this.assistantQuery()).trim();
    if (!query) return;

    this.assistantQuery.set(query);
    this.assistantService.openPopup(query);
  }

  dismissAnswer(): void {
    this.assistantAnswer.set(null);
  }
}
