import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-citizen-assistant',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './citizen-assistant.component.html',
  styleUrl: './citizen-assistant.component.scss'
})
export class CitizenAssistantComponent {
  protected assistantQuery = signal<string>('');
  protected assistantAnswer = signal<string | null>(null);
  protected isAssistantThinking = signal<boolean>(false);

  askAssistant(prompt?: string): void {
    const query = (prompt ?? this.assistantQuery()).trim();
    if (!query) return;

    this.assistantQuery.set(query);
    this.isAssistantThinking.set(true);
    this.assistantAnswer.set(null);

    setTimeout(() => {
      this.isAssistantThinking.set(false);
      const lower = query.toLowerCase();
      if (lower.includes('pm-kisan')) {
        this.assistantAnswer.set(
          'Under PM-KISAN (Pradhan Mantri Kisan Samman Nidhi), all landholding farmer families with cultivable landholding in their names are eligible for income support of ₹6,000 per year distributed in three equal installments. Institutional landholders and tax-paying families are excluded.'
        );
      } else if (lower.includes('scholarship') || lower.includes('student')) {
        this.assistantAnswer.set(
          'The National Scholarship Portal (NSP) hosts Central, UGC/AICTE, and State scholarship schemes for pre-matric, post-matric, and higher education. Eligibility is based on verified family income thresholds and academic merit.'
        );
      } else if (lower.includes('health') || lower.includes('family') || lower.includes('ayushman')) {
        this.assistantAnswer.set(
          'Ayushman Bharat (PM-JAY) offers secondary and tertiary health coverage up to ₹5 lakh per family per year. Beneficiaries are identified based on deprivation and occupational criteria from the SECC database. Check your status at nearest Ayushman Mitra or online portal.'
        );
      } else {
        this.assistantAnswer.set(
          `Based on PolicyGPT intelligence regarding "${query}": Multiple central and state programs provide benefits for eligible citizens. Explore the categories above or register an account for automated eligibility matching and personalized scheme notifications.`
        );
      }
    }, 400);
  }

  dismissAnswer(): void {
    this.assistantAnswer.set(null);
  }
}
