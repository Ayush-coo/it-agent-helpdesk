import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isHydrating } = useAuth();

  if (isHydrating) {
    return (
      <div className="route-state">
        <span>Loading session</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}