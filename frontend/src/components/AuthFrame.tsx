import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';
import { Sparkles } from 'lucide-react';

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
    <main className="min-h-screen flex items-center justify-center bg-[#212121] p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center mb-4 shadow-lg">
            <Sparkles className="text-black" size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-100 tracking-wide">RECINE AI</h1>
          <p className="text-sm text-gray-500 mt-1">{eyebrow}</p>
        </div>

        {/* Card */}
        <div className="bg-[#2f2f2f] rounded-2xl border border-gray-700/50 shadow-xl p-8">
          <h2 className="text-lg font-semibold text-gray-100 mb-1">{title}</h2>
          <p className="text-sm text-gray-400 mb-6">{subtitle}</p>
          {children}
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Enterprise recruitment intelligence
        </p>
      </div>
    </main>
  );
}
