import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ReportData {
  email: string;
  name: string;
  sessions: number;
  gestures: number;
  accuracy: number;
  battery: number;
}

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);

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

      const response = await fetch(`${API_URL}/reports/${email}`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied');
        }
        if (response.status === 404) {
          throw new Error('Report not found');
        }
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setReport(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = async () => {
    if (!keycloak?.token) return;
    window.location.href = `${API_URL}/reports/me/csv`;
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

          <div style={{ margin: '20px 0', display: 'flex', gap: '10px' }}>
            <button
                onClick={getReport}
                disabled={loading}
                style={{ padding: '8px 16px' }}
            >
              {loading ? 'Loading...' : 'Get Report'}
            </button>

            {report && (
                <button onClick={downloadCSV} style={{ padding: '8px 16px' }}>
                  Download CSV
                </button>
            )}
          </div>

          {error && (
              <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#fee', color: '#c00', borderRadius: '4px' }}>
                {error}
              </div>
          )}

          {report && (
              <div style={{ marginTop: '20px' }}>
                <h2>Statistics</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <tbody>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Email:</td>
                    <td style={{ padding: '8px' }}>{report.email}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Name:</td>
                    <td style={{ padding: '8px' }}>{report.name || '-'}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Total sessions:</td>
                    <td style={{ padding: '8px' }}>{report.sessions}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Total gestures:</td>
                    <td style={{ padding: '8px' }}>{report.gestures}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Avg accuracy:</td>
                    <td style={{ padding: '8px' }}>{report.accuracy}%</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #ccc' }}>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>Avg battery:</td>
                    <td style={{ padding: '8px' }}>{report.battery}%</td>
                  </tr>
                  </tbody>
                </table>
              </div>
          )}
        </div>
      </div>
  );
};

export default ReportPage;