import React, { useState } from 'react';
import AIService from '../services/AIService';
import './AIAssistant.css';

const AIAssistant = ({ companyId }) => {
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleOptimize = async () => {
    setError('');
    setResult(null);
    if (!sql || !companyId) return setError('SQL and company must be set');
    try {
      setLoading(true);
      const res = await AIService.optimizeSQL(companyId, sql);
      setResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-assistant">
      <h3>AI Assistant</h3>
      <textarea value={sql} onChange={(e) => setSql(e.target.value)} placeholder="Paste SQL or type a natural language request..." />
      <div className="ai-actions">
        <button onClick={handleOptimize} disabled={loading}>{loading ? 'Processing...' : 'Optimize SQL'}</button>
      </div>

      {error && <div className="ai-error">{error}</div>}

      {result && (
        <div className="ai-result">
          <h4>Suggested SQL</h4>
          <pre>{result.suggested_sql}</pre>
          <h4>Explanation</h4>
          <p>{result.explanation}</p>
          <h4>Original</h4>
          <pre>{result.original}</pre>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;
