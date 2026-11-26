import { FormEvent, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { ApiError, request } from '../lib/api';
import type { AuthUser } from '../types/auth';
import type { TicketComment, TicketEvent, TicketRead, TicketStatus } from '../types/ticket';

const nextStatuses: Record<TicketStatus, TicketStatus[]> = {
  open: ['in_progress', 'waiting_on_user'],
  in_progress: ['waiting_on_user', 'resolved'],
  waiting_on_user: ['in_progress', 'resolved'],
  resolved: ['in_progress', 'closed'],
  closed: [],
};

function messageFromError(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const { token, user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'agent';
  const [ticket, setTicket] = useState<TicketRead | null>(null);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [events, setEvents] = useState<TicketEvent[]>([]);
  const [assignees, setAssignees] = useState<AuthUser[]>([]);
  const [body, setBody] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !ticketId) return;
    const requests = [
      request<TicketRead>(`/api/v1/tickets/${ticketId}`, { headers: { Authorization: `Bearer ${token}` } }),
      request<TicketComment[]>(`/api/v1/tickets/${ticketId}/comments`, { headers: { Authorization: `Bearer ${token}` } }),
      request<TicketEvent[]>(`/api/v1/tickets/${ticketId}/events`, { headers: { Authorization: `Bearer ${token}` } }),
    ] as const;
    Promise.all(requests)
      .then(([loadedTicket, loadedComments, loadedEvents]) => {
        setTicket(loadedTicket);
        setComments(loadedComments);
        setEvents(loadedEvents);
      })
      .catch((err: unknown) => setError(messageFromError(err, 'Unable to load ticket')))
      .finally(() => setBusy(false));
    if (isStaff) {
      request<AuthUser[]>('/api/v1/tickets/assignees', {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(setAssignees)
        .catch((err: unknown) => setError(messageFromError(err, 'Unable to load assignees')));
    }
  }, [isStaff, ticketId, token]);

  async function updateTicket(patch: { status?: TicketStatus; assigned_to_id?: string | null }) {
    if (!token || !ticketId) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await request<TicketRead>(`/api/v1/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify(patch),
      });
      setTicket(updated);
      const refreshedEvents = await request<TicketEvent[]>(`/api/v1/tickets/${ticketId}/events`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEvents(refreshedEvents);
    } catch (err) {
      setError(messageFromError(err, 'Unable to update ticket'));
    } finally {
      setBusy(false);
    }
  }

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !ticketId || !body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const comment = await request<TicketComment>(`/api/v1/tickets/${ticketId}/comments`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ body: body.trim(), is_internal: isInternal }),
      });
      setComments((current) => [...current, comment]);
      setBody('');
      const refreshedEvents = await request<TicketEvent[]>(`/api/v1/tickets/${ticketId}/events`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEvents(refreshedEvents);
    } catch (err) {
      setError(messageFromError(err, 'Unable to add comment'));
    } finally {
      setBusy(false);
    }
  }

  if (!ticket) {
    return (
      <main className="min-h-screen bg-background p-8 text-slate-300">
        <p>{error || 'Loading ticket...'}</p>
        <Link to="/app/tickets" className="mt-4 inline-block text-emerald-400">Back to tickets</Link>
      </main>
    );
  }

  const requesterCannotComment = !isStaff && ticket.status === 'closed';

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-slate-200">
      <div className="mx-auto max-w-5xl">
        <Link to="/app/tickets" className="text-sm text-emerald-400 hover:text-emerald-300">← Tickets</Link>
        {error && <p role="alert" className="mt-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{error}</p>}
        <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(260px,.8fr)]">
          <section className="space-y-5">
            <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-xs font-semibold tracking-wide text-emerald-400">{ticket.ticket_number}</p>
              <h1 className="mt-2 text-2xl font-bold text-white">{ticket.title}</h1>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-300">{ticket.description}</p>
              <div className="mt-5 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-slate-800 px-3 py-1 capitalize">{ticket.status.replace(/_/g, ' ')}</span>
                <span className="rounded-full bg-indigo-950 px-3 py-1 uppercase text-indigo-300">{ticket.priority}</span>
                <span className="rounded-full bg-slate-800 px-3 py-1">{new Date(ticket.created_at).toLocaleString()}</span>
              </div>
              {isStaff && (
                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <label className="text-xs text-slate-400">
                    Status
                    <select
                      value=""
                      disabled={busy || nextStatuses[ticket.status].length === 0}
                      onChange={(event) => updateTicket({ status: event.target.value as TicketStatus })}
                      className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                    >
                      <option value="">Change status</option>
                      {nextStatuses[ticket.status].map((status) => (
                        <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>
                      ))}
                    </select>
                  </label>
                  <label className="text-xs text-slate-400">
                    Assignee
                    <select
                      value={ticket.assigned_to_id || ''}
                      disabled={busy}
                      onChange={(event) => updateTicket({ assigned_to_id: event.target.value || null })}
                      className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                    >
                      <option value="">Unassigned</option>
                      {assignees.map((assignee) => (
                        <option key={assignee.id} value={assignee.id}>
                          {assignee.full_name || assignee.email}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              )}
            </article>

            <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="text-lg font-semibold text-white">Comments</h2>
              <div className="mt-4 space-y-3">
                {comments.length ? comments.map((comment) => (
                  <article key={comment.id} className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
                    <div className="mb-2 flex items-center justify-between gap-3 text-xs text-slate-400">
                      <span>{comment.is_internal ? 'Internal note' : 'Public comment'}</span>
                      <time>{new Date(comment.created_at).toLocaleString()}</time>
                    </div>
                    <p className="whitespace-pre-wrap text-sm text-slate-200">{comment.body}</p>
                  </article>
                )) : <p className="text-sm text-slate-500">No comments yet.</p>}
              </div>
              {!requesterCannotComment && (
                <form onSubmit={addComment} className="mt-5 space-y-3">
                  <textarea
                    value={body}
                    onChange={(event) => setBody(event.target.value)}
                    required
                    rows={3}
                    placeholder="Write a comment..."
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                  />
                  {isStaff && (
                    <label className="flex items-center gap-2 text-xs text-slate-400">
                      <input type="checkbox" checked={isInternal} onChange={(event) => setIsInternal(event.target.checked)} />
                      Internal note (visible to agents and admins only)
                    </label>
                  )}
                  <button disabled={busy} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white disabled:opacity-50">
                    Add comment
                  </button>
                </form>
              )}
              {requesterCannotComment && <p className="mt-4 text-sm text-slate-500">This ticket is closed.</p>}
            </section>
          </section>

          <aside className="h-fit rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <h2 className="text-lg font-semibold text-white">Activity</h2>
            <ol className="mt-5 space-y-4">
              {events.map((item) => (
                <li key={item.id} className="border-l border-slate-700 pl-4">
                  <p className="text-sm capitalize text-slate-200">{item.type.replace(/_/g, ' ')}</p>
                  {item.old_value !== null || item.new_value !== null ? (
                    <p className="mt-1 break-words text-xs text-slate-400">
                      {item.old_value ? `${item.old_value} → ` : ''}{item.new_value || ''}
                    </p>
                  ) : null}
                  <time className="mt-1 block text-[11px] text-slate-500">{new Date(item.created_at).toLocaleString()}</time>
                </li>
              ))}
              {!events.length && <li className="text-sm text-slate-500">No activity recorded.</li>}
            </ol>
          </aside>
        </div>
      </div>
    </main>
  );
}
