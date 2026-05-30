import apiClient from '../utils/apiClient';

const AIService = {
  optimizeSQL: async (companyId, sql) => {
    const payload = { company_id: companyId, sql };
    const res = await apiClient.post('/ai/sql-optimize', payload);
    return res.data;
  }
  ,
  nlQuery: async (companyId, question) => {
    const payload = { company_id: companyId, question };
    const res = await apiClient.post('/ai/nl-query', payload);
    return res.data;
  }
  ,
  getUsage: async (companyId) => {
    const res = await apiClient.get(`/ai/usage/${companyId}`);
    return res.data;
  }
  ,
  getCompanyAI: async (companyId) => {
    const res = await apiClient.get(`/companies/${companyId}/ai`);
    return res.data;
  }
  ,
  setCompanyAI: async (companyId, enabled) => {
    const res = await apiClient.post(`/companies/${companyId}/ai`, { enabled });
    return res.data;
  }
  ,
  getCompanyAIConfig: async (companyId) => {
    const res = await apiClient.get(`/companies/${companyId}/ai/config`);
    return res.data;
  }
  ,
  setCompanyAIConfig: async (companyId, payload) => {
    const res = await apiClient.post(`/companies/${companyId}/ai/config`, payload);
    return res.data;
  }
};

export default AIService;
