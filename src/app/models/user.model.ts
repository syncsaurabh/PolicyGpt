import { Role } from './role.model';
import { UserRole } from './user.models';

export interface User {
  id: string | number;
  username: string;
  name?: string;
  email: string;
  role: Role | UserRole;
  token?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}
