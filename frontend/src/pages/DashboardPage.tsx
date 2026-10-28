import { useState, FormEvent, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, Ticket, BookOpen, MessageSquare, Plus, Activity, CheckCircle2, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { request, ApiError } from '../lib/api';
import type { TicketOverview, TicketRead, TicketStatus } from '../types/ticket';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout, token } = useAuth();
  
  const [tickets, setTickets] = useState<TicketRead[]>([]);
  const [stats, setStats] = useState<TicketOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOverview() {
      if (!token) return;
      try {
        const overview = await request<TicketOverview>('/api/v1/tickets/overview', {
          headers: { Authorization: `Bearer ${token}` }
        });
        const allTickets = await request<TicketRead[]>('/api/v1/tickets', {
          headers: { Authorization: 'Bearer ' + token },
        });
        setTickets(allTickets);
        setStats(overview);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchOverview();
  }, [token]);

  async function updateTicketStatus(ticketId: string, status: TicketStatus) {
    if (!token) return;
    setIsUpdating(ticketId);
    setError(null);
    try {
      const updated = await request<TicketRead>(`/api/v1/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { Authorization: 'Bearer ' + token },
        body: JSON.stringify({ status }),
      });
      setTickets((current) => current.map((ticket) => ticket.id === updated.id ? updated : ticket));
      setStats((current) => current ? {
        ...current,
        recent_tickets: current.recent_tickets.map((ticket) => ticket.id === updated.id ? updated : ticket),
      } : current);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to update ticket');
    } finally {
      setIsUpdating(null);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setIsCreating(true);
    setError(null);
    try {
      await request('/api/v1/tickets', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title, description, priority, category: 'general' }),
      });
      navigate('/app/chat');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to create ticket');
    } finally {
      setIsCreating(false);
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'P1': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'P2': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'P3': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <Activity size={14} className="text-blue-400" />;
      case 'in_progress': return <Clock size={14} className="text-amber-400" />;
      case 'resolved':
      case 'closed': return <CheckCircle2 size={14} className="text-emerald-400" />;
      default: return <Ticket size={14} className="text-slate-400" />;
    }
  };

  const isAdminOrAgent = user?.role === 'admin' || user?.role === 'agent';

  return (
    <div className="min-h-screen bg-background">
      <header className="px-8 py-6 border-b border-slate-800/50 bg-slate-900/50">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Welcome back, {user?.full_name || 'Agent'}</h1>
            <p className="text-slate-400 text-sm">Enterprise IT Support Portal</p>
          </div>
          <div className="flex items-center gap-4">
            {isAdminOrAgent && (
              <Link to="/app/admin" className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-sm transition-colors flex items-center gap-2">
                <ShieldAlert size={16} /> Admin Center
              </Link>
            )}
            <button onClick={logout} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors">
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Quick Actions & Ticket Form */}
        <div className="space-y-6">
          <div className="bg-panel border border-panel-border rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <MessageSquare size={18} className="text-armin" />
              Quick Help
            </h2>
            <div className="space-y-3">
              <Link to="/app/chat" className="flex items-center justify-between p-4 bg-blue-900/20 hover:bg-blue-900/40 border border-blue-500/20 rounded-xl transition-all group">
                <div>
                  <div className="font-medium text-blue-100 group-hover:text-blue-300 transition-colors">Open LocalOps analysis</div>
                  <div className="text-xs text-blue-300/60 mt-1">AI-powered instant IT support</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                  &rarr;
                </div>
              </Link>
              
              <Link to="/app/knowledge-base" className="flex items-center justify-between p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 rounded-xl transition-all group">
                <div>
                  <div className="font-medium text-slate-200 group-hover:text-white transition-colors">Browse Solutions</div>
                  <div className="text-xs text-slate-400 mt-1">Search the knowledge base</div>
                </div>
                <BookOpen size={18} className="text-slate-500 group-hover:text-slate-300 transition-colors" />
              </Link>
            </div>
          </div>

          <div className="bg-panel border border-panel-border rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Plus size={18} className="text-emerald-400" />
              New Ticket
            </h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Title</label>
                <input 
                  required
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all outline-none"
                  placeholder="Brief summary of the issue"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                <textarea 
                  required
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all outline-none resize-none"
                  placeholder="Detailed description..."
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Priority</label>
                <select 
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all outline-none"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              {error && <div className="text-rose-400 text-xs bg-rose-500/10 p-2 rounded border border-rose-500/20">{error}</div>}
              <button 
                type="submit" 
                disabled={isCreating}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                {isCreating ? 'Submitting...' : 'Submit Ticket'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Active Tickets */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-panel border border-panel-border rounded-2xl p-6 h-full min-h-[500px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Ticket size={18} className="text-indigo-400" />
                Recent Tickets
              </h2>
              <div className="text-xs text-slate-400">
                Total: {stats?.total ?? 0}
              </div>
            </div>

            {isLoading ? (
              <div className="flex justify-center items-center h-48">
                <div className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
              </div>
            ) : tickets.length > 0 ? (
              <div className="space-y-3">
                {tickets.map(ticket => (
                  <div key={ticket.id} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-slate-200 font-medium truncate">{ticket.title}</h3>
                        <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                          <span className="flex items-center gap-1">
                            {getStatusIcon(ticket.status)}
                            <span className="capitalize">{ticket.status.replace('_', ' ')}</span>
                          </span>
                          <span>&bull;</span>
                          <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                          {ticket.category && (
                            <>
                              <span>&bull;</span>
                              <span className="capitalize">{ticket.category}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border tracking-wider ${getSeverityColor(ticket.severity)}`}>
                          {ticket.severity}
                        </span>
                        {ticket.escalation_status === 'pending_review' && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1">
                            <ShieldAlert size={10} /> Escalatated
                          </span>
                        )}
                        {isAdminOrAgent && (
                          <select
                            aria-label={`Update status for ${ticket.title}`}
                            value={ticket.status}
                            disabled={isUpdating === ticket.id}
                            onChange={(event) => updateTicketStatus(ticket.id, event.target.value as TicketStatus)}
                            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-[11px] text-slate-300 disabled:opacity-50"
                          >
                            <option value="open">Open</option>
                            <option value="in_progress">In progress</option>
                            <option value="waiting_on_user">Waiting on user</option>
                            <option value="resolved">Resolved</option>
                            <option value="closed">Closed</option>
                          </select>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-slate-500">
                <Ticket size={32} className="mb-3 opacity-20" />
                <p>No active tickets found.</p>
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
