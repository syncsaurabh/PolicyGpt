import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { LayoutService } from '../../core/services/layout.service';
import { normalizeRole } from '../../models/role.model';

export interface NavItem {
  label: string;
  path: string;
  icon: string;
}

/**
 * Role-based navigation item configurations with corresponding menu icons.
 */
export const ROLE_SIDEBAR_CONFIG: Record<string, NavItem[]> = {
  ADMINISTRATOR: [
    { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    { label: 'Policies', path: '/policies', icon: 'description' },
    { label: 'Schemes', path: '/schemes', icon: 'account_balance' },
    { label: 'Approvals Panel', path: '/approvals', icon: 'fact_check' },
    { label: 'Reports', path: '/reports', icon: 'analytics' },
    { label: 'Audit Logs', path: '/admin/audit-logs', icon: 'history' },
    { label: 'Admin Users', path: '/admin/users', icon: 'manage_accounts' },
    { label: 'Notifications', path: '/notifications', icon: 'notifications' },
    { label: 'Feedback', path: '/feedback', icon: 'rate_review' },
  ],
  GOVERNMENT_OFFICIAL: [
    { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    { label: 'Policies', path: '/policies', icon: 'description' },
    { label: 'Schemes', path: '/schemes', icon: 'account_balance' },
    { label: 'Approvals', path: '/approvals', icon: 'fact_check' },
    { label: 'Reports', path: '/reports', icon: 'analytics' },
    { label: 'Notifications', path: '/notifications', icon: 'notifications' },
  ],
  CITIZEN: [
    { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    // { label: 'Search', path: '/search', icon: 'search' },
    { label: 'Policies', path: '/policies', icon: 'description' },
    { label: 'Schemes', path: '/schemes', icon: 'account_balance' },
    { label: 'Eligibility', path: '/eligibility', icon: 'task_alt' },
    { label: 'Compare', path: '/compare', icon: 'compare_arrows' },
    { label: 'Notifications', path: '/notifications', icon: 'notifications' },
    { label: 'Feedback & Support', path: '/feedback', icon: 'support_agent' },
  ],
  RESEARCHER: [
    { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    { label: 'Search', path: '/search', icon: 'search' },
    { label: 'Policies', path: '/policies', icon: 'description' },
    { label: 'Compare', path: '/compare', icon: 'compare_arrows' },
    { label: 'Notifications', path: '/notifications', icon: 'notifications' },
  ],
  ORGANIZATION: [
    { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    { label: 'Policies', path: '/policies', icon: 'description' },
    { label: 'Schemes', path: '/schemes', icon: 'account_balance' },
    { label: 'Notifications', path: '/notifications', icon: 'notifications' },
    { label: 'Feedback', path: '/feedback', icon: 'rate_review' },
  ],
};

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
  { label: 'Policies', path: '/policies', icon: 'description' },
  { label: 'Schemes', path: '/schemes', icon: 'account_balance' },
];

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  protected readonly auth = inject(Auth);
  protected readonly layoutService = inject(LayoutService);

  get filteredNavItems(): NavItem[] {
    const user = this.auth.getCurrentUser();
    if (!user || !user.role) {
      return DEFAULT_NAV_ITEMS;
    }

    const normRole = normalizeRole(user.role);
    return ROLE_SIDEBAR_CONFIG[normRole] || DEFAULT_NAV_ITEMS;
  }
}
