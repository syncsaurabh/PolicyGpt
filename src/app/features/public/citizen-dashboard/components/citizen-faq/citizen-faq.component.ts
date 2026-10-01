import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FaqService } from '../../../../../core/services/faq.service';
import { AssistantService } from '../../../../../core/services/assistant.service';
import { FAQItem } from '../../../../../models/faq.model';

@Component({
  selector: 'app-citizen-faq',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './citizen-faq.component.html',
  styleUrl: './citizen-faq.component.css'
})
export class CitizenFaqComponent implements OnInit {
  private readonly faqService = inject(FaqService);
  protected readonly assistantService = inject(AssistantService);

  protected faqs = signal<FAQItem[]>([]);
  protected selectedCategory = signal<string>('All');
  protected categories = signal<string[]>(['All', 'Schemes & Applications', 'Eligibility', 'Documentation', 'Applications']);
  protected expandedId = signal<number | null>(null);
  protected isLoading = signal<boolean>(true);

  ngOnInit(): void {
    this.loadFaqs();
  }

  loadFaqs(): void {
    this.isLoading.set(true);
    this.faqService.getFAQs({ page_size: 10 }).subscribe({
      next: (res) => {
        const results = res.results || [];
        this.faqs.set(results);
        if (results.length > 0) {
          this.expandedId.set(results[0].id);
        }
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  setCategory(category: string): void {
    this.selectedCategory.set(category);
  }

  get filteredFaqs(): FAQItem[] {
    const cat = this.selectedCategory();
    if (cat === 'All') return this.faqs().slice(0, 5);
    return this.faqs().filter(f => f.category.toLowerCase() === cat.toLowerCase()).slice(0, 5);
  }

  toggleFaq(id: number): void {
    this.expandedId.update(curr => (curr === id ? null : id));
  }

  askAssistant(question: string, event: MouseEvent): void {
    event.stopPropagation();
    this.assistantService.openPopup(`Tell me more about: ${question}`);
  }
}
