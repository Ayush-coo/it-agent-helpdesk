import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthFrame from '../components/AuthFrame';
import { ApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await login({ email, password });
      navigate('/app');
    } catch (submissionError) {
      setError(submissionError instanceof ApiError ? submissionError.message : 'Unable to sign in');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFrame
      eyebrow="Enterprise AI Helpdesk"
      title="Secure, intelligent support for modern IT teams"
      subtitle="Authenticate into a polished workspace that combines ticketing, AI triage, and knowledge-grounded assistance."
    >
      <div className="auth-card__header">
        <h2>Welcome back</h2>
        <p>Sign in to continue managing tickets, AI suggestions, and knowledge-base workflows.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="••••••••"
            required
          />
        </label>

        {error ? <div className="auth-form__error">{error}</div> : null}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <p className="auth-card__switcher">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </AuthFrame>
  );
}
