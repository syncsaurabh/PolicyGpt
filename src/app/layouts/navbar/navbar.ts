import { Component, ElementRef, HostListener, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { AuthService } from '../../core/services/auth.service';
import { UserService } from '../../core/services/user.service';
import { LayoutService } from '../../core/services/layout.service';
import { ThemeService } from '../../core/services/theme.service';
import { NotificationService } from '../../core/services/notification.service';
import { NotificationRead } from '../../models/notification.model';
import { UserUpdate } from '../../models/user.models';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class Navbar implements OnInit {
  protected readonly auth = inject(Auth);
  private readonly authService = inject(AuthService);
  private readonly userService = inject(UserService);
  protected readonly layoutService = inject(LayoutService);
  protected readonly themeService = inject(ThemeService);
  protected readonly notificationService = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly elementRef = inject(ElementRef);

  // Notification dropdown state
  isNotificationDropdownOpen = signal<boolean>(false);
  isLoadingDropdown = signal<boolean>(false);

  // Profile menu & update modal state
  isProfileDropdownOpen = signal<boolean>(false);
  isProfileModalOpen = signal<boolean>(false);
  isLoadingProfile = signal<boolean>(false);
  isSavingProfile = signal<boolean>(false);
  profileFeedback = signal<{ type: 'success' | 'error'; message: string } | null>(null);

  // Editable Profile Form Model (strictly editable fields only)
  profileForm = {
    name: '',
    phone_number: '',
    age: null as number | null,
    state: '',
    address: '',
    pincode: ''
  };

  ngOnInit(): void {
    if (this.auth.isAuthenticated()) {
      this.notificationService.refreshUnreadCount();
    }
  }

  toggleNotificationDropdown(event: Event): void {
    event.stopPropagation();
    this.closeProfileDropdown();
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

  toggleProfileDropdown(event: Event): void {
    event.stopPropagation();
    this.closeNotificationDropdown();
    this.isProfileDropdownOpen.set(!this.isProfileDropdownOpen());
  }

  closeProfileDropdown(): void {
    this.isProfileDropdownOpen.set(false);
  }

  openProfileModal(): void {
    this.closeProfileDropdown();
    this.profileFeedback.set(null);

    // Populate with existing auth state immediately
    const currentUser = this.auth.getCurrentUser();
    if (currentUser) {
      this.profileForm = {
        name: currentUser.name || '',
        phone_number: currentUser.phone_number || '',
        age: currentUser.age !== undefined && currentUser.age !== null ? currentUser.age : null,
        state: currentUser.state || '',
        address: currentUser.address || '',
        pincode: currentUser.pincode || ''
      };
    }

    this.isProfileModalOpen.set(true);
    this.isLoadingProfile.set(true);

    // Fetch latest profile from backend GET /api/v1/users/me
    this.userService.getMe().subscribe({
      next: (userRead) => {
        this.isLoadingProfile.set(false);
        this.profileForm = {
          name: userRead.name || '',
          phone_number: userRead.phone_number || '',
          age: userRead.age !== undefined && userRead.age !== null ? userRead.age : null,
          state: userRead.state || '',
          address: userRead.address || '',
          pincode: userRead.pincode || ''
        };
      },
      error: () => {
        this.isLoadingProfile.set(false);
      }
    });
  }

  closeProfileModal(): void {
    this.isProfileModalOpen.set(false);
    this.profileFeedback.set(null);
  }

  saveProfile(): void {
    // Client-side validation according to backend rules
    const name = this.profileForm.name?.trim() || '';
    const phone = this.profileForm.phone_number?.trim() || '';
    const state = this.profileForm.state?.trim() || '';
    const address = this.profileForm.address?.trim() || '';
    const pincode = this.profileForm.pincode?.trim() || '';
    const age = this.profileForm.age;

    if (name && (name.length < 2 || name.length > 100)) {
      this.profileFeedback.set({ type: 'error', message: 'Name must be between 2 and 100 characters.' });
      return;
    }
    if (phone && phone.length > 50) {
      this.profileFeedback.set({ type: 'error', message: 'Phone number must not exceed 50 characters.' });
      return;
    }
    if (age !== null && age !== undefined && (isNaN(Number(age)) || Number(age) < 1 || Number(age) > 120)) {
      this.profileFeedback.set({ type: 'error', message: 'Age must be a valid number between 1 and 120.' });
      return;
    }
    if (state && state.length > 100) {
      this.profileFeedback.set({ type: 'error', message: 'State must not exceed 100 characters.' });
      return;
    }
    if (address && address.length > 500) {
      this.profileFeedback.set({ type: 'error', message: 'Address must not exceed 500 characters.' });
      return;
    }
    if (pincode && pincode.length > 20) {
      this.profileFeedback.set({ type: 'error', message: 'Pincode must not exceed 20 characters.' });
      return;
    }

    const payload: UserUpdate = {
      name: name || null,
      phone_number: phone || null,
      age: age !== null && age !== undefined && `${age}`.trim() !== '' ? Number(age) : null,
      state: state || null,
      address: address || null,
      pincode: pincode || null
    };

    this.isSavingProfile.set(true);
    this.profileFeedback.set(null);

    this.userService.updateMe(payload).subscribe({
      next: () => {
        this.isSavingProfile.set(false);
        this.profileFeedback.set({ type: 'success', message: 'Profile updated successfully.' });

        // Refresh central auth user state so whole UI updates immediately
        this.authService.fetchProfile().subscribe();

        // Close modal after feedback
        setTimeout(() => {
          if (this.isProfileModalOpen()) {
            this.closeProfileModal();
          }
        }, 1200);
      },
      error: (err) => {
        this.isSavingProfile.set(false);
        let errorMsg = 'Unable to update profile. Please try again.';
        if (err.status === 422) {
          errorMsg = 'Please check the entered information.';
          if (err.error?.detail && typeof err.error.detail === 'string') {
            errorMsg = err.error.detail;
          }
        } else if (err.status === 401) {
          errorMsg = 'Your session has expired. Please log in again.';
        } else if (err.status === 403) {
          errorMsg = 'You are not allowed to update this profile.';
        } else if (err.error?.detail && typeof err.error.detail === 'string') {
          errorMsg = err.error.detail;
        }
        this.profileFeedback.set({ type: 'error', message: errorMsg });
      }
    });
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
      this.closeProfileDropdown();
    }
  }

  logout(): void {
    this.closeProfileDropdown();
    this.auth.logout();
  }
}

