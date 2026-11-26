const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export type ApiErrorPayload = {
  detail?: unknown;
};

function formatErrorDetail(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === 'string') return item;
      if (item && typeof item === 'object') {
        const entry = item as { loc?: unknown[]; msg?: unknown };
        const field = Array.isArray(entry.loc) ? entry.loc.at(-1) : null;
        const message = typeof entry.msg === 'string' ? entry.msg : 'Invalid value';
        return field ? `${String(field)}: ${message}` : message;
      }
      return String(item);
    });

    return messages.filter(Boolean).join('; ') || null;
  }

  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail);
    } catch {
      return null;
    }
  }

  return null;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers, ...restInit } = init || {};
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...restInit,
    headers: {
      'Content-Type': 'application/json',
      ...(headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = 'Request failed';

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      message = formatErrorDetail(payload.detail) ?? message;
    } catch {
      message = response.statusText || message;
    }

    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export function getWebSocketUrl(path: string): string {
  const url = new URL(apiBaseUrl);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = path;
  url.search = '';
  return url.toString();
}