import { Role } from './role.model';

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  token?: string;
}
