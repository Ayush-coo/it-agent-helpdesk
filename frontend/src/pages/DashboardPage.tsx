import { Link, useNavigate } from 'react-router-dom';
import { FormEvent, useState } from 'react';

import { useAuth } from '../contexts/AuthContext';
import { request, ApiError } from '../lib/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout, token } = useAuth();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [category, setCategory] = useState('general');
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [triageSummary, setTriageSummary] = useState<string | null>(null);
  const [recommendedAgent, setRecommendedAgent] = useState<string | null>(null);
  const [nextSteps, setNextSteps] = useState<string[]>([]);

  async function handleSuggest() {
    if (!description.trim() || !token) return;
    setIsSuggesting(true);
    setError(null);
    try {
      const resp = await request<{
        priority?: string;
        category?: string;
        short_summary?: string;
        recommended_agent?: string;
        next_steps?: string[];
      }>('/api/v1/ai/suggest-triage', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ description }),
      });

      setPriority(resp.priority ?? 'medium');
      setCategory(resp.category ?? 'general');
      setTriageSummary(resp.short_summary ?? null);
      setRecommendedAgent(resp.recommended_agent ?? null);
      setNextSteps(resp.next_steps ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to get triage suggestion');
    } finally {
      setIsSuggesting(false);
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setIsCreating(true);
    setError(null);
    try {
      const payload = { title, description, priority, category };
      const ticket = await request('/api/v1/tickets', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      // clear form and navigate to chat with ticket id
      setTitle('');
      setDescription('');
      setPriority('medium');
      setCategory('general');
      navigate('/app/chat');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to create ticket');
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <main className="dashboard-page">
      <section className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <div className="eyebrow">Protected shell</div>
            <h1>Command center</h1>
            <p>
              You are signed in as {user?.email}. This workspace brings together ticket intake, AI triage, and guided support workflows in one experience.
            </p>
          </div>
          <button type="button" className="secondary-button" onClick={handleLogout}>
            Sign out
          </button>
        </header>

        <div className="dashboard-grid">
          <article className="dashboard-card dashboard-card--accent">
            <span className="label">Active user</span>
            <strong>{user?.full_name ?? 'Unnamed agent'}</strong>
            <p>{user?.role}</p>
          </article>

          <article className="dashboard-card">
            <span className="label">Create Ticket</span>
            <form className="ticket-form" onSubmit={handleCreate}>
              <label>
                Title
                <input value={title} onChange={(e) => setTitle(e.target.value)} required />
              </label>

              <label>
                Description
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} required />
              </label>

              <label>
                Priority
                <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </label>

              <label>
                Category
                <input value={category} onChange={(e) => setCategory(e.target.value)} />
              </label>

              {error ? <div className="auth-form__error">{error}</div> : null}

              {triageSummary ? (
                <div className="auth-form__error" style={{ background: '#0f172a', color: '#f8fafc' }}>
                  <strong>AI summary:</strong> {triageSummary}
                  <br />
                  <strong>Recommended agent:</strong> {recommendedAgent ?? 'classifier_agent'}
                  {nextSteps.length > 0 ? (
                    <>
                      <br />
                      <strong>Next steps:</strong> {nextSteps.join(' • ')}
                    </>
                  ) : null}
                </div>
              ) : null}

              <div className="ticket-form__actions">
                <button type="button" onClick={handleSuggest} disabled={isSuggesting || !description.trim()}>
                  {isSuggesting ? 'Suggesting...' : 'Suggest triage'}
                </button>
                <button type="submit" disabled={isCreating}>{isCreating ? 'Creating...' : 'Create ticket'}</button>
              </div>
            </form>
          </article>

          <article className="dashboard-card">
            <span className="label">Live demo focus</span>
            <strong>AI-assisted support flow</strong>
            <p>Create a ticket, get triage guidance, and route the request intelligently through the helpdesk experience.</p>
          </article>
        </div>

        <footer className="dashboard-footer">
          <Link to="/app/chat">Open AI chatbot</Link>
          <span className="dashboard-footer__divider">|</span>
          <Link to="/app/knowledge-base">Open knowledge base</Link>
          <span className="dashboard-footer__divider">|</span>
          <Link to="/login">Back to login</Link>
        </footer>
      </section>
    </main>
  );
}
