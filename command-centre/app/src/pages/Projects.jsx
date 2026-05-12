import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiCall } from '../api';

export default function Projects() {
  const [projects, setProjects] = useState(null);
  useEffect(() => { apiCall('/api/projects').then(setProjects); }, []);

  if (!projects) return <div className="skeleton" style={{ height: 200 }} />;

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '22px' }}>Projects</h1>
      {!projects.length && <p style={{ color: 'var(--text-muted)' }}>No projects yet.</p>}
      {projects.map((p, i) => (
        <Link key={p.project_id} to={`/projects/${p.project_id}`}
          className={`card animate-in stagger-${Math.min(i + 1, 5)}`}
          style={{ display: 'block', marginBottom: '10px', transition: 'border-color var(--transition)' }}
          onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-heading)', fontSize: '0.95rem' }}>
                {p.job_number || '—'} · {p.client_name || 'No client'}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.83rem', marginTop: '3px' }}>{p.property_address || ''}</div>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              {p.phase && <span className="badge badge-phase">{p.phase}</span>}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
