import React, { useState } from 'react';
import AIService from '../services/AIService';
import './AIAssistant.css';

const NLAssistant = ({ companyId }) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [usage, setUsage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await AIService.nlQuery(companyId, question);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsage = async () => {
    try {
      const u = await AIService.getUsage(companyId);
      setUsage(u);
    } catch (err) {
      // ignore
    }
  };

  return (
    <div className="ai-assistant">
      <h4>Asistente en lenguaje natural</h4>
      <form onSubmit={handleSubmit} className="ai-form">
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Pregunta (ej: ¿Qué productos están por debajo del punto de reorden?)" required />
        <button type="submit" disabled={loading}>{loading ? 'Procesando...' : 'Preguntar'}</button>
      </form>
      {error && <div className="error">{error}</div>}
      <div style={{marginTop: '8px'}}>
        <button onClick={fetchUsage} className="small">Mostrar uso AI</button>
        {usage && (
          <div style={{marginTop: '8px'}}>
            <strong>Uso:</strong> {usage.tokens || 0} tokens — {usage.cost_cents ? (usage.cost_cents/100).toFixed(2) : '0.00'} USD
          </div>
        )}
      </div>
      {result && (
        <div className="ai-result">
          <p><strong>SQL generado:</strong> <code>{result.sql}</code></p>
          <p><strong>Explicación:</strong> {result.explanation} {result.confidence ? `(confidence: ${result.confidence})` : ''}</p>
          {result.results && result.results.length > 0 && (
            <table className="ai-table">
              <thead>
                <tr>{Object.keys(result.results[0]).map((k) => <th key={k}>{k}</th>)}</tr>
              </thead>
              <tbody>
                {result.results.map((row, idx) => (
                  <tr key={idx}>{Object.values(row).map((v, i) => <td key={i}>{String(v)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default NLAssistant;
