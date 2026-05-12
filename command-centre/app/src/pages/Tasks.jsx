import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };
const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };

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

  if (!projects) return <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />;

  const open = tasks.filter(t => t.status === 'open');
  const completed = tasks.filter(t => t.status === 'completed');

  return (
    <motion.div initial="hidden" animate="visible" variants={stagger}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Tasks</motion.h1>
      {!tasks.length && <motion.p variants={fadeUp} style={{ color: 'var(--text-muted)' }}>No tasks yet.</motion.p>}

      {open.length > 0 && (
        <motion.div variants={fadeUp} style={{ background: 'var(--bg-card)', borderRadius: '12px', padding: '20px', border: '1px solid var(--border)', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--warning)', marginBottom: '12px' }}>Open ({open.length})</h2>
          {open.map((t, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--bg-hover)', display: 'flex', justifyContent: 'space-between' }}>
              <div><div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t.description}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>{t.project_name}</div></div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{t.due_date || '—'}</div>
            </div>
          ))}
        </motion.div>
      )}

      {completed.length > 0 && (
        <motion.div variants={fadeUp} style={{ background: 'var(--bg-card)', borderRadius: '12px', padding: '20px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--success)', marginBottom: '12px' }}>Completed ({completed.length})</h2>
          {completed.map((t, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--bg-hover)' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textDecoration: 'line-through' }}>{t.description}</div>
            </div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
