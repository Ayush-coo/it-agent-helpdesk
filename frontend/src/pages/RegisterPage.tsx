import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthFrame from '../components/AuthFrame';
import { ApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await register({
        full_name: fullName.trim() || null,
        email,
        password,
      });
      navigate('/app');
    } catch (submissionError) {
      setError(submissionError instanceof ApiError ? submissionError.message : 'Unable to create account');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFrame
      eyebrow="Milestone 5"
      title="Create an account for the helpdesk agent"
      subtitle="Register once, then use the same JWT session to access tickets and future admin tools."
    >
      <div className="auth-card__header">
        <h2>Get started</h2>
        <p>Registration calls the backend auth endpoint directly.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Full name
          <input
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Alex Morgan"
          />
        </label>

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
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Minimum 8 characters"
            required
          />
        </label>

        {error ? <div className="auth-form__error">{error}</div> : null}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p className="auth-card__switcher">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </AuthFrame>
  );
}
