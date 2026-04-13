import React, { useState, useEffect, useCallback } from 'react';
import { maintenanceAPI } from '../api/client';
import '../styles/Pages.css';

function Maintenance() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'house',
    interval_days: '',
    estimated_cost: '',
    notes: '',
  });

  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      const type = filter === 'all' ? null : filter;
      const response = await maintenanceAPI.list(type);
      setItems(response.data);
    } catch (err) {
      console.error('Failed to load items:', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadItems();
  }, [filter, loadItems]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await maintenanceAPI.create(formData);
      setFormData({
        name: '',
        description: '',
        type: 'house',
        interval_days: '',
        estimated_cost: '',
        notes: '',
      });
      setShowForm(false);
      loadItems();
    } catch (err) {
      console.error('Failed to create item:', err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure?')) {
      try {
        await maintenanceAPI.delete(id);
        loadItems();
      } catch (err) {
        console.error('Failed to delete item:', err);
      }
    }
  };

  if (loading) return <div className="page loading">Loading...</div>;

  return (
    <div className="page">
      <h1>Maintenance Items</h1>

      <div className="controls">
        <div className="filter-buttons">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={`filter-btn ${filter === 'house' ? 'active' : ''}`}
            onClick={() => setFilter('house')}
          >
            House
          </button>
          <button 
            className={`filter-btn ${filter === 'car' ? 'active' : ''}`}
            onClick={() => setFilter('car')}
          >
            Car
          </button>
          <button 
            className={`filter-btn ${filter === 'lawn' ? 'active' : ''}`}
            onClick={() => setFilter('lawn')}
          >
            Lawn
          </button>
        </div>
        <button className="primary-btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Item'}
        </button>
      </div>

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
            <label>Type *</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            >
              <option value="house">House</option>
              <option value="car">Car</option>
              <option value="lawn">Lawn</option>
            </select>
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Interval (days)</label>
            <input
              type="number"
              value={formData.interval_days}
              onChange={(e) => setFormData({ ...formData, interval_days: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Estimated Cost</label>
            <input
              type="number"
              step="0.01"
              value={formData.estimated_cost}
              onChange={(e) => setFormData({ ...formData, estimated_cost: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>
          <button type="submit" className="primary-btn">Create</button>
        </form>
      )}

      <div className="items-grid">
        {items.map(item => (
          <div key={item.id} className="card item-card">
            <h3>{item.name}</h3>
            <p className="item-type">{item.type}</p>
            {item.description && <p>{item.description}</p>}
            {item.interval_days && <p>Every {item.interval_days} days</p>}
            {item.estimated_cost > 0 && <p>~${item.estimated_cost.toFixed(2)}</p>}
            <button 
              className="delete-btn"
              onClick={() => handleDelete(item.id)}
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      {items.length === 0 && !loading && (
        <p className="empty-message">No maintenance items. Create one to get started!</p>
      )}
    </div>
  );
}

export default Maintenance;
