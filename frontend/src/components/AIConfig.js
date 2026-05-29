import React, { useEffect, useState } from 'react';
import AIService from '../services/AIService';

export default function AIConfig({ companyId }) {
  const [config, setConfig] = useState({ ai_api_key: '', ai_quota_per_hour: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    AIService.getCompanyAIConfig(companyId)
      .then((data) => {
        if (!mounted) return;
        setConfig({ ai_api_key: data.ai_api_key || '', ai_quota_per_hour: data.ai_quota_per_hour || 0 });
      })
      .catch((err) => setError(err?.response?.data || err.message))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, [companyId]);

  const save = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await AIService.setCompanyAIConfig(companyId, config);
      setConfig({ ai_api_key: res.ai_api_key || '', ai_quota_per_hour: res.ai_quota_per_hour || 0 });
    } catch (err) {
      setError(err?.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-config">
      <h3>AI Configuration (owner only)</h3>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          <div>
            <label>AI API Key</label>
            <input type="text" value={config.ai_api_key} onChange={(e) => setConfig({ ...config, ai_api_key: e.target.value })} />
          </div>
          <div>
            <label>Quota per hour (0 = use global)</label>
            <input type="number" value={config.ai_quota_per_hour} onChange={(e) => setConfig({ ...config, ai_quota_per_hour: parseInt(e.target.value || '0') })} />
          </div>
          <button onClick={save} disabled={loading}>Save</button>
          {error && <div className="error">{String(error)}</div>}
        </div>
      )}
    </div>
  );
}
