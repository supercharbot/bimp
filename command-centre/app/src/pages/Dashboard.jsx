import { useEffect, useState } from 'react';
import { apiCall } from '../api';

export default function Dashboard() {
  const [data, setData] = useState(null);
  useEffect(() => { apiCall('/api/dashboard').then(setData); }, []);

  if (!data) return <div className="skeleton" style={{ height: 280 }} />;

  const stats = [
    { label: 'Projects', value: data.project_count },
    { label: 'Documents', value: data.document_count },
    { label: 'Open Actions', value: data.open_actions },
    { label: 'Deadlines', value: data.open_deadlines },
    { label: 'Pending Queue', value: data.pending_queue },
  ];

  return (
    <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto' }}>
      <h1 className="fade-in" style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '28px' }}>
        {stats.map((s, i) => (
          <div key={i} className={`card fade-in d${Math.min(i + 1, 5)}`}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
            <div style={{ fontSize: '1.9rem', fontWeight: 700, fontFamily: 'var(--font-heading)', marginTop: '4px' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {data.overdue_actions.length > 0 && (
        <div className="card fade-in d3" style={{ marginBottom: '14px', borderLeft: '2px solid var(--danger)' }}>
          <h2 style={{ fontSize: '0.9rem', color: 'var(--danger)', marginBottom: '10px' }}>Overdue Actions</h2>
          <table><thead><tr><th>Description</th><th>Due</th></tr></thead>
          <tbody>{data.overdue_actions.map((a, i) => (
            <tr key={i}><td>{a.description}</td><td><span className="badge badge-overdue">{a.due_date}</span></td></tr>
          ))}</tbody></table>
        </div>
      )}

      {data.upcoming_deadlines.length > 0 && (
        <div className="card fade-in d4" style={{ marginBottom: '14px', borderLeft: '2px solid var(--warning)' }}>
          <h2 style={{ fontSize: '0.9rem', color: 'var(--warning)', marginBottom: '10px' }}>Deadlines This Week</h2>
          <table><thead><tr><th>Description</th><th>Due</th></tr></thead>
          <tbody>{data.upcoming_deadlines.map((d, i) => (
            <tr key={i}><td>{d.description}</td><td><span className="badge badge-open">{d.due_date}</span></td></tr>
          ))}</tbody></table>
        </div>
      )}

      {data.recent_activity.length > 0 && (
        <div className="card fade-in d5">
          <h2 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>Recent Activity</h2>
          <table><thead><tr><th>Type</th><th>Description</th><th>Time</th></tr></thead>
          <tbody>{data.recent_activity.map((a, i) => (
            <tr key={i}><td>{a.type}</td><td>{a.description}</td><td>{new Date(a.timestamp).toLocaleString()}</td></tr>
          ))}</tbody></table>
        </div>
      )}
    </div>
  );
}
