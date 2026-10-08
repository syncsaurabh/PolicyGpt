import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { CitizenHeaderComponent } from '../citizen-dashboard/components/citizen-header/citizen-header.component';
import { CitizenFooterComponent } from '../citizen-dashboard/components/citizen-footer/citizen-footer.component';
import { FaqService } from '../../../core/services/faq.service';
import { AssistantService } from '../../../core/services/assistant.service';
import { FAQItem } from '../../../models/faq.model';
import { ChatResponse } from '../../../models/assistant.model';

@Component({
  selector: 'app-public-faqs',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    CitizenHeaderComponent,
    CitizenFooterComponent
  ],
  templateUrl: './public-faqs.component.html',
  styleUrl: './public-faqs.component.css'
})
export class PublicFaqsComponent implements OnInit {
  private readonly faqService = inject(FaqService);
  protected readonly assistantService = inject(AssistantService);
  private readonly route = inject(ActivatedRoute);

  // FAQ State
  protected faqs = signal<FAQItem[]>([]);
  protected isLoading = signal<boolean>(true);
  protected errorMessage = signal<string | null>(null);

  // Search & Filter State
  protected searchQuery = signal<string>('');
  protected searchInputModel = '';
  protected selectedCategory = signal<string>('All');
  protected expandedFaqIds = signal<Set<number>>(new Set());

  // Interactive Feedback & Copy State
  protected copiedFaqId = signal<number | null>(null);
  protected helpfulVotes = signal<Map<number, boolean>>(new Map());

  // AI Assistant Live Answer State
  protected aiQuery = signal<string>('');
  protected isAiThinking = signal<boolean>(false);
  protected aiResponse = signal<ChatResponse | null>(null);
  protected aiError = signal<string | null>(null);

  // Dynamic Categories derived from loaded FAQs
  protected categories = computed<string[]>(() => {
    const defaultCategories = ['All', 'Schemes & Applications', 'Eligibility', 'Documentation', 'Applications', 'Comparison'];
    const loadedCategories = this.faqs().map(f => f.category).filter(Boolean);
    const combined = Array.from(new Set([...defaultCategories, ...loadedCategories]));
    return combined;
  });

  // Filtered FAQs computed signal
  protected filteredFaqs = computed<FAQItem[]>(() => {
    const list = this.faqs();
    const query = this.searchQuery().toLowerCase().trim();
    const category = this.selectedCategory();

    return list.filter(item => {
      const matchCategory = category === 'All' || item.category.toLowerCase() === category.toLowerCase();
      const matchQuery = !query || 
        item.question.toLowerCase().includes(query) || 
        item.answer.toLowerCase().includes(query) || 
        (item.category && item.category.toLowerCase().includes(query));
      return matchCategory && matchQuery;
    });
  });

  // Category counts
  protected getCategoryCount(cat: string): number {
    if (cat === 'All') return this.faqs().length;
    return this.faqs().filter(f => f.category.toLowerCase() === cat.toLowerCase()).length;
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if (params['category']) {
        this.selectedCategory.set(params['category']);
      }
      if (params['q']) {
        this.searchQuery.set(params['q']);
        this.searchInputModel = params['q'];
      }
    });

    this.loadFaqs();
  }

  loadFaqs(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.faqService.getFAQs({ page_size: 100 }).subscribe({
      next: (response) => {
        const results = response.results || [];
        this.faqs.set(results);
        this.isLoading.set(false);

        // Auto-expand first 2 FAQs by default for great UX
        if (results.length > 0) {
          const initialSet = new Set<number>();
          results.slice(0, 2).forEach(f => initialSet.add(f.id));
          this.expandedFaqIds.set(initialSet);
        }
      },
      error: (err) => {
        console.error('Error loading FAQs:', err);
        this.isLoading.set(false);
        this.errorMessage.set('Unable to load FAQs at the moment. Please try again later.');
      }
    });
  }

  onSearchSubmit(): void {
    const q = this.searchInputModel.trim();
    this.searchQuery.set(q);

    // If search looks like a natural language question, also trigger AI Live answer
    if (q.length > 5 && (q.includes('?') || q.toLowerCase().startsWith('how') || q.toLowerCase().startsWith('what') || q.toLowerCase().startsWith('can') || q.toLowerCase().startsWith('am i'))) {
      this.askAiAssistant(q);
    }
  }

  onCategorySelect(category: string): void {
    this.selectedCategory.set(category);
  }

  toggleFaq(id: number): void {
    this.expandedFaqIds.update(set => {
      const next = new Set(set);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  isExpanded(id: number): boolean {
    return this.expandedFaqIds().has(id);
  }

  expandAll(): void {
    const allIds = new Set(this.filteredFaqs().map(f => f.id));
    this.expandedFaqIds.set(allIds);
  }

  collapseAll(): void {
    this.expandedFaqIds.set(new Set());
  }

  copyAnswer(faq: FAQItem, event: MouseEvent): void {
    event.stopPropagation();
    const textToCopy = `Q: ${faq.question}\n\nA: ${faq.answer}\n\n(Source: PolicyGPT AI Help Desk)`;
    navigator.clipboard.writeText(textToCopy).then(() => {
      this.copiedFaqId.set(faq.id);
      setTimeout(() => {
        if (this.copiedFaqId() === faq.id) {
          this.copiedFaqId.set(null);
        }
      }, 2500);
    });
  }

  voteHelpful(faqId: number, isHelpful: boolean, event: MouseEvent): void {
    event.stopPropagation();
    this.helpfulVotes.update(map => {
      const next = new Map(map);
      next.set(faqId, isHelpful);
      return next;
    });
  }

  getVote(faqId: number): boolean | undefined {
    return this.helpfulVotes().get(faqId);
  }

  askAssistantAbout(faq: FAQItem, event: MouseEvent): void {
    event.stopPropagation();
    const prompt = `Tell me more details about: ${faq.question}`;
    this.assistantService.openPopup(prompt);
  }

  askAiAssistant(prompt?: string): void {
    const query = (prompt ?? this.searchInputModel).trim();
    if (!query) return;

    this.aiQuery.set(query);
    this.isAiThinking.set(true);
    this.aiError.set(null);
    this.aiResponse.set(null);

    this.assistantService.sendChatMessage({ message: query }).subscribe({
      next: (res) => {
        this.aiResponse.set(res);
        this.isAiThinking.set(false);
      },
      error: (err) => {
        console.error('Error querying AI assistant:', err);
        this.isAiThinking.set(false);
        this.aiError.set('Could not fetch AI response. Please try again or open the AI popup.');
      }
    });
  }

  dismissAiAnswer(): void {
    this.aiResponse.set(null);
    this.aiError.set(null);
    this.aiQuery.set('');
  }

  openFullAssistant(initialPrompt?: string): void {
    this.assistantService.openPopup(initialPrompt || this.aiQuery());
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.searchInputModel = '';
    this.selectedCategory.set('All');
  }
}
