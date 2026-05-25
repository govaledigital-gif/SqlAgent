import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';

const ProductsPanel = ({ companyId }) => {
  const [products, setProducts] = useState([]);
  const [sku, setSku] = useState('');
  const [name, setName] = useState('');
  const [uom, setUom] = useState('unit');
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

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { sku, name, unit_of_measure: uom };
      const created = await InventoryService.createProduct(companyId, payload);
      setProducts((s) => [created, ...s]);
      setSku(''); setName(''); setUom('unit');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="products-panel">
      <h4>Products</h4>
      {error && <div className="error">{error}</div>}
      <form className="inline-form" onSubmit={handleCreate}>
        <input placeholder="SKU" value={sku} onChange={(e) => setSku(e.target.value)} required />
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input placeholder="UoM" value={uom} onChange={(e) => setUom(e.target.value)} required />
        <button type="submit">Create</button>
      </form>

      <ul className="list">
        {products.map((p) => (
          <li key={p.id}>{p.name} — {p.sku} ({p.unit_of_measure})</li>
        ))}
      </ul>
    </div>
  );
};

export default ProductsPanel;
