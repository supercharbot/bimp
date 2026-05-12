import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiCall } from '../api';

export default function ProjectDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  useEffect(() => { apiCall(`/api/projects/${id}`).then(setData); }, [id]);

  if (!data) return <div className="skeleton" style={{ height: 300 }} />;
  const p = data.project;

  const Section = ({ title, children, color }) => (
    <div className="card animate-in" style={{ marginBottom: '14px', borderLeft: color ? `2px solid ${color}` : undefined }}>
      <h2 style={{ fontSize: '0.9rem', color: color || 'var(--text-secondary)', marginBottom: '10px' }}>{title}</h2>
      {children}
    </div>
  );

  return (
    <div>
      <Link to="/projects" className="animate-in" style={{ fontSize: '0.83rem', color: 'var(--text-muted)', display: 'inline-block', marginBottom: '8px' }}>← Projects</Link>
      <h1 className="animate-in stagger-1" style={{ fontSize: '1.4rem', marginBottom: '22px' }}>{p.property_address || p.job_number}</h1>

      <div className="animate-in stagger-2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '22px' }}>
        {[['Client', p.client_name], ['Job Number', p.job_number], ['Phase', p.phase], ['Status', p.status], ['Documents', data.documents.length]].map(([label, val], i) => (
          <div key={i} className="card">
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '3px' }}>{val || '—'}</div>
          </div>
        ))}
      </div>

      {data.action_items.length > 0 && (
        <Section title="Action Items">
          <table><thead><tr><th>Description</th><th>Status</th><th>Due</th></tr></thead>
          <tbody>{data.action_items.map((a, i) => (
            <tr key={i}><td>{a.description}</td>
            <td><span className={`badge ${a.status === 'open' ? 'badge-open' : 'badge-completed'}`}>{a.status}</span></td>
            <td>{a.due_date || '—'}</td></tr>
          ))}</tbody></table>
        </Section>
      )}

      {data.deadlines.length > 0 && (
        <Section title="Deadlines">
          <table><thead><tr><th>Description</th><th>Status</th><th>Due</th></tr></thead>
          <tbody>{data.deadlines.map((d, i) => (
            <tr key={i}><td>{d.description}</td>
            <td><span className={`badge ${d.status === 'open' ? 'badge-open' : 'badge-completed'}`}>{d.status}</span></td>
            <td>{d.due_date || '—'}</td></tr>
          ))}</tbody></table>
        </Section>
      )}

      {data.decisions.length > 0 && (
        <Section title="Decisions">
          <table><thead><tr><th>Description</th><th>Date</th></tr></thead>
          <tbody>{data.decisions.map((d, i) => (
            <tr key={i}><td>{d.description}</td><td>{d.date || '—'}</td></tr>
          ))}</tbody></table>
        </Section>
      )}

      {data.documents.length > 0 && (
        <Section title="Documents">
          <table><thead><tr><th>Subject</th><th>Source</th><th>Date</th></tr></thead>
          <tbody>{data.documents.map((d, i) => (
            <tr key={i}><td>{d.subject || '—'}</td><td>{d.source}</td><td>{new Date(d.timestamp).toLocaleDateString()}</td></tr>
          ))}</tbody></table>
        </Section>
      )}
    </div>
  );
}
