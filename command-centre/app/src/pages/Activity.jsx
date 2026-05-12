import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { apiCall } from '../api';

const fadeUp = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function Activity() {
  const [activity, setActivity] = useState(null);
  useEffect(() => { apiCall('/api/activity').then(setActivity); }, []);

  if (!activity) return <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />;

  return (
    <motion.div initial="hidden" animate="visible" variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}>
      <motion.h1 variants={fadeUp} style={{ fontSize: '1.6rem', marginBottom: '24px' }}>Activity Feed</motion.h1>
      {!activity.length && <motion.p variants={fadeUp} style={{ color: 'var(--text-muted)' }}>No activity yet.</motion.p>}
      <div style={{ position: 'relative', paddingLeft: '24px' }}>
        <div style={{ position: 'absolute', left: '7px', top: 0, bottom: 0, width: '2px', background: 'var(--border)' }} />
        {activity.map((a, i) => (
          <motion.div key={i} variants={fadeUp} style={{ marginBottom: '16px', position: 'relative' }}>
            <div style={{ position: 'absolute', left: '-20px', top: '6px', width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent)', border: '2px solid var(--bg-primary)' }} />
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '10px', padding: '14px 18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{a.type}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(a.timestamp).toLocaleString()}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{a.description}</div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
