import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const card = {
  background: 'var(--bg-card)', borderRadius: '12px', padding: '24px',
  border: '1px solid var(--border)',
};

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.35 } } };

export default function Dashboard() {
  const [data, setData] = useState(null);
  useEffect(() => { apiCall('/api/dashboard').then(setData); }, []);

  if (!data) return <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />;

  const stats = [
    { label: 'Projects', value: data.project_count, color: 'var(--accent)' },
    { label: 'Documents', value: data.document_count, color: 'var(--text-secondary)' },
    { label: 'Open Actions', value: data.open_actions, color: 'var(--warning)' },
    { label: 'Deadlines', value: data.open_deadlines, color: 'var(--danger)' },
    { label: 'Pending Queue', value: data.pending_queue, color: 'var(--text-muted)' },
  ];

  return (
    <motion.div initial="hidden" animate="visible" variants={stagger}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Dashboard</motion.h1>

      <motion.div variants={stagger} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px', marginBottom: '28px' }}>
        {stats.map((s, i) => (
          <motion.div key={i} variants={fadeUp} style={card}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color, fontFamily: 'Plus Jakarta Sans, sans-serif', marginTop: '4px' }}>{s.value}</div>
          </motion.div>
        ))}
      </motion.div>

      {data.overdue_actions.length > 0 && (
        <motion.div variants={fadeUp} style={{ ...card, marginBottom: '16px', borderLeftColor: 'var(--danger)', borderLeftWidth: '3px' }}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--danger)', marginBottom: '12px' }}>Overdue Actions</h2>
          <Table headers={['Description', 'Due']} rows={data.overdue_actions.map(a => [a.description, a.due_date])} />
        </motion.div>
      )}

      {data.upcoming_deadlines.length > 0 && (
        <motion.div variants={fadeUp} style={{ ...card, marginBottom: '16px', borderLeftColor: 'var(--warning)', borderLeftWidth: '3px' }}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--warning)', marginBottom: '12px' }}>Deadlines This Week</h2>
          <Table headers={['Description', 'Due']} rows={data.upcoming_deadlines.map(d => [d.description, d.due_date])} />
        </motion.div>
      )}

      {data.recent_activity.length > 0 && (
        <motion.div variants={fadeUp} style={card}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>Recent Activity</h2>
          <Table headers={['Type', 'Description', 'Time']} rows={data.recent_activity.map(a => [a.type, a.description, new Date(a.timestamp).toLocaleString()])} />
        </motion.div>
      )}
    </motion.div>
  );
}

function Table({ headers, rows }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>{headers.map((h, i) => <th key={i} style={{ textAlign: 'left', padding: '6px 12px', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} style={{ borderBottom: '1px solid var(--bg-hover)' }}>
            {row.map((cell, j) => <td key={j} style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{cell}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
