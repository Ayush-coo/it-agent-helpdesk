import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { ApiError, request } from '../lib/api';
import type { AuthUser } from '../types/auth';
import type { TicketPriority, TicketRead, TicketStatus } from '../types/ticket';

const pageSize = 20;

export default function TicketsPage() {
  const { token, user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'agent';
  const [tickets, setTickets] = useState<TicketRead[]>([]);
  const [assignees, setAssignees] = useState<AuthUser[]>([]);
  const [status, setStatus] = useState<TicketStatus | ''>('');
  const [priority, setPriority] = useState<TicketPriority | ''>('');
  const [assigneeId, setAssigneeId] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !isStaff) return;
    request<AuthUser[]>('/api/v1/tickets/assignees', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(setAssignees)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Unable to load assignees'));
  }, [isStaff, token]);

  useEffect(() => {
    if (!token) return;
    const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (status) params.set('status', status);
    if (priority) params.set('priority', priority);
    if (assigneeId) params.set('assignee_id', assigneeId);
    if (search.trim()) params.set('q', search.trim());

    setLoading(true);
    setError(null);
    request<TicketRead[]>(`/api/v1/tickets?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(setTickets)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Unable to load tickets'))
      .finally(() => setLoading(false));
  }, [assigneeId, offset, priority, search, status, token]);

  function resetPage<T>(setter: (value: T) => void, value: T) {
    setter(value);
    setOffset(0);
  }

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-slate-200">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{isStaff ? 'Ticket queue' : 'My tickets'}</h1>
            <p className="mt-1 text-sm text-slate-400">
              {isStaff ? 'Review and manage requests across the helpdesk.' : 'Track your support requests and updates.'}
            </p>
          </div>
          <Link to="/app" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-500">
            New ticket
          </Link>
        </div>

        <section className="mb-5 grid gap-3 rounded-xl border border-slate-800 bg-slate-900/70 p-4 md:grid-cols-4">
          <input
            aria-label="Search tickets"
            value={search}
            onChange={(event) => resetPage(setSearch, event.target.value)}
            placeholder="Search title or description"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <select
            aria-label="Filter by status"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as TicketStatus | '');
              setOffset(0);
            }}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="waiting_on_user">Waiting on user</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select
            aria-label="Filter by priority"
            value={priority}
            onChange={(event) => {
              setPriority(event.target.value as TicketPriority | '');
              setOffset(0);
            }}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            <option value="">All priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
          {isStaff && (
            <select
              aria-label="Filter by assignee"
              value={assigneeId}
              onChange={(event) => resetPage(setAssigneeId, event.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            >
              <option value="">All assignees</option>
              {assignees.map((assignee) => (
                <option key={assignee.id} value={assignee.id}>
                  {assignee.full_name || assignee.email}
                </option>
              ))}
            </select>
          )}
        </section>

        {error && <p role="alert" className="mb-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{error}</p>}
        <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
          {loading ? (
            <p className="p-8 text-center text-sm text-slate-400">Loading tickets...</p>
          ) : tickets.length ? (
            <div className="divide-y divide-slate-800">
              {tickets.map((ticket) => (
                <Link
                  key={ticket.id}
                  to={`/app/tickets/${ticket.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 p-5 hover:bg-slate-800/50"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-semibold tracking-wide text-emerald-400">{ticket.ticket_number}</p>
                    <h2 className="mt-1 truncate font-medium text-white">{ticket.title}</h2>
                    <p className="mt-1 text-xs text-slate-400">
                      {new Date(ticket.created_at).toLocaleString()}
                      {ticket.assigned_to_id
                        ? ` · ${assignees.find((assignee) => assignee.id === ticket.assigned_to_id)?.full_name || 'Assigned'}`
                        : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="rounded-full bg-slate-800 px-3 py-1 capitalize text-slate-300">{ticket.status.replace(/_/g, ' ')}</span>
                    <span className="rounded-full bg-indigo-950 px-3 py-1 uppercase text-indigo-300">{ticket.priority}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="p-8 text-center text-sm text-slate-400">No tickets match these filters.</p>
          )}
        </section>
        <div className="mt-4 flex justify-end gap-3">
          <button
            type="button"
            disabled={offset === 0 || loading}
            onClick={() => setOffset((current) => Math.max(0, current - pageSize))}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={tickets.length < pageSize || loading}
            onClick={() => setOffset((current) => current + pageSize)}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </main>
  );
}
