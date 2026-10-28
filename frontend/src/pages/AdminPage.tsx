import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ShieldAlert, FileText, Settings, Database, ActivitySquare, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { request } from '../lib/api';
import DiagnosticGraph from '../components/admin/DiagnosticGraph';
import EscalationModal from '../components/admin/EscalationModal';

export default function AdminPage() {
  const { token, user } = useAuth();
  
  const [activeTab, setActiveTab] = useState<'escalations' | 'audit' | 'system'>('escalations');
  
  const [metrics, setMetrics] = useState<any>(null);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);

  useEffect(() => {
    fetchMetrics();
    fetchEscalations();
    fetchSystemHealth();
  }, [token]);

  useEffect(() => {
    if (activeTab === 'audit') fetchAuditLogs();
  }, [activeTab, token]);

  const fetchMetrics = async () => {
    if (!token) return;
    try {
      const data = await request<any>('/api/v1/admin/metrics', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMetrics(data);
    } catch (e) { console.error(e); }
  };

  const fetchEscalations = async () => {
    if (!token) return;
    try {
      const data = await request<any[]>('/api/v1/ops/escalations', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEscalations(data || []);
    } catch (e) { console.error(e); }
  };

  const fetchAuditLogs = async () => {
    if (!token) return;
    try {
      const data = await request<any[]>('/api/v1/admin/audit-logs', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAuditLogs(data || []);
    } catch (e) { console.error(e); }
  };
  
  const fetchSystemHealth = async () => {
    if (!token) return;
    try {
      const data = await request<any>('/api/v1/ai/status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSystemHealth(data);
    } catch (e) { console.error(e); }
  };

  const handleResolved = () => {
    setSelectedTicket(null);
    fetchEscalations();
    fetchMetrics();
  };

  if (user?.role !== 'admin' && user?.role !== 'agent') {
    return <div className="p-8 text-rose-400">Unauthorized access.</div>;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="px-8 py-4 border-b border-slate-800/50 bg-slate-900/80 sticky top-0 z-10 backdrop-blur-md">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
              <Activity className="text-indigo-400" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">LocalOps Operations Center</h1>
              <div className="text-[10px] text-slate-400 uppercase tracking-widest mt-0.5">Global System View</div>
            </div>
          </div>
          <Link to="/app" className="text-sm text-slate-400 hover:text-white transition-colors">Back to Dashboard</Link>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto p-8 w-full">
        {/* Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Tickets', value: metrics?.total_tickets || 0, icon: <FileText size={18} /> },
            { label: 'Open P1/P2', value: metrics?.open_p1_p2 || 0, icon: <ShieldAlert size={18} />, color: 'text-rose-400' },
            { label: 'Auto-Resolved', value: metrics?.auto_resolved_rate || '0%', icon: <CheckCircle size={18} />, color: 'text-emerald-400' },
            { label: 'Avg Response', value: metrics?.avg_response_time || '0m', icon: <ActivitySquare size={18} />, color: 'text-indigo-400' },
          ].map((m, i) => (
            <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 flex items-start justify-between">
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">{m.label}</div>
                <div className={`text-2xl font-bold ${m.color || 'text-white'}`}>{m.value}</div>
              </div>
              <div className={`p-2 rounded-lg bg-slate-800 ${m.color || 'text-slate-400'}`}>
                {m.icon}
              </div>
            </div>
          ))}
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 border-b border-slate-800 mb-6">
          {[
            { id: 'escalations', label: 'Pending Escalations', icon: <ShieldAlert size={16} /> },
            { id: 'audit', label: 'Audit Logs', icon: <FileText size={16} /> },
            { id: 'system', label: 'System Health', icon: <Database size={16} /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id 
                  ? 'border-indigo-500 text-indigo-400' 
                  : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-700'
              }`}
            >
              {tab.icon} {tab.label}
              {tab.id === 'escalations' && escalations.length > 0 && (
                <span className="ml-2 bg-rose-500 text-white text-[10px] px-2 py-0.5 rounded-full">{escalations.length}</span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 min-h-[500px]">
          
          {activeTab === 'escalations' && (
            <div className="space-y-6">
              {escalations.length > 0 ? escalations.map(ticket => (
                <div key={ticket.id} className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/50">
                  <div className="p-4 flex items-center justify-between bg-slate-900 border-b border-slate-800">
                    <div className="flex items-center gap-4">
                      <span className="px-2 py-1 rounded text-[10px] font-bold uppercase border tracking-wider bg-rose-500/10 text-rose-400 border-rose-500/20">
                        {ticket.severity}
                      </span>
                      <h3 className="font-semibold text-slate-200">{ticket.title}</h3>
                    </div>
                    <button 
                      onClick={() => setSelectedTicket(ticket)}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                    >
                      <ShieldAlert size={14} /> Review
                    </button>
                  </div>
                  <div className="h-64 border-b border-slate-800">
                    <DiagnosticGraph trail={ticket.diagnostic_trail || []} />
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                  <CheckCircle size={48} className="mb-4 text-emerald-500/30" />
                  <p className="text-lg">No pending escalations.</p>
                  <p className="text-sm">All operations are running autonomously.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-900 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Resource</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="px-4 py-3 font-medium text-indigo-300">{log.action}</td>
                      <td className="px-4 py-3 text-slate-300">{log.resource_type} {log.resource_id?.slice(0, 8)}...</td>
                      <td className="px-4 py-3">
                        {log.severity && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">{log.severity}</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs ${log.status === 'success' ? 'text-emerald-400 bg-emerald-400/10' : 'text-slate-400 bg-slate-800'}`}>
                          {log.status || 'unknown'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="max-w-2xl">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <Settings size={18} className="text-slate-400" /> AI Engine Status
                </h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                      <div className="text-slate-300 font-medium">Ollama Inference Engine</div>
                      <div className="text-xs text-slate-500 mt-1">Provider: {systemHealth?.provider}</div>
                    </div>
                    <div>
                      {systemHealth?.available ? (
                        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-semibold flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div> Online
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-xs font-semibold">Offline</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                      <div className="text-slate-300 font-medium">Model Deployment</div>
                      <div className="text-xs text-slate-500 mt-1">Active Model: {systemHealth?.model}</div>
                    </div>
                    <div className="text-slate-400 text-sm">{systemHealth?.detail}</div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-slate-300 font-medium">Local policy routing</div>
                      <div className="text-xs text-slate-500 mt-1">Status: Active</div>
                    </div>
                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-semibold flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div> Routing
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {selectedTicket && token && (
        <EscalationModal 
          token={token} 
          ticket={selectedTicket} 
          onClose={() => setSelectedTicket(null)} 
          onResolved={handleResolved} 
        />
      )}
    </div>
  );
}
