import React, { useEffect, useState } from 'react';
import ReportPage from './components/ReportPage';

const AUTH_URL = process.env.REACT_APP_AUTH_URL || 'http://localhost:8081';

interface User {
  authenticated: boolean;
  userId?: string;
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await fetch(`${AUTH_URL}/auth/check`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setUser({ authenticated: true, userId: data.userId });
      } else {
        setUser({ authenticated: false });
        startKeycloakLogin();
      }
    } catch (error) {
      setUser({ authenticated: false });
      startKeycloakLogin();
    } finally {
      setLoading(false);
    }
  };

  const startKeycloakLogin = () => {
    const generateCodeVerifier = () => {
      const array = new Uint8Array(32);
      crypto.getRandomValues(array);
      return btoa(String.fromCharCode.apply(null, Array.from(array)))
          .replace(/\+/g, '-')
          .replace(/\//g, '_')
          .replace(/=+$/, '');
    };

    const sha256 = async (plain: string) => {
      const encoder = new TextEncoder();
      const data = encoder.encode(plain);
      const hash = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hash));

      return btoa(String.fromCharCode.apply(null, hashArray))
          .replace(/\+/g, '-')
          .replace(/\//g, '_')
          .replace(/=+$/, '');
    };

    const codeVerifier = generateCodeVerifier();
    localStorage.setItem('pkce_code_verifier', codeVerifier);

    sha256(codeVerifier).then(codeChallenge => {
      const keycloakUrl = process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080';
      const realm = process.env.REACT_APP_KEYCLOAK_REALM || 'reports-realm';
      const clientId = process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'reports-frontend';

      const authUrl = `${keycloakUrl}/realms/${realm}/protocol/openid-connect/auth` +
          `?response_type=code` +
          `&client_id=${clientId}` +
          `&redirect_uri=${encodeURIComponent('http://localhost:3000/callback')}` +
          `&code_challenge=${codeChallenge}` +
          `&code_challenge_method=S256`;

      window.location.href = authUrl;
    });
  };

  const handleCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const codeVerifier = localStorage.getItem('pkce_code_verifier');

    if (code && codeVerifier) {
      localStorage.removeItem('pkce_code_verifier');

      const response = await fetch(`${AUTH_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code, codeVerifier })
      });

      if (response.ok) {
        window.location.href = '/';
      }
    }
  };

  const logout = async () => {
    await fetch(`${AUTH_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    setUser({ authenticated: false });
    window.location.href = '/';
  };

  useEffect(() => {
    if (window.location.pathname === '/callback') {
      handleCallback();
    } else {
      checkSession();
    }
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user?.authenticated) {
    return <div>Redirecting to login...</div>;
  }

  return (
      <div className="App">
        <button onClick={logout}>Logout</button>
        <div>Welcome, {user.userId}</div>
        <ReportPage />
      </div>
  );
};

export default App;