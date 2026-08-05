import { FormEvent, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

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
    if (!normalized || !token) {
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    try {
      const response = await request<KnowledgeBaseSearchResponse>(
        `/api/v1/knowledge-base/search?query=${encodeURIComponent(normalized)}&k=5`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      setSearchResults(response);
    } catch (searchRequestError) {
      setSearchError(searchRequestError instanceof ApiError ? searchRequestError.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  }

  async function handleIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canIngest || !token) {
      return;
    }

    setIsIngesting(true);
    setIngestError(null);
    setIngestSuccess(null);

    try {
      const response = await request<KnowledgeBaseDocument>('/api/v1/knowledge-base/ingest', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: title.trim(),
          content: content.trim(),
          source: source.trim() || null,
          tags: tags
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });
      setIngestSuccess(response);
      setTitle('');
      setContent('');
      setSource('');
      setTags('');
    } catch (ingestRequestError) {
      setIngestError(ingestRequestError instanceof ApiError ? ingestRequestError.message : 'Ingestion failed');
    } finally {
      setIsIngesting(false);
    }
  }

  return (
    <main className="kb-page">
      <section className="kb-shell">
        <header className="kb-header">
          <div>
            <div className="eyebrow">Milestone 7</div>
            <h1>RAG knowledge base</h1>
            <p>
              Search and curate troubleshooting documents for chatbot retrieval. Signed in as {user?.email}.
            </p>
          </div>
          <div className="kb-header__links">
            <Link to="/app/chat">Open chatbot</Link>
            <Link to="/app">Dashboard</Link>
          </div>
        </header>

        <section className="kb-grid">
          <article className="kb-card">
            <h2>Search knowledge base</h2>
            <form className="kb-form" onSubmit={handleSearch}>
              <label>
                Search query
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="VPN disconnect after password reset"
                  required
                />
              </label>
              <button type="submit" disabled={isSearching}>
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </form>
            {searchError ? <div className="auth-form__error">{searchError}</div> : null}

            <div className="kb-results">
              {searchResults?.results.length ? (
                searchResults.results.map((item) => (
                  <article key={item.id} className="kb-result">
                    <strong>{item.title}</strong>
                    <p>{item.snippet}</p>
                    <div>
                      <span>score: {item.score.toFixed(3)}</span>
                      {item.source ? <span>source: {item.source}</span> : null}
                    </div>
                  </article>
                ))
              ) : (
                <p className="kb-empty">No search results yet.</p>
              )}
            </div>
          </article>

          <article className="kb-card">
            <h2>Ingest document</h2>
            {canIngest ? (
              <form className="kb-form" onSubmit={handleIngest}>
                <label>
                  Title
                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Resetting VPN certificates"
                    required
                  />
                </label>
                <label>
                  Source
                  <input
                    value={source}
                    onChange={(event) => setSource(event.target.value)}
                    placeholder="Internal wiki / SOP"
                  />
                </label>
                <label>
                  Tags (comma-separated)
                  <input
                    value={tags}
                    onChange={(event) => setTags(event.target.value)}
                    placeholder="vpn,certificates,windows"
                  />
                </label>
                <label>
                  Content
                  <textarea
                    value={content}
                    onChange={(event) => setContent(event.target.value)}
                    rows={10}
                    placeholder="Step-by-step resolution notes"
                    required
                  />
                </label>
                <button type="submit" disabled={isIngesting}>
                  {isIngesting ? 'Ingesting...' : 'Ingest document'}
                </button>
              </form>
            ) : (
              <p className="kb-empty">Only admins and agents can ingest new knowledge items.</p>
            )}

            {ingestError ? <div className="auth-form__error">{ingestError}</div> : null}
            {ingestSuccess ? (
              <p className="kb-success">Saved: {ingestSuccess.title}</p>
            ) : null}
          </article>
        </section>
      </section>
    </main>
  );
}