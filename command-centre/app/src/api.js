const API_BASE = '';

export async function apiCall(path, options = {}) {
  const token = localStorage.getItem('bimp_token');
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('bimp_token');
    window.location.reload();
    return null;
  }
  return res.json();
}

export async function googleLogin(credential) {
  const res = await fetch(`${API_BASE}/api/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });
  return res.json();
}
