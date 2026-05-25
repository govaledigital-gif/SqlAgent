import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';

const StockPanel = ({ companyId }) => {
  const [stock, setStock] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (companyId) fetchStock();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId]);

  const fetchStock = async () => {
    try {
      const [data, products, warehouses] = await Promise.all([
        InventoryService.listStock(companyId),
        InventoryService.listProducts(companyId),
        InventoryService.listWarehouses(companyId),
      ]);

      const prodMap = new Map((products || []).map(p => [p.id, p]));
      const whMap = new Map((warehouses || []).map(w => [w.id, w]));

      const enriched = (data || []).map(s => ({
        ...s,
        product: prodMap.get(s.product_id)?.name || s.product_id,
        warehouse: whMap.get(s.warehouse_id)?.name || s.warehouse_id,
      }));

      setStock(enriched);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stock-panel">
      <h4>Stock Balances</h4>
      {error && <div className="error">{error}</div>}
      <table style={{width: '100%', borderCollapse: 'collapse'}}>
        <thead>
          <tr>
            <th style={{textAlign:'left', padding:8}}>Product</th>
            <th style={{textAlign:'left', padding:8}}>Warehouse</th>
            <th style={{textAlign:'right', padding:8}}>Quantity</th>
            <th style={{textAlign:'left', padding:8}}>Lot</th>
            <th style={{textAlign:'left', padding:8}}>Serial</th>
          </tr>
        </thead>
        <tbody>
          {stock.map((s) => (
            <tr key={s.id}>
              <td style={{padding:8}}>{s.product_id}</td>
              <td style={{padding:8}}>{s.warehouse_id}</td>
              <td style={{padding:8, textAlign:'right'}}>{s.quantity}</td>
              <td style={{padding:8}}>{s.lot_number}</td>
              <td style={{padding:8}}>{s.serial_number}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StockPanel;
