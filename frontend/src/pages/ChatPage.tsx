import { FormEvent, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { request, ApiError } from '../lib/api';
import type { ChatMessage, ChatResponse } from '../types/chat';

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ChatPage() {
  const { token, user } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState('');
  const [ticketId, setTicketId] = useState('');
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: makeId(),
      role: 'assistant',
      content: 'I am ready to help with IT issues. Ask me about troubleshooting, access problems, or ticket updates.',
    },
  ]);

  const modelHint = useMemo(() => 'Ollama + LangChain', []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = prompt.trim();
    if (!text || !token) {
      return;
    }

    const userMessage: ChatMessage = {
      id: makeId(),
      role: 'user',
      content: text,
    };

    setMessages((previous) => [...previous, userMessage]);
    setPrompt('');
    setIsSending(true);
    setError(null);

    try {
      const response = await request<ChatResponse>('/api/v1/chat', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          context: context.trim() || null,
          ticket_id: ticketId.trim() || null,
          use_knowledge_base: useKnowledgeBase,
        }),
      });

      setMessages((previous) => [
        ...previous,
        {
          id: makeId(),
          role: 'assistant',
          content: response.reply,
          references: response.references,
        },
      ]);
    } catch (submissionError) {
      setError(submissionError instanceof ApiError ? submissionError.message : 'Unable to reach chatbot service');
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">
        <header className="chat-header">
          <div>
            <div className="eyebrow">Milestone 6</div>
            <h1>AI helpdesk assistant</h1>
            <p>
              Signed in as {user?.email}. Messages are sent to a protected FastAPI endpoint powered by {modelHint}.
            </p>
          </div>
          <div className="chat-header__links">
            <Link to="/app/knowledge-base">Knowledge base</Link>
            <Link to="/app">Back to dashboard</Link>
          </div>
        </header>

        <section className="chat-grid">
          <aside className="chat-config">
            <h2>Request context</h2>
            <label>
              Ticket ID
              <input
                value={ticketId}
                onChange={(event) => setTicketId(event.target.value)}
                placeholder="Optional ticket id"
              />
            </label>
            <label>
              Extra context
              <textarea
                value={context}
                onChange={(event) => setContext(event.target.value)}
                rows={8}
                placeholder="Network outage details, system info, recent errors..."
              />
            </label>
            <label className="chat-config__checkbox">
              <input
                type="checkbox"
                checked={useKnowledgeBase}
                onChange={(event) => setUseKnowledgeBase(event.target.checked)}
              />
              Use RAG knowledge base
            </label>
          </aside>

          <section className="chat-panel">
            <div className="chat-messages" aria-live="polite">
              {messages.map((message) => (
                <article key={message.id} className={`chat-bubble chat-bubble--${message.role}`}>
                  <span>{message.role === 'user' ? 'You' : 'Assistant'}</span>
                  <p>{message.content}</p>
                  {message.role === 'assistant' && message.references?.length ? (
                    <ul className="chat-references">
                      {message.references.map((reference) => (
                        <li key={reference.id}>
                          <strong>{reference.title}</strong>
                          <span>score: {reference.score.toFixed(3)}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ))}
            </div>

            <form className="chat-form" onSubmit={handleSubmit}>
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                rows={3}
                placeholder="Describe your IT issue and what you have tried so far"
                required
              />
              <div className="chat-form__actions">
                {error ? <div className="auth-form__error">{error}</div> : null}
                <button type="submit" disabled={isSending}>
                  {isSending ? 'Sending...' : 'Send message'}
                </button>
              </div>
            </form>
          </section>
        </section>
      </section>
    </main>
  );
}