import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';

export default function AuthFrame({
  title,
  subtitle,
  eyebrow,
  children,
}: {
  title: string;
  subtitle: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <main className="auth-page">
      <section className="auth-hero">
        <div className="auth-hero__content">
          <div className="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>

          <div className="auth-hero__stats" aria-label="Platform highlights">
            <div>
              <strong>Secure by design</strong>
              <span>JWT authentication and role-aware access</span>
            </div>
            <div>
              <strong>AI-assisted triage</strong>
              <span>Smart ticket classification with agent routing</span>
            </div>
            <div>
              <strong>Knowledge-grounded answers</strong>
              <span>RAG-ready helpdesk support experience</span>
            </div>
          </div>
        </div>
      </section>

      <section className="auth-card-shell">
        <div className="auth-card">
          {children}
        </div>
        <p className="auth-card__footer">
          Need the back-office view?{' '}
          <Link to="/app">Open the protected shell</Link>
        </p>
      </section>
    </main>
  );
}
