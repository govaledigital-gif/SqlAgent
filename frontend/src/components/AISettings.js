import React, { useEffect, useState } from 'react';
import AIService from '../services/AIService';

export default function AISettings({ companyId }) {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    AIService.getCompanyAI(companyId)
      .then((data) => {
        if (!mounted) return;
        setEnabled(Boolean(data.ai_enabled));
      })
      .catch((err) => setError(err?.response?.data || err.message))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, [companyId]);

  const toggle = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await AIService.setCompanyAI(companyId, !enabled);
      setEnabled(Boolean(res.ai_enabled));
    } catch (err) {
      setError(err?.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-settings">
      <h3>AI Settings</h3>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          <label>
            <input type="checkbox" checked={enabled} onChange={toggle} /> Enable AI for this company
          </label>
          {error && <div className="error">{String(error)}</div>}
        </div>
      )}
    </div>
  );
}
