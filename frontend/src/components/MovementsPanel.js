import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';

const MovementsPanel = ({ companyId }) => {
  const [products, setProducts] = useState([]);
  const [movementType, setMovementType] = useState('receipt');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [error, setError] = useState('');

  useEffect(() => {
    if (companyId) fetchProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId]);

  const fetchProducts = async () => {
    try {
      const data = await InventoryService.listProducts(companyId);
      setProducts(data || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRecord = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { product_id: productId, quantity: Number(quantity) };
      await InventoryService.recordMovement(companyId, movementType, payload);
      // Could show created info or refresh stock; for now just clear
      setProductId(''); setQuantity('1');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="movements-panel">
      <h4>Record Movement</h4>
      {error && <div className="error">{error}</div>}
      <form className="inline-form" onSubmit={handleRecord}>
        <select value={movementType} onChange={(e) => setMovementType(e.target.value)}>
          <option value="receipt">Receipt</option>
          <option value="dispatch">Dispatch</option>
          <option value="transfer">Transfer</option>
        </select>
        <select value={productId} onChange={(e) => setProductId(e.target.value)} required>
          <option value="">-- select product --</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
          ))}
        </select>
        <input value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" min="0.0001" step="0.0001" />
        <button type="submit">Record</button>
      </form>
    </div>
  );
};

export default MovementsPanel;
