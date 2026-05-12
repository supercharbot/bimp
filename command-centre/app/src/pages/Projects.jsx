import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function Projects() {
  const [projects, setProjects] = useState(null);
  useEffect(() => { apiCall('/api/projects').then(setProjects); }, []);

  if (!projects) return <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />;

  return (
    <motion.div initial="hidden" animate="visible" variants={stagger}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Projects</motion.h1>
      {!projects.length && <motion.p variants={fadeUp} style={{ color: 'var(--text-muted)' }}>No projects yet.</motion.p>}
      {projects.map(p => (
        <motion.div key={p.project_id} variants={fadeUp}>
          <Link to={`/projects/${p.project_id}`} style={{
            display: 'block', padding: '20px 24px', background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '10px', marginBottom: '10px', textDecoration: 'none', color: 'var(--text-primary)',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--bg-hover)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--bg-card)'; }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontFamily: 'Plus Jakarta Sans, sans-serif' }}>
                  {p.job_number || 'No job number'} — {p.client_name || 'No client'}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>{p.property_address || ''}</div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {p.phase && <span style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', background: 'var(--accent-glow)', color: 'var(--accent)' }}>{p.phase}</span>}
                {p.status && <span style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', background: 'rgba(16,185,129,0.1)', color: 'var(--success)' }}>{p.status}</span>}
              </div>
            </div>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
