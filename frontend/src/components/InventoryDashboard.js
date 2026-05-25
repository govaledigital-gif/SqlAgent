import React, { useState, useEffect } from 'react';
import InventoryService from '../services/InventoryService';
import ProductsPanel from './ProductsPanel';
import MovementsPanel from './MovementsPanel';
import StockPanel from './StockPanel';
import CycleCountsPanel from './CycleCountsPanel';
import './InventoryDashboard.css';

const InventoryDashboard = () => {
  const [companies, setCompanies] = useState([]);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [whName, setWhName] = useState('');
  const [whCode, setWhCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const data = await InventoryService.listCompanies();
      setCompanies(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { name, code };
      const created = await InventoryService.createCompany(payload);
      setCompanies((s) => [created, ...s]);
      setName('');
      setCode('');
    } catch (err) {
      setError(err.message);
    }
  };

  const selectCompany = async (company) => {
    setSelectedCompany(company);
    try {
      const data = await InventoryService.listWarehouses(company.id);
      setWarehouses(data || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateWarehouse = async (e) => {
    e.preventDefault();
    if (!selectedCompany) return;
    setError('');
    try {
      const payload = { name: whName, code: whCode };
      const created = await InventoryService.createWarehouse(selectedCompany.id, payload);
      setWarehouses((s) => [created, ...s]);
      setWhName('');
      setWhCode('');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="inventory">
      <h2>Inventory Dashboard</h2>
      {error && <div className="error">{error}</div>}

      <section className="companies">
        <h3>Companies</h3>
        <form onSubmit={handleCreateCompany} className="inline-form">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="Code" value={code} onChange={(e) => setCode(e.target.value)} required />
          <button type="submit">Create Company</button>
        </form>

        {loading ? <p>Loading...</p> : (
          <ul className="list">
            {companies.map((c) => (
              <li key={c.id}>
                <button className="link" onClick={() => selectCompany(c)}>{c.name} ({c.code})</button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedCompany && (
        <>
          <section className="warehouses">
            <h3>Warehouses for {selectedCompany.name}</h3>
            <form onSubmit={handleCreateWarehouse} className="inline-form">
              <input placeholder="Warehouse name" value={whName} onChange={(e) => setWhName(e.target.value)} required />
              <input placeholder="Code" value={whCode} onChange={(e) => setWhCode(e.target.value)} required />
              <button type="submit">Create Warehouse</button>
            </form>

            <ul className="list">
              {warehouses.map((w) => (
                <li key={w.id}>{w.name} ({w.code})</li>
              ))}
            </ul>
          </section>

          <section className="products-section">
            <ProductsPanel companyId={selectedCompany.id} />
          </section>

          <section className="movements-section">
            <MovementsPanel companyId={selectedCompany.id} />
          </section>

          <section className="stock-section">
            <StockPanel companyId={selectedCompany.id} />
          </section>

          <section className="cyclecounts-section">
            <CycleCountsPanel companyId={selectedCompany.id} />
          </section>
        </>
      )}
    </div>
  );
};

export default InventoryDashboard;
