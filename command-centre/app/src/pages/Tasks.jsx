import { useEffect, useState } from 'react';
import { apiCall } from '../api';

export default function Tasks() {
  const [projects, setProjects] = useState(null);
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    apiCall('/api/projects').then(async (projs) => {
      if (!projs) return;
      setProjects(projs);
      const allTasks = [];
      for (const p of projs) {
        const detail = await apiCall(`/api/projects/${p.project_id}`);
        if (detail?.action_items) {
          detail.action_items.forEach(a => allTasks.push({ ...a, project_name: p.property_address || p.job_number }));
        }
      }
      setTasks(allTasks);
    });
  }, []);

  if (!projects) return <div className="skeleton" style={{ height: 200 }} />;

  const open = tasks.filter(t => t.status === 'open');
  const completed = tasks.filter(t => t.status === 'completed');

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '22px' }}>Tasks</h1>
      {!tasks.length && <p style={{ color: 'var(--text-muted)' }}>No tasks yet.</p>}

      {open.length > 0 && (
        <div className="card animate-in" style={{ marginBottom: '14px' }}>
          <h2 style={{ fontSize: '0.9rem', color: 'var(--warning)', marginBottom: '10px' }}>Open ({open.length})</h2>
          {open.map((t, i) => (
            <div key={i} style={{ padding: '9px 0', borderBottom: i < open.length - 1 ? '1px solid var(--bg-hover)' : 'none', display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t.description}</div>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '2px' }}>{t.project_name}</div>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', marginLeft: '16px' }}>{t.due_date || '—'}</div>
            </div>
          ))}
        </div>
      )}

      {completed.length > 0 && (
        <div className="card animate-in stagger-2">
          <h2 style={{ fontSize: '0.9rem', color: 'var(--success)', marginBottom: '10px' }}>Completed ({completed.length})</h2>
          {completed.map((t, i) => (
            <div key={i} style={{ padding: '8px 0', borderBottom: i < completed.length - 1 ? '1px solid var(--bg-hover)' : 'none' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textDecoration: 'line-through' }}>{t.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
