import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ReportPageProps {
  userId?: string;
  sessionId?: string | null;
}

const ReportPage: React.FC<ReportPageProps> = ({ userId, sessionId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);

  useEffect(() => {
    console.log('ReportPage mounted with:', { userId, sessionId });
  }, [userId, sessionId]);

  const getReport = async () => {
    console.log('getReport called with:', { userId, sessionId });

    if (!userId) {
      setError('Not authenticated');
      return;
    }

    if (!sessionId) {
      setError('No session ID available. Please refresh the page.');
      console.error('Session ID is null or undefined');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReportUrl(null);
      setReportData(null);

      const headers: HeadersInit = {
        'X-Session-Id': sessionId
      };

      console.log('Making request to:', `${API_URL}/reports/${userId}`);
      console.log('With headers:', headers);

      const response = await fetch(`${API_URL}/reports/${userId}`, {
        headers,
        credentials: 'include'
      });

      console.log('Response status:', response.status);

      if (response.status === 401) {
        setError('Session expired. Please refresh the page and login again.');
        return;
      }

      if (response.status === 403) {
        setError('Access denied. You can only access your own reports.');
        return;
      }

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Report data received:', data);

      setReportData(data);

      if (data.report_url) {
        setReportUrl(data.report_url);
      }

    } catch (err) {
      console.error('Get report error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

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

          {reportData && !reportUrl && (
              <div style={{ marginTop: '20px' }}>
                <h3>Report Data</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <tbody>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Email:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.email}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Name:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.name}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Sessions:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.sessions}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Gestures:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.gestures}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Accuracy:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.accuracy}%</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}><strong>Battery:</strong></td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{reportData.battery}%</td>
                  </tr>
                  </tbody>
                </table>
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