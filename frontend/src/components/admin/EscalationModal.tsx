import { useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle } from 'lucide-react';
import { request } from '../../lib/api';

interface EscalationModalProps {
  token: string;
  ticket: any;
  onClose: () => void;
  onResolved: () => void;
}

export default function EscalationModal({ token, ticket, onClose, onResolved }: EscalationModalProps) {
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (action: 'approve' | 'reject') => {
    if (action === 'reject' && !reason.trim()) {
      setError('A reason is required when rejecting an escalation.');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    try {
      await request(`/api/v1/ops/escalations/${ticket.id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ action, reason }),
      });
      onResolved();
    } catch (err: any) {
      setError(err?.message || `Failed to ${action} escalation`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!ticket) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div className="p-6 border-b border-slate-800 bg-slate-950/50 flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center shrink-0 border border-rose-500/20">
            <ShieldAlert className="text-rose-400" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Human-in-the-Loop Escalation</h2>
            <p className="text-slate-400 text-sm">LocalOps halted execution due to policy risk or missing permissions.</p>
          </div>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Incident Details</div>
            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800">
              <div className="flex items-center gap-3 mb-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase border tracking-wider bg-rose-500/10 text-rose-400 border-rose-500/20">{ticket.severity}</span>
                <span className="text-slate-200 font-medium">{ticket.title}</span>
              </div>
              <p className="text-sm text-slate-400">{ticket.description}</p>
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Affected Assets</div>
            {ticket.affected_assets?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {ticket.affected_assets.map((asset: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-300 font-mono">
                    {asset}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-500 italic">No structural assets detected.</div>
            )}
          </div>

          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Authorization Note</div>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter reason for approval or rejection..."
              rows={3}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 resize-none outline-none"
            />
            {error && <div className="mt-2 text-xs text-rose-400">{error}</div>}
          </div>
        </div>

        <div className="p-6 border-t border-slate-800 bg-slate-950/50 flex items-center justify-end gap-3">
          <button 
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={() => handleAction('reject')}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-rose-400 border border-rose-500/30 rounded-lg transition-colors disabled:opacity-50"
          >
            <XCircle size={16} /> Reject
          </button>
          <button 
            onClick={() => handleAction('approve')}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50"
          >
            <CheckCircle size={16} /> Approve Execution
          </button>
        </div>
      </div>
    </div>
  );
}
