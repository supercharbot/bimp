import { useAuth } from '../context/AuthContext';
import { useEffect } from 'react';

export default function Login() {
  const { login } = useAuth();

  useEffect(() => {
    const wrapper = document.getElementById('google-login-wrapper');
    const btn = document.getElementById('google-btn');
    if (wrapper) wrapper.style.display = 'flex';

    const init = () => {
      if (!window.google?.accounts?.id || !btn) return false;
      window.google.accounts.id.initialize({
        client_id: '1032037096655-ih9ucbaljg71n1qmt5crcnsgpl193cei.apps.googleusercontent.com',
        callback: (r) => login(r.credential),
      });
      window.google.accounts.id.renderButton(btn, {
        theme: 'filled_black', size: 'large', shape: 'pill', text: 'signin_with', width: 280,
      });
      return true;
    };

    if (!init()) {
      const iv = setInterval(() => { if (init()) clearInterval(iv); }, 100);
      return () => { clearInterval(iv); if (wrapper) wrapper.style.display = 'none'; };
    }

    return () => { if (wrapper) wrapper.style.display = 'none'; };
  }, [login]);

  return null;
}
