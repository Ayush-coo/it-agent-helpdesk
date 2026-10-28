import { useState, useCallback } from 'react';
import { getApiBaseUrl } from '../lib/api';
import type { ChatMessage } from '../types/chat';

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
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (text: string, ticketId?: string, context?: string, useKnowledgeBase = true) => {
    if (!text.trim() || !token) return;

    const userMessageId = makeId();
    const assistantMessageId = makeId();

    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: 'user', content: text },
      { id: assistantMessageId, role: 'assistant', content: '' }
    ]);
    
    setIsStreaming(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          context: context?.trim() || null,
          ticket_id: ticketId?.trim() || null,
          use_knowledge_base: useKnowledgeBase,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'delta' || data.type === 'done') {
                  setMessages((prev) => 
                    prev.map((msg) => 
                      msg.id === assistantMessageId 
                        ? { 
                            ...msg, 
                            content: data.type === 'done' ? data.reply : msg.content + data.content,
                            references: data.references || msg.references 
                          }
                        : msg
                    )
                  );
                } else if (data.type === 'error') {
                  setError(data.message);
                }
              } catch (e) {
                // Ignore parse errors for incomplete chunks
              }
            }
          }
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Unable to reach LocalOps');
    } finally {
      setIsStreaming(false);
    }
  }, [token]);

  return { messages, sendMessage, isStreaming, error };
}
