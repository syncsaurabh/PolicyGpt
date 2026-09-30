import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class LayoutService {
  /** Reactive signal tracking mobile/tablet sidebar drawer open state */
  readonly isSidebarOpen = signal<boolean>(false);

  /** Reactive signal tracking desktop collapsed (icon-only) sidebar state */
  readonly isSidebarCollapsed = signal<boolean>(false);

  /** Toggles sidebar between expanded and collapsed icon-only mode on desktop (>= 1024px), and drawer on mobile/tablet (< 1024px) */
  toggleSidebar(): void {
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      this.isSidebarOpen.update(open => !open);
    } else {
      this.isSidebarCollapsed.update(collapsed => !collapsed);
    }
  }

  closeSidebar(): void {
    this.isSidebarOpen.set(false);
  }

  openSidebar(): void {
    this.isSidebarOpen.set(true);
  }

  collapseSidebar(): void {
    this.isSidebarCollapsed.set(true);
  }

  expandSidebar(): void {
    this.isSidebarCollapsed.set(false);
  }
}
