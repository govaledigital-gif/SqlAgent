import { useState, useEffect } from 'react';
import SqlService from '../services/SqlService';

const SqlController = () => {
  const [prompt, setPrompt] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [schema, setSchema] = useState('');
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSchema();
    fetchTables();
  }, []);

  const fetchSchema = async () => {
    try {
      const data = await SqlService.getSchema();
      setSchema(data.schema);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchTables = async () => {
    try {
      const data = await SqlService.listTables();
      setTables(data.tables);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleGenerateSql = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await SqlService.generateSql(prompt, schema);
      setGeneratedSql(data.query);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    prompt,
    setPrompt,
    generatedSql,
    schema,
    tables,
    loading,
    error,
    handleGenerateSql,
  };
};

export default SqlController;
