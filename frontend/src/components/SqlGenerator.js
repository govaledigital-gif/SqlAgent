import React from 'react';
import './SqlGenerator.css';

const SqlGenerator = ({ controller }) => {
  const {
    prompt,
    setPrompt,
    generatedSql,
    tables,
    loading,
    error,
    handleGenerateSql,
  } = controller;

  return (
    <div className="sql-generator-container">
      <header className="header">
        <h1>🚀 SQL Architect - The Data Agent</h1>
        <p>Transform natural language into optimized SQL queries</p>
      </header>

      <div className="content">
        <div className="input-section">
          <div className="tables-info">
            <h3>Available Tables:</h3>
            <ul>
              {tables.map((table) => (
                <li key={table}>{table}</li>
              ))}
            </ul>
          </div>

          <div className="prompt-section">
            <label htmlFor="prompt">Describe your SQL query in natural language:</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Get all users who made purchases in the last 30 days"
              rows="6"
            />
            <button
              onClick={handleGenerateSql}
              disabled={loading}
              className="generate-btn"
            >
              {loading ? 'Generating...' : 'Generate SQL'}
            </button>
          </div>
        </div>

        <div className="output-section">
          {error && <div className="error-message">{error}</div>}
          {generatedSql && (
            <div className="sql-output">
              <h3>Generated SQL:</h3>
              <pre>{generatedSql}</pre>
              <button
                onClick={() => navigator.clipboard.writeText(generatedSql)}
                className="copy-btn"
              >
                Copy SQL
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SqlGenerator;
