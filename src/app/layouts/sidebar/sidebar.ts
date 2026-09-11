import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Auth } from '../../core/services/auth';
import { Role } from '../../models/role.model';

interface NavItem {
  label: string;
  path: string;
  roles?: Role[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  protected readonly auth = inject(Auth);

  // Full list of routes mapped to authorized roles.
  // Routes without a 'roles' key are accessible to all authenticated users.
  private readonly navItems: NavItem[] = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Policies', path: '/policies', roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.RESEARCHER] },
    { label: 'Schemes', path: '/schemes', roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.CITIZEN] },
    { label: 'Eligibility Check', path: '/eligibility', roles: [Role.CITIZEN] },
    { label: 'Compare Schemes', path: '/compare', roles: [Role.CITIZEN, Role.RESEARCHER] },
    { label: 'Notifications', path: '/notifications', roles: [Role.CITIZEN] },
    { label: 'Approvals Panel', path: '/approvals', roles: [Role.GOVERNMENT_OFFICIAL] },
    { label: 'Reports', path: '/reports', roles: [Role.ADMINISTRATOR, Role.GOVERNMENT_OFFICIAL, Role.RESEARCHER] },
    { label: 'Admin Users', path: '/admin/users', roles: [Role.ADMINISTRATOR] },
    { label: 'Audit Logs', path: '/admin/audit-logs', roles: [Role.ADMINISTRATOR] },
    { label: 'Feedback', path: '/feedback' },
  ];

  /**
   * Filtered list of links the current user has permission to see.
   */
  get filteredNavItems(): NavItem[] {
    const user = this.auth.getCurrentUser();
    if (!user) {
      return [];
    }

    return this.navItems.filter(item => {
      // If the route has no specific role restriction, show it to all authenticated users
      if (!item.roles || item.roles.length === 0) {
        return true;
      }
      return this.auth.hasRole(item.roles);
    });
  }
}
