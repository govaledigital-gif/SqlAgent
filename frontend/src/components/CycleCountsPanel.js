import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';

const CycleCountsPanel = ({ companyId }) => {
  const [counts, setCounts] = useState([]);
  const [name, setName] = useState('Cycle 1');
  const [linesJson, setLinesJson] = useState('[]');
  const [error, setError] = useState('');

  useEffect(() => {
    if (companyId) fetchCounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId]);

  const fetchCounts = async () => {
    try {
      const data = await InventoryService.listCycleCounts(companyId);
      setCounts(data || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { warehouse_id: '', name, lines: JSON.parse(linesJson), auto_close: false };
      await InventoryService.createCycleCount(companyId, payload);
      setName('Cycle 1'); setLinesJson('[]');
      fetchCounts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleClose = async (countId) => {
    try {
      await InventoryService.closeCycleCount(companyId, countId);
      fetchCounts();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="cyclecounts-panel">
      <h4>Cycle Counts</h4>
      {error && <div className="error">{error}</div>}

      <form className="inline-form" onSubmit={handleCreate}>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input placeholder='Lines JSON (e.g. [{"product_id":"id","location_id":"loc","counted_quantity":1}])' value={linesJson} onChange={(e) => setLinesJson(e.target.value)} style={{flex:1}} />
        <button type="submit">Create</button>
      </form>

      <ul className="list">
        {counts.map((c) => (
          <li key={c.id}>
            {c.name} - {c.status} {c.closed_at ? `(closed ${c.closed_at})` : ''}
            {!c.closed_at && <button onClick={() => handleClose(c.id)} style={{marginLeft:8}}>Close</button>}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CycleCountsPanel;
