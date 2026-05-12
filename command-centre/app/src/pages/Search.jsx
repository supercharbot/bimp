import { useState } from 'react';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

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
    <motion.div initial="hidden" animate="visible" variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.06 } } }}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Search</motion.h1>
      <motion.div variants={fadeUp}>
        <input value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch()}
          placeholder="Ask BIMP anything..."
          style={{
            width: '100%', padding: '14px 20px', background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '10px', color: 'var(--text-primary)', fontSize: '0.95rem', outline: 'none',
            transition: 'border-color 0.15s',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--accent)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
      </motion.div>

      {loading && <div className="skeleton" style={{ height: 120, borderRadius: 12, marginTop: 16 }} />}

      {results && !loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: '20px' }}>
          {results.chunks?.length ? results.chunks.map((c, i) => (
            <div key={i} style={{
              padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: '10px', marginBottom: '10px',
            }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{c.text}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px', display: 'flex', gap: '16px' }}>
                <span>{c.source}</span><span>{c.author}</span>
                <span>{new Date(c.timestamp).toLocaleDateString()}</span>
                <span style={{ color: 'var(--accent)' }}>Score: {c.score}</span>
              </div>
            </div>
          )) : <div style={{ color: 'var(--text-muted)', padding: '20px' }}>No results found.</div>}
        </motion.div>
      )}
    </motion.div>
  );
}
