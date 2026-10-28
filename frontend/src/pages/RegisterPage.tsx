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
      eyebrow="Local-first IT operations"
      title="Create your account"
      subtitle="Start a governed, local-first IT operations workspace."
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="text-sm font-medium text-gray-300 mb-1 block">Full name</span>
          <input
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Alex Morgan"
            className="w-full bg-[#212121] border border-gray-600/50 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder:text-gray-500 outline-none focus:border-gray-400 focus:ring-1 focus:ring-gray-400/30 transition-all"
          />
        </label>

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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimum 8 characters"
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
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Already have an account?{' '}
        <Link to="/login" className="text-white hover:underline">Sign in</Link>
      </p>
    </AuthFrame>
  );
}
