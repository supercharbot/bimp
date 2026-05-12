import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { apiCall } from '../api';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function Chat() {
  const { user } = useAuth();
  const { setChatActive } = useChat();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  const fullName = user?.name || user?.email?.split('@')[0] || '';
  const firstName = fullName.split(' ')[0];

  useEffect(() => {
    setChatActive(messages.length > 0);
  }, [messages.length, setChatActive]);

  useEffect(() => {
    setChatActive(false);
    return () => setChatActive(false);
  }, [setChatActive]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (text) => {
    if (!text?.trim() || loading) return;
    const q = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);

    const result = await apiCall('/api/search', {
      method: 'POST', body: JSON.stringify({ query: q }),
    });

    let reply = '';
    if (result?.chunks?.length) {
      reply = result.chunks.map(c =>
        `${c.text}\n— ${c.source}, ${c.author}, ${new Date(c.timestamp).toLocaleDateString()}`
      ).join('\n\n');
    } else {
      reply = 'No results found for that query.';
    }

    if (result?.deadlines?.length) {
      reply += '\n\nOpen deadlines:\n' + result.deadlines.map(d => `• ${d.description} — due ${d.due_date}`).join('\n');
    }
    if (result?.action_items?.length) {
      reply += '\n\nOpen action items:\n' + result.action_items.map(a => `• ${a.description} — due ${a.due_date || 'no date'}`).join('\n');
    }

    setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    setLoading(false);
    inputRef.current?.focus();
  };

  const hasMessages = messages.length > 0;

  if (!hasMessages) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        minHeight: 'calc(100vh - 56px)',
      }}>
        <div className="fade-in" style={{
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: '36px',
          width: '100%', maxWidth: '600px', padding: '0 24px',
          marginTop: '-80px',
        }}>
          <div style={{ textAlign: 'center' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 600, marginBottom: '10px' }}>
              {getGreeting()}, {firstName}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem' }}>
              How can I help you today?
            </p>
          </div>

          <div style={{ width: '100%' }}>
            <div style={{
              display: 'flex', background: 'var(--bg-surface)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius)',
              overflow: 'hidden', transition: 'border-color var(--transition)',
            }}
            onFocus={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
            onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}>
              <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && send(input)}
                placeholder="Ask BIMP anything..."
                autoFocus
                style={{
                  flex: 1, padding: '16px 20px', background: 'transparent', border: 'none',
                  color: 'var(--text-primary)', fontSize: '1rem', outline: 'none',
                }}
              />
              <button onClick={() => send(input)} disabled={loading || !input.trim()} style={{
                padding: '0 22px', background: 'transparent', border: 'none',
                color: input.trim() ? 'var(--accent)' : 'var(--text-muted)',
                cursor: input.trim() ? 'pointer' : 'default',
                fontSize: '1.1rem', fontWeight: 600, transition: 'color var(--transition)',
              }}>
                ↑
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: 'calc(100vh - 56px)',
      maxWidth: '720px', margin: '0 auto', width: '100%',
    }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px 0' }}>
        {messages.map((m, i) => (
          <div key={i} className="fade-in" style={{
            marginBottom: '22px',
            display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '85%', padding: '14px 18px',
              borderRadius: 'var(--radius)',
              background: m.role === 'user' ? 'var(--accent-soft)' : 'var(--bg-surface)',
              border: `1px solid ${m.role === 'user' ? 'var(--accent-border)' : 'var(--border)'}`,
              fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)',
              whiteSpace: 'pre-wrap',
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="fade-in" style={{ marginBottom: '22px' }}>
            <div style={{
              display: 'inline-block', padding: '14px 18px',
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-muted)', fontSize: '0.88rem',
            }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ padding: '16px 0 20px', borderTop: '1px solid var(--border)' }}>
        <div style={{
          display: 'flex', background: 'var(--bg-surface)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius)',
          overflow: 'hidden', transition: 'border-color var(--transition)',
        }}
        onFocus={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
        onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}>
          <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)}
            placeholder="Ask BIMP anything..."
            style={{
              flex: 1, padding: '15px 18px', background: 'transparent', border: 'none',
              color: 'var(--text-primary)', fontSize: '0.95rem', outline: 'none',
            }}
          />
          <button onClick={() => send(input)} disabled={loading || !input.trim()} style={{
            padding: '0 22px', background: 'transparent', border: 'none',
            color: input.trim() ? 'var(--accent)' : 'var(--text-muted)',
            cursor: input.trim() ? 'pointer' : 'default',
            fontSize: '1.1rem', fontWeight: 600, transition: 'color var(--transition)',
          }}>
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
