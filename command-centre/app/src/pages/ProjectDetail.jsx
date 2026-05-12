import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const card = { background: 'var(--bg-card)', borderRadius: '12px', padding: '20px', border: '1px solid var(--border)', marginBottom: '16px' };
const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };
const badge = (color, bg) => ({ padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem', color, background: bg });

export default function ProjectDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  useEffect(() => { apiCall(`/api/projects/${id}`).then(setData); }, [id]);

  if (!data) return <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />;
  const p = data.project;

  return (
    <motion.div initial="hidden" animate="visible" variants={stagger}>
      <motion.div variants={fadeUp} style={{ marginBottom: '8px' }}>
        <Link to="/projects" style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textDecoration: 'none' }}>← Projects</Link>
      </motion.div>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>{p.property_address || p.job_number}</motion.h1>

      <motion.div variants={stagger} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        {[['Client', p.client_name], ['Job Number', p.job_number], ['Phase', p.phase], ['Status', p.status], ['Documents', data.documents.length]].map(([label, val], i) => (
          <motion.div key={i} variants={fadeUp} style={card}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>{val || '—'}</div>
          </motion.div>
        ))}
      </motion.div>

      {data.action_items.length > 0 && (
        <motion.div variants={fadeUp} style={card}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>Action Items</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{['Description', 'Status', 'Due'].map(h => <th key={h} style={{ textAlign: 'left', padding: '6px 12px', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr></thead>
            <tbody>{data.action_items.map((a, i) => (
              <tr key={i}><td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{a.description}</td>
              <td style={{ padding: '8px 12px' }}><span style={a.status === 'open' ? badge('var(--warning)', 'rgba(245,158,11,0.1)') : badge('var(--success)', 'rgba(16,185,129,0.1)')}>{a.status}</span></td>
              <td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{a.due_date || '—'}</td></tr>
            ))}</tbody>
          </table>
        </motion.div>
      )}

      {data.deadlines.length > 0 && (
        <motion.div variants={fadeUp} style={card}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>Deadlines</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{['Description', 'Status', 'Due'].map(h => <th key={h} style={{ textAlign: 'left', padding: '6px 12px', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr></thead>
            <tbody>{data.deadlines.map((d, i) => (
              <tr key={i}><td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{d.description}</td>
              <td style={{ padding: '8px 12px' }}><span style={d.status === 'open' ? badge('var(--warning)', 'rgba(245,158,11,0.1)') : badge('var(--success)', 'rgba(16,185,129,0.1)')}>{d.status}</span></td>
              <td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{d.due_date || '—'}</td></tr>
            ))}</tbody>
          </table>
        </motion.div>
      )}

      {data.decisions.length > 0 && (
        <motion.div variants={fadeUp} style={card}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>Decisions</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{['Description', 'Date'].map(h => <th key={h} style={{ textAlign: 'left', padding: '6px 12px', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr></thead>
            <tbody>{data.decisions.map((d, i) => (
              <tr key={i}><td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{d.description}</td>
              <td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{d.date || '—'}</td></tr>
            ))}</tbody>
          </table>
        </motion.div>
      )}

      {data.documents.length > 0 && (
        <motion.div variants={fadeUp} style={card}>
          <h2 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>Documents</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{['Subject', 'Source', 'Date'].map(h => <th key={h} style={{ textAlign: 'left', padding: '6px 12px', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>{h}</th>)}</tr></thead>
            <tbody>{data.documents.map((d, i) => (
              <tr key={i}><td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{d.subject || '—'}</td>
              <td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{d.source}</td>
              <td style={{ padding: '8px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{new Date(d.timestamp).toLocaleDateString()}</td></tr>
            ))}</tbody>
          </table>
        </motion.div>
      )}
    </motion.div>
  );
}
