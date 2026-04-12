import React, { useState, useEffect } from 'react';
import { budgetsAPI } from '../api/client';
import '../styles/Pages.css';

function Budgets() {
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: 'maintenance',
    limit: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    notes: '',
  });

  useEffect(() => {
    loadBudgets();
  }, []);

  const loadBudgets = async () => {
    try {
      setLoading(true);
      const response = await budgetsAPI.list();
      setBudgets(response.data);
    } catch (err) {
      console.error('Failed to load budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await budgetsAPI.create(formData);
      setFormData({
        name: '',
        category: 'maintenance',
        limit: '',
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        notes: '',
      });
      setShowForm(false);
      loadBudgets();
    } catch (err) {
      console.error('Failed to create budget:', err);
    }
  };

  if (loading) return <div className="page loading">Loading...</div>;

  const months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December'];

  return (
    <div className="page">
      <h1>Budgets</h1>

      <button className="primary-btn" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : '+ New Budget'}
      </button>

      {showForm && (
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Category *</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            >
              <option value="maintenance">Maintenance</option>
              <option value="lawn">Lawn</option>
              <option value="personal">Personal</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Limit *</label>
            <input
              type="number"
              step="0.01"
              value={formData.limit}
              onChange={(e) => setFormData({ ...formData, limit: e.target.value })}
              required
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Month *</label>
              <select
                value={formData.month}
                onChange={(e) => setFormData({ ...formData, month: parseInt(e.target.value) })}
              >
                {months.map((m, idx) => (
                  <option key={idx} value={idx + 1}>{m}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Year *</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
              />
            </div>
          </div>
          <button type="submit" className="primary-btn">Create Budget</button>
        </form>
      )}

      <div className="budgets-grid">
        {budgets.map(budget => {
          const percentage = budget.limit > 0 ? (budget.spent / budget.limit) * 100 : 0;
          const remaining = budget.limit - budget.spent;
          
          return (
            <div key={budget.id} className="card budget-card">
              <h3>{budget.name}</h3>
              <p className="budget-category">{budget.category}</p>
              <p className="budget-month">
                {months[budget.month - 1]} {budget.year}
              </p>
              
              <div className="budget-bar">
                <div 
                  className={`budget-progress ${percentage > 100 ? 'over-budget' : ''}`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                ></div>
              </div>
              
              <div className="budget-info">
                <p>Spent: <strong>${budget.spent.toFixed(2)}</strong></p>
                <p>Limit: <strong>${budget.limit.toFixed(2)}</strong></p>
                <p className={remaining >= 0 ? 'positive' : 'negative'}>
                  Remaining: <strong>${remaining.toFixed(2)}</strong>
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {budgets.length === 0 && !loading && (
        <p className="empty-message">No budgets created yet. Create one to get started!</p>
      )}
    </div>
  );
}

export default Budgets;
