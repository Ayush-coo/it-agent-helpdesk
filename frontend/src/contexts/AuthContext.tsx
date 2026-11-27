import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { request } from '../lib/api';
import { clearToken, loadToken, saveToken } from '../lib/storage';
import type { AuthResponse, AuthUser, LoginRequest, RegisterRequest } from '../types/auth';

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isHydrating: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  demoLogin: () => void;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function fetchCurrentUser(token: string): Promise<AuthUser> {
  return request<AuthUser>('/api/v1/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);

  useEffect(() => {
    const storedToken = loadToken();
    if (!storedToken) {
      setIsHydrating(false);
      return;
    }

    setToken(storedToken);
    fetchCurrentUser(storedToken)
      .then(setUser)
      .catch(() => {
        clearToken();
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsHydrating(false));
  }, []);

  async function authenticate(endpoint: '/api/v1/auth/login' | '/api/v1/auth/register', payload: LoginRequest | RegisterRequest) {
    const response = await request<AuthResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    saveToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }

  async function login(payload: LoginRequest) {
    await authenticate('/api/v1/auth/login', payload);
  }

  function demoLogin() {
    const demoUser: AuthUser = {
      id: 'demo-agent',
      full_name: 'Agent',
      email: 'agent@localops.test',
      role: 'agent',
      is_active: true,
      created_at: new Date().toISOString(),
    };
    saveToken('localops-demo-session');
    setToken('localops-demo-session');
    setUser(demoUser);
  }

  async function register(payload: RegisterRequest) {
    await authenticate('/api/v1/auth/register', payload);
  }

  function logout() {
    clearToken();
    setToken(null);
    setUser(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      isHydrating,
      login,
      demoLogin,
      register,
      logout,
    }),
    [isHydrating, login, logout, register, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}