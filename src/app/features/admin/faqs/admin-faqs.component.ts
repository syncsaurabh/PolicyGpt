import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FaqService } from '../../../core/services/faq.service';
import { FAQCreatePayload, FAQItem, FAQUpdatePayload } from '../../../models/faq.model';

@Component({
  selector: 'app-admin-faqs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-faqs.component.html',
  styleUrl: './admin-faqs.component.css'
})
export class AdminFaqsComponent implements OnInit {
  private readonly faqService = inject(FaqService);

  // FAQ List & Table State
  protected faqs = signal<FAQItem[]>([]);
  protected isLoading = signal<boolean>(true);
  protected errorMessage = signal<string | null>(null);
  protected successMessage = signal<string | null>(null);

  // Search & Filter State
  protected searchQuery = signal<string>('');
  protected selectedCategory = signal<string>('All');
  protected selectedStatus = signal<string>('ALL'); // ALL, ACTIVE, INACTIVE

  // Modal State
  protected isCreateEditModalOpen = signal<boolean>(false);
  protected isDeleteModalOpen = signal<boolean>(false);
  protected isSubmitting = signal<boolean>(false);
  protected modalMode = signal<'create' | 'edit'>('create');
  protected editingFaqId = signal<number | null>(null);
  protected deletingFaq = signal<FAQItem | null>(null);

  // Form Model
  protected formQuestion = '';
  protected formAnswer = '';
  protected formCategory = 'Schemes & Applications';
  protected formDisplayOrder = 0;
  protected formIsActive = true;
  protected formError = '';

  // Preset categories for easy selection
  protected presetCategories: string[] = [
    'Schemes & Applications',
    'Eligibility',
    'Documentation',
    'Applications',
    'Comparison',
    'Portal Support',
    'General Guidelines'
  ];

  // Derived Categories from current FAQs
  protected availableCategories = computed<string[]>(() => {
    const list = this.faqs().map(f => f.category).filter(Boolean);
    return Array.from(new Set(['All', ...this.presetCategories, ...list]));
  });

  // Filtered FAQs computed list
  protected filteredFaqs = computed<FAQItem[]>(() => {
    const query = this.searchQuery().toLowerCase().trim();
    const cat = this.selectedCategory();
    const status = this.selectedStatus();

    return this.faqs().filter(item => {
      // Category match
      const matchCat = cat === 'All' || (item.category && item.category.toLowerCase() === cat.toLowerCase());
      
      // Status match
      const isActive = item.is_active !== false;
      const matchStatus = status === 'ALL' || (status === 'ACTIVE' ? isActive : !isActive);

      // Search query match
      const matchQuery = !query || 
        item.question.toLowerCase().includes(query) || 
        item.answer.toLowerCase().includes(query) || 
        (item.category && item.category.toLowerCase().includes(query));

      return matchCat && matchStatus && matchQuery;
    });
  });

  // Metrics
  protected totalCount = computed(() => this.faqs().length);
  protected activeCount = computed(() => this.faqs().filter(f => f.is_active !== false).length);
  protected categoryCount = computed(() => new Set(this.faqs().map(f => f.category)).size);

  ngOnInit(): void {
    this.loadFaqs();
  }

  loadFaqs(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.faqService.getFAQs({ page_size: 100 }).subscribe({
      next: (response) => {
        this.faqs.set(response.results || []);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching FAQs for admin:', err);
        this.isLoading.set(false);
        this.errorMessage.set(this.extractErrorMessage(err, 'Failed to load FAQs. Please try again.'));
      }
    });
  }

  openCreateModal(): void {
    this.modalMode.set('create');
    this.editingFaqId.set(null);
    this.formQuestion = '';
    this.formAnswer = '';
    this.formCategory = 'Schemes & Applications';
    this.formDisplayOrder = this.faqs().length;
    this.formIsActive = true;
    this.formError = '';
    this.isCreateEditModalOpen.set(true);
  }

  openEditModal(faq: FAQItem): void {
    this.modalMode.set('edit');
    this.editingFaqId.set(faq.id);
    this.formQuestion = faq.question;
    this.formAnswer = faq.answer;
    this.formCategory = faq.category || 'General';
    this.formDisplayOrder = faq.display_order ?? 0;
    this.formIsActive = faq.is_active !== false;
    this.formError = '';
    this.isCreateEditModalOpen.set(true);
  }

  closeCreateEditModal(): void {
    this.isCreateEditModalOpen.set(false);
    this.formError = '';
  }

  saveFaq(): void {
    if (!this.formQuestion.trim()) {
      this.formError = 'Please enter a valid FAQ question.';
      return;
    }
    if (!this.formAnswer.trim()) {
      this.formError = 'Please provide an answer for this FAQ.';
      return;
    }

    this.isSubmitting.set(true);
    this.formError = '';

    if (this.modalMode() === 'create') {
      const payload: FAQCreatePayload = {
        question: this.formQuestion.trim(),
        answer: this.formAnswer.trim(),
        category: this.formCategory.trim() || 'General',
        display_order: Number(this.formDisplayOrder) || 0,
        is_active: this.formIsActive
      };

      this.faqService.createFAQ(payload).subscribe({
        next: (created) => {
          this.isSubmitting.set(false);
          this.isCreateEditModalOpen.set(false);
          this.showSuccess(`FAQ "${created.question.slice(0, 40)}..." created successfully!`);
          this.loadFaqs();
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.formError = this.extractErrorMessage(err, 'Failed to create FAQ. Please verify inputs.');
        }
      });
    } else {
      const id = this.editingFaqId();
      if (!id) return;

      const payload: FAQUpdatePayload = {
        question: this.formQuestion.trim(),
        answer: this.formAnswer.trim(),
        category: this.formCategory.trim() || 'General',
        display_order: Number(this.formDisplayOrder) || 0,
        is_active: this.formIsActive
      };

      this.faqService.updateFAQ(id, payload).subscribe({
        next: (updated) => {
          this.isSubmitting.set(false);
          this.isCreateEditModalOpen.set(false);
          this.showSuccess(`FAQ #${updated.id} updated successfully!`);
          this.loadFaqs();
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.formError = this.extractErrorMessage(err, 'Failed to update FAQ.');
        }
      });
    }
  }

  toggleActiveStatus(faq: FAQItem, event: Event): void {
    event.stopPropagation();
    const newStatus = !(faq.is_active !== false);

    this.faqService.updateFAQ(faq.id, { is_active: newStatus }).subscribe({
      next: () => {
        this.showSuccess(`FAQ #${faq.id} is now ${newStatus ? 'Published' : 'Hidden / Draft'}.`);
        this.loadFaqs();
      },
      error: (err) => {
        this.errorMessage.set(this.extractErrorMessage(err, 'Failed to toggle FAQ status.'));
      }
    });
  }

  openDeleteModal(faq: FAQItem, event: Event): void {
    event.stopPropagation();
    this.deletingFaq.set(faq);
    this.isDeleteModalOpen.set(true);
  }

  closeDeleteModal(): void {
    this.isDeleteModalOpen.set(false);
    this.deletingFaq.set(null);
  }

  confirmDelete(): void {
    const faq = this.deletingFaq();
    if (!faq) return;

    this.isSubmitting.set(true);
    this.faqService.deleteFAQ(faq.id).subscribe({
      next: () => {
        this.isSubmitting.set(false);
        this.isDeleteModalOpen.set(false);
        this.deletingFaq.set(null);
        this.showSuccess(`FAQ #${faq.id} deleted successfully.`);
        this.loadFaqs();
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.errorMessage.set(this.extractErrorMessage(err, 'Failed to delete FAQ.'));
      }
    });
  }

  private extractErrorMessage(err: any, fallback: string): string {
    if (!err) return fallback;
    if (typeof err === 'string') return err;
    if (err.error) {
      if (typeof err.error === 'string') return err.error;
      if (typeof err.error.detail === 'string') return err.error.detail;
      if (Array.isArray(err.error.detail)) {
        return err.error.detail.map((d: any) => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(', ');
      }
      if (err.error.detail && typeof err.error.detail === 'object') {
        return err.error.detail.msg || err.error.detail.message || JSON.stringify(err.error.detail);
      }
      if (err.error.message && typeof err.error.message === 'string') return err.error.message;
    }
    if (err.message && typeof err.message === 'string') return err.message;
    return fallback;
  }

  private showSuccess(msg: string): void {
    this.successMessage.set(msg);
    setTimeout(() => {
      this.successMessage.set(null);
    }, 4500);
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.selectedCategory.set('All');
    this.selectedStatus.set('ALL');
  }
}
