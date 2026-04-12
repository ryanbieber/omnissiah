import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Maintenance endpoints
export const maintenanceAPI = {
  list: (type, skip = 0, limit = 100) => 
    api.get('/maintenance', { params: { maintenance_type: type, skip, limit } }),
  get: (id) => api.get(`/maintenance/${id}`),
  create: (data) => api.post('/maintenance', data),
  update: (id, data) => api.put(`/maintenance/${id}`, data),
  delete: (id) => api.delete(`/maintenance/${id}`),
};

// Cars endpoints
export const carsAPI = {
  list: (skip = 0, limit = 100) => api.get('/cars', { params: { skip, limit } }),
  get: (id) => api.get(`/cars/${id}`),
  create: (data) => api.post('/cars', data),
  update: (id, data) => api.put(`/cars/${id}`, data),
  delete: (id) => api.delete(`/cars/${id}`),
};

// Tasks endpoints
export const tasksAPI = {
  list: (status, skip = 0, limit = 100) => 
    api.get('/tasks', { params: { status, skip, limit } }),
  get: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
};

// Budgets endpoints
export const budgetsAPI = {
  list: (category, month, year, skip = 0, limit = 100) => 
    api.get('/budgets', { params: { category, month, year, skip, limit } }),
  get: (id) => api.get(`/budgets/${id}`),
  create: (data) => api.post('/budgets', data),
  update: (id, data) => api.put(`/budgets/${id}`, data),
  delete: (id) => api.delete(`/budgets/${id}`),
  addExpense: (budgetId, data) => api.post(`/budgets/${budgetId}/expenses`, data),
  getExpenses: (budgetId) => api.get(`/budgets/${budgetId}/expenses`),
};

// Agent endpoints
export const agentAPI = {
  execute: (data) => api.post('/agent/execute', data),
  getExecution: (id) => api.get(`/agent/${id}`),
  listExecutions: (agentType, status, skip = 0, limit = 100) =>
    api.get('/agent', { params: { agent_type: agentType, status, skip, limit } }),
  updateExecution: (id, data) => api.put(`/agent/${id}`, data),
};

export default api;
