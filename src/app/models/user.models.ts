/**
 * UserRole enum aligned with FastAPI Backend schema.
 */
export enum UserRole {
  ADMINISTRATOR = 'ADMINISTRATOR',
  GOVERNMENT_OFFICIAL = 'GOVERNMENT_OFFICIAL',
  CITIZEN = 'CITIZEN',
  RESEARCHER = 'RESEARCHER',
  ORGANIZATION = 'ORGANIZATION',
  GUEST_USER = 'GUEST_USER'
}

/**
 * UserRead schema returned from backend for user queries and auth payloads.
 */
export interface UserRead {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * UserUpdate schema for updating user profile.
 */
export interface UserUpdate {
  name?: string | null;
}
