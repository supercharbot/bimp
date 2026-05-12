import { useEffect, useState } from 'react';
import { apiCall } from '../api';

export default function HoldingQueue() {
  const [queue, setQueue] = useState(null);
  useEffect(() => { apiCall('/api/holding-queue').then(setQueue); }, []);

  if (!queue) return <div className="skeleton" style={{ height: 200 }} />;

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '22px' }}>Holding Queue</h1>
      {!queue.length && <p style={{ color: 'var(--text-muted)' }}>No pending items. All documents have been matched.</p>}
      {queue.map((item, i) => (
        <div key={i} className={`card animate-in stagger-${Math.min(i + 1, 5)}`} style={{ marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.8rem' }}>{item.document_id}</div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                Arrived: {new Date(item.arrived_at).toLocaleDateString()} · Expires: {new Date(item.expires_at).toLocaleDateString()}
              </div>
            </div>
            <span className="badge badge-open">{item.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
