import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from '../services/auth';
import { Role } from '../../models/role.model';

/**
 * Guard to restrict access to pages based on the user's role.
 */
export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(Auth);
  const router = inject(Router);

  // 1. Ensure user is authenticated first
  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url }
    });
  }

  // 2. Fetch expected roles from route configuration
  const allowedRoles = route.data?.['roles'] as Role[] | undefined;
  
  // If no specific roles are configured, allow access
  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }

  // 3. Check if user holds one of the required roles
  const user = authService.getCurrentUser();
  if (user && allowedRoles.includes(user.role)) {
    return true;
  }

  // 4. Authenticated but lacks the correct role, redirect to unauthorized
  return router.createUrlTree(['/unauthorized']);
};
