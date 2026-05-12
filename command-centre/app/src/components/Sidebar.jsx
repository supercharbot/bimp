import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';

const nav = [
  { to: '/', label: 'New chat', icon: '＋' },
  { to: '/dashboard', label: 'Dashboard', icon: '◫' },
  { to: '/projects', label: 'Projects', icon: '▤' },
  { to: '/tasks', label: 'Tasks', icon: '☑' },
  { to: '/activity', label: 'Activity', icon: '↻' },
  { to: '/holding-queue', label: 'Queue', icon: '☷' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { chatActive } = useChat();
  const location = useLocation();
  const isChat = location.pathname === '/';
  const collapsed = isChat && chatActive;
  const w = collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-expanded)';
  const initial = (user?.name || user?.email || 'U')[0].toUpperCase();

  return (
    <div style={{
      position: 'fixed', left: 0, top: 0, bottom: 0, width: w,
      background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', zIndex: 100,
      transition: 'width 200ms ease', overflow: 'hidden',
    }}>
      <div style={{
        padding: collapsed ? '20px 0 16px' : '20px 22px 16px',
        borderBottom: '1px solid var(--border)',
        fontFamily: 'var(--font-heading)', fontSize: collapsed ? '1.2rem' : '1.15rem',
        fontWeight: 700, letterSpacing: '-0.03em',
        textAlign: collapsed ? 'center' : 'left', whiteSpace: 'nowrap',
      }}>
        {collapsed ? 'B' : 'BIMP'}
      </div>

      <nav style={{ flex: 1, padding: '10px 0' }}>
        {nav.map(item => (
          <NavLink key={item.to} to={item.to} end={item.to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: '14px',
              padding: collapsed ? '14px 0' : '13px 22px',
              justifyContent: collapsed ? 'center' : 'flex-start',
              fontSize: collapsed ? '1.4rem' : '0.95rem',
              color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
              background: isActive ? 'var(--accent-soft)' : 'transparent',
              borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all var(--transition)', whiteSpace: 'nowrap',
            })}>
            <span style={{ width: '24px', textAlign: 'center', flexShrink: 0 }}>{item.icon}</span>
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div style={{
        padding: collapsed ? '16px 0' : '16px 22px',
        borderTop: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: '12px',
        justifyContent: collapsed ? 'center' : 'flex-start',
      }}>
        <div style={{
          width: '36px', height: '36px', borderRadius: '50%',
          background: 'var(--accent)', color: '#1a1a1a',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.9rem', fontWeight: 700, flexShrink: 0,
        }}>
          {initial}
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{user?.name}</div>
            <button onClick={logout} style={{
              background: 'none', border: 'none', padding: 0, color: 'var(--text-muted)',
              fontSize: '0.75rem', cursor: 'pointer',
            }}>Sign out</button>
          </div>
        )}
      </div>
    </div>
  );
}
