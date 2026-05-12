import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', label: 'Dashboard', icon: '◫' },
  { to: '/projects', label: 'Projects', icon: '▦' },
  { to: '/search', label: 'Search', icon: '⌕' },
  { to: '/tasks', label: 'Tasks', icon: '☐' },
  { to: '/activity', label: 'Activity', icon: '↻' },
  { to: '/holding-queue', label: 'Holding Queue', icon: '⊟' },
];

const s = {
  sidebar: {
    position: 'fixed', left: 0, top: 0, bottom: 0, width: 'var(--sidebar-width)',
    background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)',
    display: 'flex', flexDirection: 'column', zIndex: 100,
  },
  brand: {
    padding: '24px 24px 20px', borderBottom: '1px solid var(--border)',
    fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '1.3rem', fontWeight: 700,
    letterSpacing: '-0.02em',
  },
  accent: { color: 'var(--accent)' },
  nav: { flex: 1, padding: '12px 0', overflowY: 'auto' },
  link: {
    display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 24px',
    color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem',
    transition: 'all 0.15s ease', borderLeft: '2px solid transparent',
  },
  activeLink: {
    color: 'var(--text-primary)', background: 'var(--accent-glow)',
    borderLeftColor: 'var(--accent)',
  },
  icon: { fontSize: '1.1rem', width: '20px', textAlign: 'center' },
  user: {
    padding: '16px 24px', borderTop: '1px solid var(--border)',
    fontSize: '0.8rem', color: 'var(--text-muted)',
  },
  userName: { color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: '2px' },
  logout: {
    marginTop: '8px', cursor: 'pointer', color: 'var(--text-muted)',
    fontSize: '0.8rem', background: 'none', border: 'none', padding: 0,
  },
};

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <div style={s.sidebar}>
      <div style={s.brand}>B<span style={s.accent}>IMP</span></div>
      <nav style={s.nav}>
        {navItems.map(item => (
          <NavLink key={item.to} to={item.to} end={item.to === '/'}
            style={({ isActive }) => ({ ...s.link, ...(isActive ? s.activeLink : {}) })}
            onMouseEnter={e => { if (!e.currentTarget.classList.contains('active')) e.currentTarget.style.color = 'var(--text-secondary)'; }}
            onMouseLeave={e => { if (!e.currentTarget.classList.contains('active')) e.currentTarget.style.color = ''; }}>
            <span style={s.icon}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div style={s.user}>
        <span style={s.userName}>{user?.name}</span>
        {user?.role}
        <button style={s.logout} onClick={logout}>Sign out</button>
      </div>
    </div>
  );
}
