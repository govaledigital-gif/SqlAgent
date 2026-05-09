import apiClient from '../utils/apiClient';

class SqlService {
  async generateSql(prompt, schema = null) {
    try {
      const response = await apiClient.post('/generate-sql', {
        prompt,
        schema,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to generate SQL');
    }
  }

  async getSchema() {
    try {
      const response = await apiClient.get('/schema');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch schema');
    }
  }

  async getTableSchema(tableName) {
    try {
      const response = await apiClient.get(`/schema/${tableName}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch table schema');
    }
  }

  async listTables() {
    try {
      const response = await apiClient.get('/tables');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch tables');
    }
  }
}

export default new SqlService();
