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
  is_verified?: boolean;
  created_at: string;
  updated_at: string;
  phone_number?: string | null;
  age?: number | null;
  state?: string | null;
  address?: string | null;
  pincode?: string | null;
}

/**
 * UserUpdate schema for updating user profile via PUT /api/v1/users/me.
 */
export interface UserUpdate {
  name?: string | null;
  phone_number?: string | null;
  age?: number | null;
  state?: string | null;
  address?: string | null;
  pincode?: string | null;
}

