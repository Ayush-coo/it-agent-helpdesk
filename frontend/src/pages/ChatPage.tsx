import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, LogOut, Settings, ShieldAlert, Plus } from 'lucide-react';
import LocalOpsChat from '../components/chat/LocalOpsChat';
import { useAuth } from '../contexts/AuthContext';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [chatSession, setChatSession] = useState(0);

  const isAdminOrAgent = user?.role === 'admin' || user?.role === 'agent';

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-[#212121] text-gray-100 font-sans overflow-hidden">
      {/* Sidebar */}
      <div 
        className={`${isSidebarOpen ? 'w-64' : 'w-0'} bg-[#171717] flex-shrink-0 transition-all duration-300 overflow-hidden flex flex-col border-r border-gray-800`}
      >
        <div className="p-3">
          <button
            onClick={() => setChatSession((current) => current + 1)}
            className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg hover:bg-gray-800 transition-colors text-sm font-medium"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>

        <div className="flex-1" />
        <div className="p-3 border-t border-gray-800 space-y-1">
          {isAdminOrAgent && (
            <Link to="/app/admin" className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm">
              <ShieldAlert size={16} />
              Admin Center
            </Link>
          )}
          <button className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm">
            <Settings size={16} />
            Settings
          </button>
          <button onClick={logout} className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm text-red-400">
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#212121] relative">
        {/* Mobile Header / Sidebar Toggle */}
        <div className="h-12 flex items-center px-4 md:hidden">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-gray-400 hover:text-white">
            <Bot size={24} />
          </button>
          <span className="ml-3 font-semibold">LocalOps</span>
        </div>

        {/* Desktop Sidebar Toggle (Optional, can just leave sidebar fixed) */}
        
        <main className="flex-1 overflow-hidden relative w-full h-full">
          <LocalOpsChat key={chatSession} />
        </main>
      </div>
    </div>
  );
}
