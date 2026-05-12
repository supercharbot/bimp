import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { useChat } from './context/ChatContext';
import Login from './components/Login';
import Sidebar from './components/Sidebar';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Tasks from './pages/Tasks';
import Activity from './pages/Activity';
import HoldingQueue from './pages/HoldingQueue';

function Layout({ children }) {
  const location = useLocation();
  const { chatActive } = useChat();
  const isChat = location.pathname === '/';
  const collapsed = isChat && chatActive;
  const margin = collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-expanded)';

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main key={location.pathname} className="fade-in" style={{
        marginLeft: margin, flex: 1,
        padding: isChat ? '0' : '28px 36px',
        transition: 'margin-left 200ms ease',
      }}>
        {children}
      </main>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)' }}>
      <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text-muted)' }}>BIMP</div>
    </div>
  );

  if (!user) return <Login />;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/activity" element={<Activity />} />
        <Route path="/holding-queue" element={<HoldingQueue />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  );
}
