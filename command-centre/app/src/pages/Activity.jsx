import { useEffect, useState } from 'react';
import { apiCall } from '../api';

export default function Activity() {
  const [activity, setActivity] = useState(null);
  useEffect(() => { apiCall('/api/activity').then(setActivity); }, []);

  if (!activity) return <div className="skeleton" style={{ height: 200 }} />;

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '22px' }}>Activity Feed</h1>
      {!activity.length && <p style={{ color: 'var(--text-muted)' }}>No activity yet.</p>}
      <div style={{ position: 'relative', paddingLeft: '20px' }}>
        <div style={{ position: 'absolute', left: '5px', top: 4, bottom: 4, width: '1px', background: 'var(--border)' }} />
        {activity.map((a, i) => (
          <div key={i} className={`animate-in stagger-${Math.min(i + 1, 5)}`} style={{ marginBottom: '12px', position: 'relative' }}>
            <div style={{ position: 'absolute', left: '-18px', top: '8px', width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent)' }} />
            <div className="card" style={{ padding: '12px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{a.type}</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{new Date(a.timestamp).toLocaleString()}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{a.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
