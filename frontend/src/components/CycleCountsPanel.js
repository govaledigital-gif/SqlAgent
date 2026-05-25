import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';

const CycleCountsPanel = ({ companyId }) => {
  const [counts, setCounts] = useState([]);
  const [name, setName] = useState('Cycle 1');
  const [warehouseId, setWarehouseId] = useState('');
  const [warehouses, setWarehouses] = useState([]);
  const [lines, setLines] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (companyId) {
      fetchCounts();
      fetchLookups();
    }
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

  const fetchLookups = async () => {
    try {
      const [ws, ps] = await Promise.all([
        InventoryService.listWarehouses(companyId),
        InventoryService.listProducts(companyId),
      ]);
      setWarehouses(ws || []);
      setProducts(ps || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const onWarehouseChange = async (wid) => {
    setWarehouseId(wid);
    try {
      const locs = await InventoryService.listLocations(companyId, wid);
      setLocations(locs || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const addLine = () => {
    setLines([...lines, { product_id: '', location_id: '', counted_quantity: 0 }]);
  };

  const updateLine = (idx, key, value) => {
    const copy = [...lines];
    copy[idx] = { ...copy[idx], [key]: value };
    setLines(copy);
  };

  const removeLine = (idx) => {
    const copy = [...lines];
    copy.splice(idx, 1);
    setLines(copy);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { warehouse_id: warehouseId, name, lines, auto_close: false };
      await InventoryService.createCycleCount(companyId, payload);
      setName('Cycle 1'); setLines([]); setWarehouseId('');
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
        <select value={warehouseId} onChange={(e) => onWarehouseChange(e.target.value)} required>
          <option value="">-- select warehouse --</option>
          {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <button type="button" onClick={addLine}>Add line</button>
        <button type="submit">Create</button>
      </form>

      {lines.map((ln, idx) => (
        <div key={idx} style={{display:'flex', gap:8, marginTop:8}}>
          <select value={ln.product_id} onChange={(e) => updateLine(idx, 'product_id', e.target.value)} required>
            <option value="">-- product --</option>
            {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={ln.location_id} onChange={(e) => updateLine(idx, 'location_id', e.target.value)} required>
            <option value="">-- location --</option>
            {locations.map(l => <option key={l.id} value={l.id}>{l.code || l.name}</option>)}
          </select>
          <input type="number" value={ln.counted_quantity} onChange={(e) => updateLine(idx, 'counted_quantity', Number(e.target.value))} min="0" step="0.0001" />
          <button type="button" onClick={() => removeLine(idx)}>Remove</button>
        </div>
      ))}

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
