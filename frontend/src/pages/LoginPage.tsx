import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthFrame from '../components/AuthFrame';
import { ApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, demoLogin } = useAuth();
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

  function handleDemoLogin() {
    demoLogin();
    navigate('/app');
  }

  return (
    <AuthFrame
      eyebrow="LocalOps Helpdesk · Local IT operations"
      title="Welcome to LocalOps"
      subtitle="Sign in for explainable, policy-aware IT support."
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="text-sm font-medium text-gray-300 mb-1 block">Email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
            className="w-full bg-[#212121] border border-gray-600/50 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder:text-gray-500 outline-none focus:border-gray-400 focus:ring-1 focus:ring-gray-400/30 transition-all"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-gray-300 mb-1 block">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="w-full bg-[#212121] border border-gray-600/50 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder:text-gray-500 outline-none focus:border-gray-400 focus:ring-1 focus:ring-gray-400/30 transition-all"
          />
        </label>

        {error && (
          <div className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 rounded-xl font-semibold text-sm bg-white text-black hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="mt-4 pt-4 border-t border-gray-700/50">
        <button
          type="button"
          onClick={handleDemoLogin}
          className="w-full py-3 rounded-xl font-semibold text-sm bg-[#d5f466] text-[#173c32] hover:bg-[#e2ff8a] transition-all"
        >
          Enter demo workspace
        </button>
      </div>

      <p className="text-center text-sm text-gray-500 mt-6">
        New here?{' '}
        <Link to="/register" className="text-white hover:underline">Create an account</Link>
      </p>
    </AuthFrame>
  );
}
