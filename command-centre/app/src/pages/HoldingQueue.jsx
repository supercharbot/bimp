import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function HoldingQueue() {
  const [queue, setQueue] = useState(null);
  useEffect(() => { apiCall('/api/holding-queue').then(setQueue); }, []);

  if (!queue) return <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />;

  return (
    <motion.div initial="hidden" animate="visible" variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.06 } } }}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Holding Queue</motion.h1>
      {!queue.length && <motion.p variants={fadeUp} style={{ color: 'var(--text-muted)' }}>No pending items. All documents have been matched.</motion.p>}
      {queue.map((item, i) => (
        <motion.div key={i} variants={fadeUp} style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '10px',
          padding: '16px 20px', marginBottom: '10px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{item.document_id}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Arrived: {new Date(item.arrived_at).toLocaleDateString()} · Expires: {new Date(item.expires_at).toLocaleDateString()}
              </div>
            </div>
            <span style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', background: 'rgba(245,158,11,0.1)', color: 'var(--warning)' }}>{item.status}</span>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
