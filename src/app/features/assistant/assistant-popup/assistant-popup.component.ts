import {
  Component,
  inject,
  signal,
  effect,
  untracked,
  ViewChild,
  ElementRef,
  AfterViewChecked
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AssistantService } from '../../../core/services/assistant.service';
import { AuthService } from '../../../core/services/auth.service';
import {
  AssistantChatMessage,
  ChatRequest,
  ChatResponse,
  ConversationListItem,
  SourceCitation
} from '../../../models/assistant.model';

@Component({
  selector: 'app-assistant-popup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assistant-popup.component.html',
  styleUrl: './assistant-popup.component.css'
})
export class AssistantPopupComponent implements AfterViewChecked {
  protected readonly assistantService = inject(AssistantService);
  protected readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  @ViewChild('messagesContainer') private messagesContainer?: ElementRef<HTMLDivElement>;
  @ViewChild('chatInput') private chatInput?: ElementRef<HTMLTextAreaElement>;

  // Track authenticated user identity to prevent cross-user data leaks
  private lastUserId = signal<number | string | null>(this.authService.currentUser()?.id ?? null);
  private lastUserRole = signal<string | null>(this.authService.currentUser()?.role ?? null);

  // Chat conversation state
  protected activeConversationId = signal<string | null>(null);
  protected activeConversationTitle = signal<string | null>(null);
  protected messages = signal<AssistantChatMessage[]>([]);
  protected inputText = signal<string>('');
  protected isLoading = signal<boolean>(false);
  protected errorMessage = signal<string | null>(null);

  // History drawer state
  protected isHistoryOpen = signal<boolean>(false);
  protected conversations = signal<ConversationListItem[]>([]);
  protected isLoadingConversations = signal<boolean>(false);
  protected deletingConversationId = signal<string | null>(null);

  // Suggested starting questions
  protected readonly defaultSuggestions = [
    'Find government schemes',
    'Check scheme eligibility',
    'Compare schemes',
    'How do I apply?'
  ];

  private shouldScrollToBottom = false;

  constructor() {
    // 1. Strict Identity and Role Isolation Watcher
    effect(() => {
      const currentUser = this.authService.currentUser();
      const currentUserId = currentUser?.id ?? null;
      const currentUserRole = currentUser?.role ?? null;
      const resetTrigger = this.assistantService.sessionResetTrigger();

      const previousUserId = untracked(() => this.lastUserId());
      const previousUserRole = untracked(() => this.lastUserRole());

      const userChanged = currentUserId !== previousUserId || currentUserRole !== previousUserRole;

      if (userChanged || resetTrigger > 0) {
        // Update stored identity snapshots
        this.lastUserId.set(currentUserId);
        this.lastUserRole.set(currentUserRole);

        // Completely reset all local assistant conversation & history state
        this.clearAllAssistantState();

        // If logged out, ensure popup is closed
        if (!currentUserId) {
          this.assistantService.closePopup();
        } else if (this.assistantService.isPopupOpen()) {
          // If a new user logged in with popup active, fetch their isolated sessions
          this.loadConversations();
        }
      }
    });

    // 2. External prompts trigger handler
    effect(() => {
      const pendingPrompt = this.assistantService.pendingPrompt();
      if (pendingPrompt) {
        this.assistantService.clearPendingPrompt();
        this.sendMessage(pendingPrompt);
      }
    });

    // 3. Popup visibility handler
    effect(() => {
      const isOpen = this.assistantService.isPopupOpen();
      if (isOpen) {
        this.shouldScrollToBottom = true;
        if (this.authService.authenticated()) {
          this.loadConversations();
        }
        setTimeout(() => this.focusInput(), 150);
      }
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  /**
   * Resets all in-memory chat state and cached data
   */
  private clearAllAssistantState(): void {
    this.activeConversationId.set(null);
    this.activeConversationTitle.set(null);
    this.messages.set([]);
    this.conversations.set([]);
    this.errorMessage.set(null);
    this.isLoading.set(false);
    this.isHistoryOpen.set(false);
    this.inputText.set('');
  }

  togglePopup(): void {
    this.assistantService.togglePopup();
  }

  closePopup(): void {
    this.assistantService.closePopup();
  }

  toggleHistory(): void {
    const next = !this.isHistoryOpen();
    this.isHistoryOpen.set(next);
    if (next && this.authService.authenticated()) {
      this.loadConversations();
    }
  }

  startNewChat(): void {
    this.activeConversationId.set(null);
    this.activeConversationTitle.set(null);
    this.messages.set([]);
    this.errorMessage.set(null);
    this.isHistoryOpen.set(false);
    this.focusInput();
  }

  loadConversations(): void {
    if (!this.authService.authenticated()) {
      this.conversations.set([]);
      return;
    }

    this.isLoadingConversations.set(true);
    this.assistantService.getConversations(30).subscribe({
      next: (res) => {
        this.conversations.set(res.results || []);
        this.isLoadingConversations.set(false);
      },
      error: (err) => {
        console.warn('Could not load AI conversations:', err);
        this.isLoadingConversations.set(false);
      }
    });
  }

  selectConversation(conv: ConversationListItem): void {
    // If user is not authenticated or switched, abort
    if (!this.authService.authenticated()) return;

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.activeConversationId.set(conv.id);
    this.activeConversationTitle.set(conv.title);
    this.isHistoryOpen.set(false);

    this.assistantService.getConversationHistory(conv.id).subscribe({
      next: (detail) => {
        const loadedMessages: AssistantChatMessage[] = (detail.messages || []).map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          sources: m.sources,
          intent: m.intent,
          created_at: m.created_at
        }));
        this.messages.set(loadedMessages);
        this.isLoading.set(false);
        this.shouldScrollToBottom = true;
      },
      error: (err) => {
        this.isLoading.set(false);
        this.handleApiError(err);
      }
    });
  }

  deleteConversation(event: Event, convId: string): void {
    event.stopPropagation();
    if (!this.authService.authenticated()) return;

    this.deletingConversationId.set(convId);

    this.assistantService.deleteConversation(convId).subscribe({
      next: () => {
        this.conversations.update((list) => list.filter((c) => c.id !== convId));
        this.deletingConversationId.set(null);
        if (this.activeConversationId() === convId) {
          this.startNewChat();
        }
      },
      error: (err) => {
        this.deletingConversationId.set(null);
        console.error('Failed to delete AI conversation:', err);
      }
    });
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  sendMessage(customPrompt?: string): void {
    const raw = customPrompt ?? this.inputText();
    const messageText = raw?.trim();

    if (!messageText || this.isLoading()) return;

    this.errorMessage.set(null);
    this.inputText.set('');

    const userMessage: AssistantChatMessage = {
      role: 'user',
      content: messageText,
      created_at: new Date().toISOString()
    };

    this.messages.update((list) => [...list, userMessage]);
    this.isLoading.set(true);
    this.shouldScrollToBottom = true;

    const payload: ChatRequest = {
      message: messageText,
      conversation_id: this.activeConversationId() || undefined
    };

    this.assistantService.sendChatMessage(payload).subscribe({
      next: (res: ChatResponse) => {
        const aiMessage: AssistantChatMessage = {
          role: 'assistant',
          content: res.answer,
          sources: res.sources,
          intent: res.intent,
          suggested_questions: res.suggested_questions,
          created_at: res.created_at || new Date().toISOString()
        };

        this.messages.update((list) => [...list, aiMessage]);
        this.activeConversationId.set(res.conversation_id);
        this.isLoading.set(false);
        this.shouldScrollToBottom = true;

        if (this.authService.authenticated()) {
          this.loadConversations();
        }
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading.set(false);
        this.handleApiError(err);
        this.shouldScrollToBottom = true;
      }
    });
  }

  retryLast(): void {
    const list = this.messages();
    if (!list.length) return;
    const lastUserMsg = [...list].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      this.sendMessage(lastUserMsg.content);
    }
  }

  navigateToSource(source: SourceCitation): void {
    if (source.url) {
      if (source.url.startsWith('http://') || source.url.startsWith('https://')) {
        window.open(source.url, '_blank', 'noopener,noreferrer');
      } else {
        this.router.navigateByUrl(source.url);
      }
      return;
    }

    const isAuth = this.authService.authenticated();
    if (source.type === 'scheme' && source.id) {
      this.router.navigate([isAuth ? '/schemes' : '/public/schemes', source.id]);
    } else if (source.type === 'policy' && source.id) {
      this.router.navigate([isAuth ? '/policies' : '/public/policies', source.id]);
    } else if (source.type === 'comparison') {
      this.router.navigate(['/compare']);
    } else if (source.type === 'eligibility') {
      this.router.navigate(['/eligibility']);
    } else {
      this.router.navigate(['/citizen'], { fragment: 'popular-schemes' });
    }
  }

  private handleApiError(error: HttpErrorResponse): void {
    if (error.status === 401) {
      this.errorMessage.set('Your session has expired. Please log in to continue.');
    } else if (error.status === 403) {
      this.errorMessage.set('You do not have permission to perform this action or access this conversation.');
    } else if (error.status === 400 || error.status === 422) {
      const detail = error.error?.detail;
      if (typeof detail === 'string') {
        this.errorMessage.set(detail);
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        this.errorMessage.set(detail[0].msg);
      } else {
        this.errorMessage.set('Unable to process the request. Please check your query.');
      }
    } else if (error.status === 500) {
      this.errorMessage.set("Sorry, I couldn't process your request right now. Please try again.");
    } else {
      this.errorMessage.set('Network connection error. Please check your connection and retry.');
    }
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer?.nativeElement) {
        const el = this.messagesContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    } catch {
      // Ignored
    }
  }

  private focusInput(): void {
    try {
      this.chatInput?.nativeElement?.focus();
    } catch {
      // Ignored
    }
  }
}
