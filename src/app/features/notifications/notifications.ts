import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { NotificationService } from '../../core/services/notification.service';
import {
  NotificationBroadcast,
  NotificationChannel,
  NotificationCreate,
  NotificationListParams,
  NotificationPreferenceRead,
  NotificationPreferenceUpdate,
  NotificationRead,
  NotificationType,
} from '../../models/notification.model';
import { Role } from '../../models/role.model';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.css',
})
export class Notifications implements OnInit {
  protected readonly auth = inject(Auth);
  protected readonly notificationService = inject(NotificationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  // Active View Tab: 'notifications' | 'preferences' | 'admin'
  activeTab = signal<'notifications' | 'preferences' | 'admin'>('notifications');

  // Role Checks
  get isAdmin(): boolean {
    return this.auth.hasRole([Role.ADMINISTRATOR]);
  }

  get isOfficialOrAdmin(): boolean {
    return this.auth.hasRole([Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL]);
  }

  // --- Notifications Feed State ---
  notifications = signal<NotificationRead[]>([]);
  totalCount = signal<number>(0);
  page = signal<number>(1);
  pageSize = signal<number>(10);
  totalPages = signal<number>(1);
  isLoading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  // Filters
  filterUnreadOnly = signal<boolean>(false);
  selectedCategory = signal<string>('ALL'); // 'ALL' | 'POLICIES' | 'SCHEMES' | 'APPLICATIONS' | 'SYSTEM'
  selectedChannel = signal<string>('ALL'); // 'ALL' | 'IN_APP' | 'EMAIL' | 'SMS' | 'PUSH'

  // --- Preferences State ---
  preferences = signal<NotificationPreferenceRead | null>(null);
  isLoadingPrefs = signal<boolean>(false);
  isSavingPrefs = signal<boolean>(false);

  prefEmail = signal<boolean>(true);
  prefSms = signal<boolean>(true);
  prefInApp = signal<boolean>(true);
  prefPolicyAlerts = signal<boolean>(true);
  prefSchemeUpdates = signal<boolean>(true);
  prefDeadlineReminders = signal<boolean>(true);
  prefApplicationUpdates = signal<boolean>(true);
  prefSystemAlerts = signal<boolean>(true);

  // --- Admin Logs & Actions State ---
  adminNotifications = signal<NotificationRead[]>([]);
  adminTotalCount = signal<number>(0);
  adminPage = signal<number>(1);
  adminPageSize = signal<number>(15);
  adminTotalPages = signal<number>(1);
  isLoadingAdmin = signal<boolean>(false);
  isTriggeringDeadline = signal<boolean>(false);

  adminUserIdFilter = signal<number | null>(null);
  adminStatusFilter = signal<string>('ALL');
  adminTypeFilter = signal<string>('ALL');
  adminChannelFilter = signal<string>('ALL');

  // --- Modals State ---
  selectedNotification = signal<NotificationRead | null>(null);

  // Broadcast Modal Form
  isBroadcastModalOpen = signal<boolean>(false);
  isSendingBroadcast = signal<boolean>(false);
  broadcastTitle = signal<string>('');
  broadcastMessage = signal<string>('');
  broadcastType = signal<string>('SYSTEM_ALERT');
  broadcastChannel = signal<string>('IN_APP');
  broadcastTargetRoles = signal<string[]>([]);

  // Targeted Notification Modal Form
  isTargetedModalOpen = signal<boolean>(false);
  isSendingTargeted = signal<boolean>(false);
  targetedUserId = signal<number | null>(null);
  targetedTitle = signal<string>('');
  targetedMessage = signal<string>('');
  targetedType = signal<string>('GENERAL');
  targetedChannel = signal<string>('IN_APP');
  targetedEntityType = signal<string>('');
  targetedEntityId = signal<string>('');

  // Toast State
  toast = signal<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  readonly availableTypes = [
    { value: 'ALL', label: 'All Types' },
    { value: 'NEW_POLICY', label: 'New Policy' },
    { value: 'POLICY_UPDATED', label: 'Policy Updated' },
    { value: 'POLICY_APPROVED', label: 'Policy Approved' },
    { value: 'POLICY_REJECTED', label: 'Policy Rejected' },
    { value: 'NEW_SCHEME', label: 'New Scheme' },
    { value: 'SCHEME_UPDATED', label: 'Scheme Updated' },
    { value: 'SCHEME_DEADLINE', label: 'Scheme Deadline' },
    { value: 'DEADLINE_REMINDER', label: 'Deadline Reminder' },
    { value: 'APPLICATION_SUBMITTED', label: 'Application Submitted' },
    { value: 'APPLICATION_STATUS_CHANGED', label: 'Application Status Changed' },
    { value: 'APPLICATION_APPROVED', label: 'Application Approved' },
    { value: 'APPLICATION_REJECTED', label: 'Application Rejected' },
    { value: 'ELIGIBILITY_MATCH', label: 'Eligibility Match' },
    { value: 'SYSTEM_ANNOUNCEMENT', label: 'System Announcement' },
    { value: 'SYSTEM_ALERT', label: 'System Alert' },
    { value: 'FEEDBACK_RESPONSE', label: 'Feedback Response' },
    { value: 'GENERAL', label: 'General' },
  ];

  readonly availableChannels = [
    { value: 'ALL', label: 'All Channels' },
    { value: 'IN_APP', label: 'In-App' },
    { value: 'EMAIL', label: 'Email' },
    { value: 'SMS', label: 'SMS' },
    { value: 'PUSH', label: 'Push' },
  ];

  readonly systemRoles = [
    { id: 'CITIZEN', label: 'Citizen' },
    { id: 'GOVERNMENT_OFFICIAL', label: 'Government Official' },
    { id: 'RESEARCHER', label: 'Researcher' },
    { id: 'ORGANIZATION', label: 'Organization' },
  ];

  ngOnInit(): void {
    // Check query params for tab or specific notification id
    this.route.queryParams.subscribe((params) => {
      if (params['tab'] === 'preferences') {
        this.setActiveTab('preferences');
      } else if (params['tab'] === 'admin' && this.isAdmin) {
        this.setActiveTab('admin');
      } else {
        this.loadNotifications();
      }

      if (params['id']) {
        const notifId = Number(params['id']);
        if (!isNaN(notifId)) {
          this.fetchAndOpenDetails(notifId);
        }
      }
    });

    this.notificationService.refreshUnreadCount();
  }

  showToast(text: string, type: 'success' | 'error' | 'info' = 'success'): void {
    this.toast.set({ type, text });
    setTimeout(() => {
      this.toast.set(null);
    }, 4500);
  }

  setActiveTab(tab: 'notifications' | 'preferences' | 'admin'): void {
    this.activeTab.set(tab);
    if (tab === 'notifications') {
      this.loadNotifications();
    } else if (tab === 'preferences') {
      this.loadPreferences();
    } else if (tab === 'admin' && this.isAdmin) {
      this.loadAdminNotifications();
    }
  }

  // ==========================================
  // 1. MY NOTIFICATIONS ACTIONS
  // ==========================================

  loadNotifications(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    const params: NotificationListParams = {
      page: this.page(),
      page_size: this.pageSize(),
      unread_only: this.filterUnreadOnly(),
    };

    if (this.selectedChannel() !== 'ALL') {
      params.channel = this.selectedChannel();
    }

    this.notificationService.getNotifications(params).subscribe({
      next: (res) => {
        let results = res.results || [];

        // Apply client-side category filter grouping if selected
        if (this.selectedCategory() !== 'ALL') {
          results = results.filter((item) => this.matchesCategory(item.notification_type, this.selectedCategory()));
        }

        this.notifications.set(results);
        this.totalCount.set(res.total_count);
        this.totalPages.set(res.total_pages || Math.ceil(res.total_count / this.pageSize()) || 1);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to load notifications.');
      },
    });
  }

  matchesCategory(type: string, category: string): boolean {
    const t = (type || '').toUpperCase();
    switch (category) {
      case 'POLICIES':
        return t.includes('POLICY');
      case 'SCHEMES':
        return t.includes('SCHEME');
      case 'APPLICATIONS':
        return t.includes('APPLICATION') || t.includes('DEADLINE') || t.includes('ELIGIBILITY');
      case 'SYSTEM':
        return t.includes('SYSTEM') || t.includes('GENERAL') || t.includes('FEEDBACK') || t.includes('ALERT');
      default:
        return true;
    }
  }

  setCategoryFilter(category: string): void {
    this.selectedCategory.set(category);
    this.page.set(1);
    this.loadNotifications();
  }

  toggleUnreadOnly(): void {
    this.filterUnreadOnly.set(!this.filterUnreadOnly());
    this.page.set(1);
    this.loadNotifications();
  }

  onChannelFilterChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.selectedChannel.set(select.value);
    this.page.set(1);
    this.loadNotifications();
  }

  goToPage(newPage: number): void {
    if (newPage >= 1 && newPage <= this.totalPages() && newPage !== this.page()) {
      this.page.set(newPage);
      this.loadNotifications();
    }
  }

  markAsRead(item: NotificationRead, event?: Event): void {
    if (event) event.stopPropagation();
    if (item.is_read) return;

    this.notificationService.markAsRead(item.id).subscribe({
      next: (updated) => {
        this.notifications.update((list) =>
          list.map((n) => (n.id === item.id ? { ...n, is_read: true, read_at: updated.read_at } : n))
        );
        this.showToast('Notification marked as read.', 'info');
      },
      error: (err) => {
        this.showToast(err?.error?.detail || 'Failed to update notification status.', 'error');
      },
    });
  }

  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe({
      next: (res) => {
        this.notifications.update((list) => list.map((n) => ({ ...n, is_read: true })));
        this.showToast(res.message || 'All notifications marked as read.');
      },
      error: (err) => {
        this.showToast(err?.error?.detail || 'Failed to mark all as read.', 'error');
      },
    });
  }

  deleteNotification(item: NotificationRead, event?: Event): void {
    if (event) event.stopPropagation();
    if (!confirm(`Are you sure you want to delete notification "${item.title}"?`)) return;

    this.notificationService.deleteNotification(item.id).subscribe({
      next: () => {
        this.notifications.update((list) => list.filter((n) => n.id !== item.id));
        this.totalCount.update((c) => Math.max(0, c - 1));
        this.showToast('Notification deleted successfully.');
        if (this.selectedNotification()?.id === item.id) {
          this.closeDetailsModal();
        }
      },
      error: (err) => {
        this.showToast(err?.error?.detail || 'Failed to delete notification.', 'error');
      },
    });
  }

  // ==========================================
  // 2. DETAILS MODAL
  // ==========================================

  fetchAndOpenDetails(id: number): void {
    this.notificationService.getNotification(id).subscribe({
      next: (data) => {
        this.openDetailsModal(data);
      },
      error: () => {
        // Fallback: search in current list
        const found = this.notifications().find((n) => n.id === id);
        if (found) this.openDetailsModal(found);
      },
    });
  }

  openDetailsModal(item: NotificationRead): void {
    this.selectedNotification.set(item);
    if (!item.is_read) {
      this.notificationService.markAsRead(item.id).subscribe({
        next: (updated) => {
          this.notifications.update((list) =>
            list.map((n) => (n.id === item.id ? { ...n, is_read: true, read_at: updated.read_at } : n))
          );
          if (this.selectedNotification()?.id === item.id) {
            this.selectedNotification.set({ ...item, is_read: true, read_at: updated.read_at });
          }
        },
      });
    }
  }

  closeDetailsModal(): void {
    this.selectedNotification.set(null);
  }

  navigateToEntity(item: NotificationRead): void {
    this.closeDetailsModal();
    if (!item.entity_type || !item.entity_id) return;

    const entityType = item.entity_type.toUpperCase();
    if (entityType.includes('POLICY')) {
      this.router.navigate(['/policies', item.entity_id]);
    } else if (entityType.includes('SCHEME')) {
      this.router.navigate(['/schemes', item.entity_id]);
    }
  }

  // ==========================================
  // 3. PREFERENCES ACTIONS
  // ==========================================

  loadPreferences(): void {
    this.isLoadingPrefs.set(true);
    this.notificationService.getPreferences().subscribe({
      next: (pref) => {
        this.preferences.set(pref);
        this.prefEmail.set(pref.email_enabled);
        this.prefSms.set(pref.sms_enabled);
        this.prefInApp.set(pref.in_app_enabled);
        this.prefPolicyAlerts.set(pref.policy_alerts);
        this.prefSchemeUpdates.set(pref.scheme_updates);
        this.prefDeadlineReminders.set(pref.deadline_reminders);
        this.prefApplicationUpdates.set(pref.application_updates);
        this.prefSystemAlerts.set(pref.system_alerts);
        this.isLoadingPrefs.set(false);
      },
      error: (err) => {
        this.isLoadingPrefs.set(false);
        this.showToast(err?.error?.detail || 'Failed to load preferences.', 'error');
      },
    });
  }

  savePreferences(): void {
    this.isSavingPrefs.set(true);
    const updatePayload: NotificationPreferenceUpdate = {
      email_enabled: this.prefEmail(),
      sms_enabled: this.prefSms(),
      in_app_enabled: this.prefInApp(),
      policy_alerts: this.prefPolicyAlerts(),
      scheme_updates: this.prefSchemeUpdates(),
      deadline_reminders: this.prefDeadlineReminders(),
      application_updates: this.prefApplicationUpdates(),
      system_alerts: this.prefSystemAlerts(),
    };

    this.notificationService.updatePreferences(updatePayload).subscribe({
      next: (res) => {
        this.preferences.set(res);
        this.isSavingPrefs.set(false);
        this.showToast('Notification preferences updated successfully!');
      },
      error: (err) => {
        this.isSavingPrefs.set(false);
        this.showToast(err?.error?.detail || 'Failed to save preferences.', 'error');
      },
    });
  }

  // ==========================================
  // 4. ADMIN ACTIONS & LOGS
  // ==========================================

  loadAdminNotifications(): void {
    if (!this.isAdmin) return;
    this.isLoadingAdmin.set(true);

    const params: any = {
      page: this.adminPage(),
      page_size: this.adminPageSize(),
    };

    if (this.adminUserIdFilter() !== null && this.adminUserIdFilter()! > 0) {
      params.user_id = this.adminUserIdFilter();
    }
    if (this.adminStatusFilter() !== 'ALL') {
      params.status_filter = this.adminStatusFilter();
    }
    if (this.adminTypeFilter() !== 'ALL') {
      params.notification_type = this.adminTypeFilter();
    }
    if (this.adminChannelFilter() !== 'ALL') {
      params.channel = this.adminChannelFilter();
    }

    this.notificationService.getAdminNotifications(params).subscribe({
      next: (res) => {
        this.adminNotifications.set(res.results || []);
        this.adminTotalCount.set(res.total_count);
        this.adminTotalPages.set(res.total_pages || Math.ceil(res.total_count / this.adminPageSize()) || 1);
        this.isLoadingAdmin.set(false);
      },
      error: (err) => {
        this.isLoadingAdmin.set(false);
        this.showToast(err?.error?.detail || 'Failed to load system notification logs.', 'error');
      },
    });
  }

  triggerDeadlineScan(): void {
    if (!this.isAdmin) return;
    this.isTriggeringDeadline.set(true);

    this.notificationService.triggerDeadlineCheck().subscribe({
      next: (res) => {
        this.isTriggeringDeadline.set(false);
        this.showToast(res.message || 'Deadline scan completed successfully!');
        this.loadAdminNotifications();
      },
      error: (err) => {
        this.isTriggeringDeadline.set(false);
        this.showToast(err?.error?.detail || 'Failed to execute deadline check scan.', 'error');
      },
    });
  }

  openBroadcastModal(): void {
    this.broadcastTitle.set('');
    this.broadcastMessage.set('');
    this.broadcastType.set('SYSTEM_ALERT');
    this.broadcastChannel.set('IN_APP');
    this.broadcastTargetRoles.set([]);
    this.isBroadcastModalOpen.set(true);
  }

  closeBroadcastModal(): void {
    this.isBroadcastModalOpen.set(false);
  }

  toggleTargetRole(roleId: string): void {
    const current = this.broadcastTargetRoles();
    if (current.includes(roleId)) {
      this.broadcastTargetRoles.set(current.filter((r) => r !== roleId));
    } else {
      this.broadcastTargetRoles.set([...current, roleId]);
    }
  }

  sendBroadcast(): void {
    if (!this.broadcastTitle().trim() || !this.broadcastMessage().trim()) {
      this.showToast('Please enter both a title and message.', 'error');
      return;
    }

    this.isSendingBroadcast.set(true);
    const payload: NotificationBroadcast = {
      title: this.broadcastTitle().trim(),
      message: this.broadcastMessage().trim(),
      notification_type: this.broadcastType() as NotificationType,
      channel: this.broadcastChannel() as NotificationChannel,
      target_roles: this.broadcastTargetRoles().length > 0 ? this.broadcastTargetRoles() : null,
    };

    this.notificationService.broadcastNotification(payload).subscribe({
      next: (res) => {
        this.isSendingBroadcast.set(false);
        this.closeBroadcastModal();
        this.showToast(res.message || 'Broadcast announcement dispatched!');
        this.loadAdminNotifications();
      },
      error: (err) => {
        this.isSendingBroadcast.set(false);
        this.showToast(err?.error?.detail || 'Failed to send broadcast.', 'error');
      },
    });
  }

  openTargetedModal(): void {
    this.targetedUserId.set(null);
    this.targetedTitle.set('');
    this.targetedMessage.set('');
    this.targetedType.set('GENERAL');
    this.targetedChannel.set('IN_APP');
    this.targetedEntityType.set('');
    this.targetedEntityId.set('');
    this.isTargetedModalOpen.set(true);
  }

  closeTargetedModal(): void {
    this.isTargetedModalOpen.set(false);
  }

  sendTargeted(): void {
    if (!this.targetedUserId() || this.targetedUserId()! <= 0) {
      this.showToast('Please enter a valid User ID.', 'error');
      return;
    }
    if (!this.targetedTitle().trim() || !this.targetedMessage().trim()) {
      this.showToast('Please enter both title and message.', 'error');
      return;
    }

    this.isSendingTargeted.set(true);
    const payload: NotificationCreate = {
      user_id: this.targetedUserId()!,
      title: this.targetedTitle().trim(),
      message: this.targetedMessage().trim(),
      notification_type: this.targetedType() as NotificationType,
      channel: this.targetedChannel() as NotificationChannel,
      entity_type: this.targetedEntityType().trim() || null,
      entity_id: this.targetedEntityId().trim() || null,
    };

    this.notificationService.createTargetedNotification(payload).subscribe({
      next: () => {
        this.isSendingTargeted.set(false);
        this.closeTargetedModal();
        this.showToast('Targeted notification dispatched successfully!');
        this.loadAdminNotifications();
      },
      error: (err) => {
        this.isSendingTargeted.set(false);
        this.showToast(err?.error?.detail || 'Failed to dispatch targeted notification.', 'error');
      },
    });
  }

  // --- Helpers for Styling & Badges ---
  getTypeBadgeClass(type: string): string {
    const t = (type || '').toUpperCase();
    if (t.includes('APPROV') || t.includes('MATCH')) return 'badge-success';
    if (t.includes('REJECT') || t.includes('FAIL') || t.includes('ALERT')) return 'badge-danger';
    if (t.includes('DEADLINE') || t.includes('REMINDER') || t.includes('PENDING')) return 'badge-warning';
    if (t.includes('POLICY') || t.includes('SCHEME') || t.includes('SUBMIT')) return 'badge-primary';
    return 'badge-info';
  }

  getChannelBadgeClass(channel: string): string {
    const c = (channel || '').toUpperCase();
    if (c === 'EMAIL') return 'badge-channel-email';
    if (c === 'SMS') return 'badge-channel-sms';
    if (c === 'PUSH') return 'badge-channel-push';
    return 'badge-channel-inapp';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }
}
