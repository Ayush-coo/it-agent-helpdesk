import { useState, useCallback } from 'react';
import { getApiBaseUrl } from '../lib/api';
import type { ChatMessage, ChatResponse } from '../types/chat';

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useLocalOpsStream(token: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: makeId(),
      role: 'assistant',
      content: 'I’m LocalOps. Describe the operational symptom, affected service, site, or asset.',
    },
  ]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [mockOtp, setMockOtp] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    text: string,
    ticketId?: string,
    context?: string,
    useKnowledgeBase = true,
    actionConfirmation?: 'confirm' | 'cancel',
    otp?: string | null,
  ) => {
    if (!text.trim() || !token) return;

    const userMessageId = makeId();
    const assistantMessageId = makeId();
    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: 'user', content: text },
      { id: assistantMessageId, role: 'assistant', content: '' },
    ]);

    setIsStreaming(true);
    setError(null);
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          context: context?.trim() || null,
          ticket_id: ticketId?.trim() || null,
          use_knowledge_base: useKnowledgeBase,
          action_confirmation: actionConfirmation,
          otp,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat request failed (HTTP ${response.status})`);
      }

      const result = await response.json() as ChatResponse;
      setConversationId(result.conversation_id);
      setPendingAction(result.pending_action ?? null);
      setMockOtp(result.mock_otp ?? null);
      setMessages((prev) => prev.map((msg) => (
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: result.reply,
              references: result.references,
              ticket: result.ticket,
              pendingAction: result.pending_action,
              mockOtp: result.mock_otp,
            }
          : msg
      )));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to reach LocalOps');
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId));
    } finally {
      setIsStreaming(false);
    }
  }, [conversationId, token]);

  const confirmSensitiveAction = useCallback(() => {
    if (!pendingAction) return;
    void sendMessage(
      `Confirm ${pendingAction.replace(/_/g, ' ')}`,
      undefined,
      undefined,
      true,
      'confirm',
      mockOtp,
    );
  }, [mockOtp, pendingAction, sendMessage]);

  const cancelSensitiveAction = useCallback(() => {
    if (!pendingAction) return;
    void sendMessage(
      `Cancel ${pendingAction.replace(/_/g, ' ')}`,
      undefined,
      undefined,
      true,
      'cancel',
    );
  }, [pendingAction, sendMessage]);

  return {
    messages,
    sendMessage,
    confirmSensitiveAction,
    cancelSensitiveAction,
    pendingAction,
    isStreaming,
    error,
  };
}
