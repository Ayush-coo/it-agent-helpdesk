export type UserRole = 'admin' | 'agent' | 'user';

export type AuthUser = {
  id: string;
  full_name: string | null;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer';
  user: AuthUser;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = {
  full_name?: string | null;
  email: string;
  password: string;
};