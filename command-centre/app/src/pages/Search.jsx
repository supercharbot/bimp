import { useState } from 'react';
import { apiCall } from '../api';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    const r = await apiCall('/api/search', { method: 'POST', body: JSON.stringify({ query }) });
    setResults(r);
    setLoading(false);
  };

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '22px' }}>Search</h1>
      <input value={query} onChange={e => setQuery(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && doSearch()}
        placeholder="Ask BIMP anything..."
        className="animate-in"
        style={{
          width: '100%', padding: '12px 18px', background: 'var(--bg-input)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
          color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none',
          transition: 'border-color var(--transition)',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent-border)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />

      {loading && <div className="skeleton" style={{ height: 100, marginTop: 14 }} />}

      {results && !loading && (
        <div style={{ marginTop: '16px' }}>
          {results.chunks?.length ? results.chunks.map((c, i) => (
            <div key={i} className={`card animate-in stagger-${Math.min(i + 1, 5)}`} style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '0.87rem', color: 'var(--text-secondary)', lineHeight: 1.65 }}>{c.text}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px', display: 'flex', gap: '14px' }}>
                <span>{c.source}</span><span>{c.author}</span>
                <span>{new Date(c.timestamp).toLocaleDateString()}</span>
                <span style={{ color: 'var(--accent)' }}>Score: {c.score}</span>
              </div>
            </div>
          )) : <p style={{ color: 'var(--text-muted)', padding: '16px 0' }}>No results found.</p>}
        </div>
      )}
    </div>
  );
}
