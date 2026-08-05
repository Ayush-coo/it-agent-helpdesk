const tokenKey = 'it-agent-auth-token';

export function loadToken(): string | null {
  return window.localStorage.getItem(tokenKey);
}

export function saveToken(token: string): void {
  window.localStorage.setItem(tokenKey, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(tokenKey);
}