const tokenKey = 'it-agent-auth-token';

import type { ChatMessage } from '../types/chat';

export type AssistantMemory = {
  id: string;
  text: string;
  createdAt: string;
};

export type AssistantScheduleItem = {
  id: string;
  text: string;
  when: string;
  done: boolean;
};

function userKey(prefix: string, userId: string): string {
  return `it-agent-${prefix}-${userId}`;
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function loadAssistantMemory(userId: string): AssistantMemory[] {
  return readJson(userKey('memory', userId), []);
}

export function saveAssistantMemory(userId: string, memory: AssistantMemory[]): void {
  window.localStorage.setItem(userKey('memory', userId), JSON.stringify(memory));
}

export function loadAssistantSchedule(userId: string): AssistantScheduleItem[] {
  return readJson(userKey('schedule', userId), []);
}

export function saveAssistantSchedule(userId: string, schedule: AssistantScheduleItem[]): void {
  window.localStorage.setItem(userKey('schedule', userId), JSON.stringify(schedule));
}

export function loadAssistantConversation(userId: string): ChatMessage[] {
  const messages = readJson<ChatMessage[]>(userKey('conversation', userId), []);
  const staleFallback = "I'm with you. Describe what you expected to happen, what happened instead, and we'll work out the next move.";
  return messages.filter((message) => message.content !== staleFallback);
}

export function saveAssistantConversation(userId: string, messages: ChatMessage[]): void {
  window.localStorage.setItem(userKey('conversation', userId), JSON.stringify(messages.slice(-40)));
}

export function loadToken(): string | null {
  return window.localStorage.getItem(tokenKey);
}

export function saveToken(token: string): void {
  window.localStorage.setItem(tokenKey, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(tokenKey);
}