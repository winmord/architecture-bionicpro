import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState<string | null>(null);

  const getReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    const email = keycloak.tokenParsed?.email;
    if (!email) {
      setError('Email not found');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReportUrl(null);

      const response = await fetch(`${API_URL}/reports/${email}`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();

      if (data.report_url) {
        setReportUrl(data.report_url);
      } else {
        // Нет данных
        setReportUrl(null);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading...</div>;
  }

  if (!keycloak.authenticated) {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
          <button onClick={() => keycloak.login()} style={{ padding: '10px 20px' }}>
            Login
          </button>
        </div>
    );
  }

  return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', minWidth: '400px' }}>
          <h1>Usage Reports</h1>

          <div style={{ margin: '20px 0' }}>
            <button
                onClick={getReport}
                disabled={loading}
                style={{ padding: '8px 16px' }}
            >
              {loading ? 'Loading...' : 'Get Report'}
            </button>
          </div>

          {error && (
              <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#fee', color: '#c00', borderRadius: '4px' }}>
                {error}
              </div>
          )}

          {reportUrl && (
              <div style={{ marginTop: '20px' }}>
                <p>Report ready:</p>
                <a href={reportUrl} target="_blank" rel="noopener noreferrer">
                  Download CSV
                </a>
              </div>
          )}
        </div>
      </div>
  );
};

export default ReportPage;