import { UserRole } from './user.models';

export enum Role {
  ADMINISTRATOR = 'Administrator',
  GOVERNMENT_OFFICIAL = 'Government Official',
  CITIZEN = 'Citizen',
  RESEARCHER = 'Researcher',
  ORGANIZATION = 'Organization',
  GUEST = 'Guest User'
}

/**
 * Normalizes role string to standard uppercase format or matches UserRole.
 */
export function normalizeRole(role: string | Role | UserRole | undefined | null): string {
  if (!role) return '';
  const cleaned = role.toString().toUpperCase().replace(/[\s-]+/g, '_');
  if (cleaned === 'GUEST') return 'GUEST_USER';
  return cleaned;
}

/**
 * Converts backend UserRole or string to display-friendly Role enum.
 */
export function toDisplayRole(userRole: string | UserRole | undefined | null): Role {
  const norm = normalizeRole(userRole);
  switch (norm) {
    case 'ADMINISTRATOR':
      return Role.ADMINISTRATOR;
    case 'GOVERNMENT_OFFICIAL':
      return Role.GOVERNMENT_OFFICIAL;
    case 'CITIZEN':
      return Role.CITIZEN;
    case 'RESEARCHER':
      return Role.RESEARCHER;
    case 'ORGANIZATION':
      return Role.ORGANIZATION;
    case 'GUEST_USER':
    case 'GUEST':
      return Role.GUEST;
    default:
      return Role.CITIZEN;
  }
}

/**
 * Converts display Role to backend UserRole.
 */
export function toBackendRole(role: Role | string | undefined | null): UserRole {
  const norm = normalizeRole(role);
  if (Object.values(UserRole).includes(norm as UserRole)) {
    return norm as UserRole;
  }
  return UserRole.CITIZEN;
}
