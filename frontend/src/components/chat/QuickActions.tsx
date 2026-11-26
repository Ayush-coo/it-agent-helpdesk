import { Key, ShieldAlert, Printer, Activity, Ticket } from 'lucide-react';

interface QuickActionsProps {
  onSelectAction: (text: string) => void;
  disabled: boolean;
}

export default function QuickActions({ onSelectAction, disabled }: QuickActionsProps) {
  const actions = [
    { icon: <Key size={16} />, label: 'Reset My Password', text: 'Please reset my Active Directory password.' },
    { icon: <ShieldAlert size={16} />, label: 'Fix VPN Connection', text: 'I am having trouble with my VPN connection, can you flush the sessions?' },
    { icon: <Printer size={16} />, label: 'Fix Printer', text: 'My printer is stuck, can you restart the print spooler?' },
    { icon: <Activity size={16} />, label: 'System Health', text: 'Please run a system health check.' },
    { icon: <Ticket size={16} />, label: 'Create Ticket', text: 'I need to create a new support ticket.' },
  ];

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {actions.map((action, i) => (
        <button
          key={i}
          disabled={disabled}
          onClick={() => onSelectAction(action.text)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-900/30 hover:bg-blue-800/50 border border-blue-500/30 text-blue-100 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className="text-armin">{action.icon}</span>
          {action.label}
        </button>
      ))}
    </div>
  );
}
