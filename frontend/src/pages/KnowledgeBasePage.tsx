import { FormEvent, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Upload, BookOpen, Tag } from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { ApiError, request } from '../lib/api';
import type {
  KnowledgeBaseDocument,
  KnowledgeBaseSearchResponse,
} from '../types/knowledgeBase';

export default function KnowledgeBasePage() {
  const { token, user } = useAuth();
  const canIngest = useMemo(() => user?.role === 'admin' || user?.role === 'agent', [user?.role]);

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<KnowledgeBaseSearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [source, setSource] = useState('');
  const [tags, setTags] = useState('');
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [ingestSuccess, setIngestSuccess] = useState<KnowledgeBaseDocument | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = query.trim();
    if (!normalized || !token) return;

    setIsSearching(true);
    setSearchError(null);

    try {
      const response = await request<KnowledgeBaseSearchResponse>(
        `/api/v1/knowledge-base/search?query=${encodeURIComponent(normalized)}&k=5`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setSearchResults(response);
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  }

  async function handleIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canIngest || !token) return;

    setIsIngesting(true);
    setIngestError(null);
    setIngestSuccess(null);

    try {
      const response = await request<KnowledgeBaseDocument>('/api/v1/knowledge-base/ingest', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          title: title.trim(),
          content: content.trim(),
          source: source.trim() || null,
          tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
        }),
      });
      setIngestSuccess(response);
      setTitle('');
      setContent('');
      setSource('');
      setTags('');
    } catch (err) {
      setIngestError(err instanceof ApiError ? err.message : 'Ingestion failed');
    } finally {
      setIsIngesting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="px-8 py-6 border-b border-slate-800/50 bg-slate-900/50">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <BookOpen size={24} className="text-armin" /> RAG Knowledge Base
            </h1>
            <p className="text-sm text-slate-400 mt-1">Search and curate local troubleshooting evidence.</p>
          </div>
          <div className="flex gap-4 text-sm">
            <Link to="/app/chat" className="text-slate-400 hover:text-white transition-colors">Open Chatbot</Link>
            <Link to="/app" className="text-slate-400 hover:text-white transition-colors">Dashboard</Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Search */}
        <div className="bg-panel border border-panel-border rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Search size={18} className="text-armin" /> Search Knowledge Base
          </h2>
          <form className="space-y-4" onSubmit={handleSearch}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="VPN disconnect after password reset"
              required
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-200 outline-none focus:border-armin/50 focus:ring-1 focus:ring-armin/50 transition-all"
            />
            <button
              type="submit"
              disabled={isSearching}
              className="w-full py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-armin to-armin-hover text-slate-900 disabled:opacity-50 transition-all"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </form>
          {searchError && <div className="mt-3 px-3 py-2 rounded bg-rose-500/10 text-rose-400 text-sm border border-rose-500/20">{searchError}</div>}

          <div className="mt-4 space-y-3">
            {searchResults?.results.length ? (
              searchResults.results.map((item) => (
                <div key={item.id} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                  <strong className="text-sm text-slate-200 block mb-1">{item.title}</strong>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.snippet}</p>
                  <div className="flex gap-3 mt-2 text-[11px] text-slate-500">
                    <span>score: {item.score.toFixed(3)}</span>
                    {item.source && <span>source: {item.source}</span>}
                    {item.tags?.length > 0 && (
                      <span className="flex items-center gap-1"><Tag size={10} /> {item.tags.join(', ')}</span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 mt-2">No results yet. Try a search above.</p>
            )}
          </div>
        </div>

        {/* Ingest */}
        <div className="bg-panel border border-panel-border rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Upload size={18} className="text-emerald-400" /> Ingest Document
          </h2>
          {canIngest ? (
            <form className="space-y-4" onSubmit={handleIngest}>
              <label className="block">
                <span className="text-xs font-medium text-slate-400 mb-1 block">Title</span>
                <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Resetting VPN certificates" required className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50" />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-400 mb-1 block">Source</span>
                <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="Internal wiki / SOP" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50" />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-400 mb-1 block">Tags (comma-separated)</span>
                <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="vpn,certificates,windows" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50" />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-400 mb-1 block">Content</span>
                <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={8} placeholder="Step-by-step resolution notes..." required className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 resize-none" />
              </label>
              <button type="submit" disabled={isIngesting} className="w-full py-2.5 rounded-lg font-semibold text-sm bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 transition-all">
                {isIngesting ? 'Ingesting...' : 'Ingest Document'}
              </button>
            </form>
          ) : (
            <p className="text-sm text-slate-500">Only admins and agents can ingest new knowledge items.</p>
          )}
          {ingestError && <div className="mt-3 px-3 py-2 rounded bg-rose-500/10 text-rose-400 text-sm border border-rose-500/20">{ingestError}</div>}
          {ingestSuccess && <p className="mt-3 text-emerald-400 text-sm">Saved: {ingestSuccess.title}</p>}
        </div>
      </main>
    </div>
  );
}