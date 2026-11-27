import { BrowserRouter, Navigate, NavLink, Route, Routes } from 'react-router-dom';

import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import AdminPage from './pages/AdminPage';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TicketDetailPage from './pages/TicketDetailPage';
import TicketsPage from './pages/TicketsPage';

function AppLayout() {
  const links = [
    { to: '/app', label: 'Dashboard', end: true },
    { to: '/app/tickets', label: 'Tickets', end: false },
    { to: '/app/chat', label: 'Chat', end: false },
    { to: '/app/knowledge-base', label: 'Knowledge Base', end: false },
  ];

  return (
    <>
      <nav className="flex items-center gap-2 border-b border-slate-800 bg-slate-950 px-6 py-3 text-sm">
        <span className="mr-5 font-semibold text-white">LocalOps</span>
        {links.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 transition-colors ${
                isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route index element={<DashboardPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="tickets/:ticketId" element={<TicketDetailPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/app/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
