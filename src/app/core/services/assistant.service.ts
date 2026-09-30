import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ChatRequest,
  ChatResponse,
  ConversationDetailResponse,
  ConversationListResponse
} from '../../models/assistant.model';
import { MessageResponse } from '../../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class AssistantService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  // Global popup visibility signal
  readonly isPopupOpen = signal<boolean>(false);
  // Optional pre-filled/auto-dispatched prompt
  readonly pendingPrompt = signal<string | null>(null);
  // Reactive session reset trigger for user/role transitions
  readonly sessionResetTrigger = signal<number>(0);

  /**
   * Completely reset AI Assistant session state across frontend.
   * Closes the popup, clears any pending prompts or cached storage,
   * and signals all components to purge message history and conversation IDs.
   */
  resetSession(): void {
    this.isPopupOpen.set(false);
    this.pendingPrompt.set(null);
    this.sessionResetTrigger.update((count) => count + 1);

    // Clean up any assistant storage items if present
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('assistant') || key.startsWith('chat_'))) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach((k) => localStorage.removeItem(k));

      const sessionKeys: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && (key.startsWith('assistant') || key.startsWith('chat_'))) {
          sessionKeys.push(key);
        }
      }
      sessionKeys.forEach((k) => sessionStorage.removeItem(k));
    } catch (e) {
      console.warn('Could not clean assistant storage on reset:', e);
    }
  }

  /**
   * Toggle the AI Assistant floating popup
   */
  togglePopup(): void {
    this.isPopupOpen.update((open) => !open);
  }

  /**
   * Open the AI Assistant floating popup, optionally triggering or pre-filling a prompt
   */
  openPopup(prompt?: string): void {
    this.isPopupOpen.set(true);
    if (prompt) {
      this.pendingPrompt.set(prompt);
    }
  }

  /**
   * Close the AI Assistant floating popup
   */
  closePopup(): void {
    this.isPopupOpen.set(false);
  }

  /**
   * Clear the pending prompt once consumed
   */
  clearPendingPrompt(): void {
    this.pendingPrompt.set(null);
  }

  /**
   * Interactive PolicyGPT AI Assistant Chat
   * POST /api/v1/assistant/chat
   */
  sendChatMessage(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/assistant/chat`, request);
  }

  /**
   * List user's active AI conversation sessions
   * GET /api/v1/assistant/conversations
   */
  getConversations(limit: number = 20): Observable<ConversationListResponse> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<ConversationListResponse>(`${this.apiUrl}/assistant/conversations`, { params });
  }

  /**
   * Get conversation session message history
   * GET /api/v1/assistant/conversations/{id}
   */
  getConversationHistory(id: string): Observable<ConversationDetailResponse> {
    return this.http.get<ConversationDetailResponse>(`${this.apiUrl}/assistant/conversations/${encodeURIComponent(id)}`);
  }

  /**
   * Delete a conversation session
   * DELETE /api/v1/assistant/conversations/{id}
   */
  deleteConversation(id: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${this.apiUrl}/assistant/conversations/${encodeURIComponent(id)}`);
  }
}
