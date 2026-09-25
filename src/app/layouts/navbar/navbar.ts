import { Component, ElementRef, HostListener, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { LayoutService } from '../../core/services/layout.service';
import { ThemeService } from '../../core/services/theme.service';
import { NotificationService } from '../../core/services/notification.service';
import { NotificationRead } from '../../models/notification.model';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class Navbar implements OnInit {
  protected readonly auth = inject(Auth);
  protected readonly layoutService = inject(LayoutService);
  protected readonly themeService = inject(ThemeService);
  protected readonly notificationService = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly elementRef = inject(ElementRef);

  isNotificationDropdownOpen = signal<boolean>(false);
  isLoadingDropdown = signal<boolean>(false);

  ngOnInit(): void {
    if (this.auth.isAuthenticated()) {
      this.notificationService.refreshUnreadCount();
    }
  }

  toggleNotificationDropdown(event: Event): void {
    event.stopPropagation();
    const nextState = !this.isNotificationDropdownOpen();
    this.isNotificationDropdownOpen.set(nextState);

    if (nextState) {
      this.isLoadingDropdown.set(true);
      this.notificationService.loadRecentForDropdown().subscribe({
        next: () => this.isLoadingDropdown.set(false),
        error: () => this.isLoadingDropdown.set(false)
      });
    }
  }

  closeNotificationDropdown(): void {
    this.isNotificationDropdownOpen.set(false);
  }

  markAllAsRead(event: Event): void {
    event.stopPropagation();
    this.notificationService.markAllAsRead().subscribe({
      next: () => {},
      error: (err) => console.error('Error marking notifications as read:', err)
    });
  }

  onNotificationClick(notification: NotificationRead): void {
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe();
    }
    this.closeNotificationDropdown();
    this.router.navigate(['/notifications'], { queryParams: { id: notification.id } });
  }

  formatTime(dateStr: string): string {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.closeNotificationDropdown();
    }
  }

  logout(): void {
    this.auth.logout();
  }
}
