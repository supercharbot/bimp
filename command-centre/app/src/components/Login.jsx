import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { useEffect } from 'react';

const styles = {
  page: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    minHeight: '100vh', flexDirection: 'column', gap: '32px',
    background: 'radial-gradient(ellipse at 50% 0%, rgba(59,130,246,0.08) 0%, var(--bg-primary) 60%)',
  },
  logo: {
    fontSize: '3rem', fontWeight: 700, letterSpacing: '-0.03em',
    fontFamily: 'Plus Jakarta Sans, sans-serif', color: 'var(--text-primary)',
  },
  accent: { color: 'var(--accent)' },
  sub: { color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '-16px', letterSpacing: '0.04em' },
  card: {
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: '16px', padding: '40px', display: 'flex',
    flexDirection: 'column', alignItems: 'center', gap: '24px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
  },
  footer: { color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '8px' },
};

export default function Login() {
  const { login } = useAuth();

  useEffect(() => {
    window.handleGoogleLogin = async (response) => {
      const success = await login(response.credential);
      if (!success) alert('Login failed. Ensure your account is registered.');
    };
  }, [login]);

  return (
    <motion.div style={styles.page} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
      <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2, duration: 0.5 }}>
        <div style={styles.logo}>B<span style={styles.accent}>IMP</span></div>
      </motion.div>
      <motion.div style={styles.sub} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
        Business Intelligence & Monitoring Platform
      </motion.div>
      <motion.div style={styles.card} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5, duration: 0.5 }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Sign in with your Develo account</div>
        <div id="g_id_onload"
          data-client_id="1032037096655-ih9ucbaljg71n1qmt5crcnsgpl193cei.apps.googleusercontent.com"
          data-callback="handleGoogleLogin"
          data-auto_prompt="false" />
        <div className="g_id_signin" data-type="standard" data-size="large" data-theme="filled_black" data-text="sign_in_with" data-shape="pill" />
      </motion.div>
      <div style={styles.footer}>Develo Pty Ltd</div>
    </motion.div>
  );
}
