import apiClient from '../utils/apiClient';

class InventoryService {
  async listCompanies() {
    try {
      const res = await apiClient.get('/companies');
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to list companies');
    }
  }

  async createCompany(payload) {
    try {
      const res = await apiClient.post('/companies', payload);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to create company');
    }
  }

  async listWarehouses(companyId) {
    try {
      const res = await apiClient.get(`/companies/${companyId}/warehouses`);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to list warehouses');
    }
  }

  async createWarehouse(companyId, payload) {
    try {
      const res = await apiClient.post(`/companies/${companyId}/warehouses`, payload);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to create warehouse');
    }
  }

  async listProducts(companyId) {
    try {
      const res = await apiClient.get(`/companies/${companyId}/products`);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to list products');
    }
  }

  async createProduct(companyId, payload) {
    try {
      const res = await apiClient.post(`/companies/${companyId}/products`, payload);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to create product');
    }
  }

  async recordMovement(companyId, movementType, payload) {
    try {
      const path = movementType === 'receipt' ? 'receipts' : (movementType === 'dispatch' ? 'shipments' : 'transfers');
      const res = await apiClient.post(`/companies/${companyId}/movements/${path}`, payload);
      return res.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to record movement');
    }
  }
}

const inventoryService = new InventoryService();
export default inventoryService;
