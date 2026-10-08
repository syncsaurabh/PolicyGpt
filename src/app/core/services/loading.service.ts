import { Injectable, signal, computed } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  // Counter of all active in-flight HTTP requests
  private readonly _activeHttpRequests = signal<number>(0);

  // Map of granular action states (e.g., 'save-policy-123', 'delete-scheme-45', 'export-pdf')
  private readonly _activeActions = signal<Map<string, string>>(new Map());

  // Global loading signal: true if ANY HTTP request or registered action is running
  public readonly isGlobalLoading = computed(() => this._activeHttpRequests() > 0);
  public readonly activeRequestCount = this._activeHttpRequests.asReadonly();

  /**
   * Increment active HTTP request count (called by interceptor)
   */
  startRequest(): void {
    this._activeHttpRequests.update(count => count + 1);
  }

  /**
   * Decrement active HTTP request count (called by interceptor)
   */
  stopRequest(): void {
    this._activeHttpRequests.update(count => Math.max(0, count - 1));
  }

  /**
   * Reset request counter (failsafe on route change or session reset)
   */
  resetRequests(): void {
    this._activeHttpRequests.set(0);
    this._activeActions.set(new Map());
  }

  /**
   * Start a named action with an optional descriptive status text
   * @param actionKey unique identifier for the action, e.g. 'delete-faq-5'
   * @param statusText text like 'Deleting...', 'Saving...', 'Exporting...'
   */
  startAction(actionKey: string, statusText: string = 'Processing...'): void {
    this._activeActions.update(map => {
      const next = new Map(map);
      next.set(actionKey, statusText);
      return next;
    });
  }

  /**
   * Stop a named action
   */
  stopAction(actionKey: string): void {
    this._activeActions.update(map => {
      const next = new Map(map);
      next.delete(actionKey);
      return next;
    });
  }

  /**
   * Check if a specific action is currently in progress
   */
  isActionLoading(actionKey: string): boolean {
    return this._activeActions().has(actionKey);
  }

  /**
   * Get the current status text for a named action
   */
  getActionStatus(actionKey: string): string | undefined {
    return this._activeActions().get(actionKey);
  }

  /**
   * Cleanly and safely extract a human-readable error message from any HTTP or JavaScript error
   */
  extractErrorMessage(err: any, fallback: string = 'An unexpected error occurred. Please try again.'): string {
    if (!err) return fallback;
    if (typeof err === 'string') return err;

    // Handle Angular HttpErrorResponse
    if (err.error) {
      if (typeof err.error === 'string') return err.error;

      // FastAPI validation error format: { detail: [{ loc: [...], msg: "..." }] } or { detail: "..." }
      if (typeof err.error.detail === 'string') return err.error.detail;
      if (Array.isArray(err.error.detail)) {
        return err.error.detail
          .map((d: any) => d.msg || (typeof d === 'string' ? d : JSON.stringify(d)))
          .join(', ');
      }
      if (err.error.detail && typeof err.error.detail === 'object') {
        return err.error.detail.msg || err.error.detail.message || JSON.stringify(err.error.detail);
      }

      // Generic error response format: { message: "..." }
      if (typeof err.error.message === 'string') return err.error.message;
      if (typeof err.error.error === 'string') return err.error.error;
    }

    if (err.message && typeof err.message === 'string') return err.message;
    if (err.statusText && err.statusText !== 'OK') return `${err.statusText} (${err.status || 500})`;

    return fallback;
  }
}
