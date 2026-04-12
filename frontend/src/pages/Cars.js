import React, { useState, useEffect } from 'react';
import { carsAPI } from '../api/client';
import '../styles/Pages.css';

function Cars() {
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    current_miles: '',
    notes: '',
  });

  useEffect(() => {
    loadCars();
  }, []);

  const loadCars = async () => {
    try {
      setLoading(true);
      const response = await carsAPI.list();
      setCars(response.data);
    } catch (err) {
      console.error('Failed to load cars:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await carsAPI.create(formData);
      setFormData({
        name: '',
        make: '',
        model: '',
        year: new Date().getFullYear(),
        current_miles: '',
        notes: '',
      });
      setShowForm(false);
      loadCars();
    } catch (err) {
      console.error('Failed to create car:', err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure?')) {
      try {
        await carsAPI.delete(id);
        loadCars();
      } catch (err) {
        console.error('Failed to delete car:', err);
      }
    }
  };

  if (loading) return <div className="page loading">Loading...</div>;

  return (
    <div className="page">
      <h1>My Vehicles</h1>

      <button className="primary-btn" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : '+ Add Vehicle'}
      </button>

      {showForm && (
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Ford Fiesta 2016 ST"
              required
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Make *</label>
              <input
                type="text"
                value={formData.make}
                onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Model *</label>
              <input
                type="text"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Year *</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label>Current Miles *</label>
            <input
              type="number"
              value={formData.current_miles}
              onChange={(e) => setFormData({ ...formData, current_miles: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>
          <button type="submit" className="primary-btn">Add Vehicle</button>
        </form>
      )}

      <div className="items-grid">
        {cars.map(car => (
          <div key={car.id} className="card car-card">
            <h3>{car.name}</h3>
            <p className="car-year">{car.year} {car.make} {car.model}</p>
            <p className="car-miles">
              <strong>Mileage:</strong> {car.current_miles.toLocaleString()} miles
            </p>
            {car.notes && <p><strong>Notes:</strong> {car.notes}</p>}
            <button 
              className="delete-btn"
              onClick={() => handleDelete(car.id)}
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      {cars.length === 0 && !loading && (
        <p className="empty-message">No vehicles added yet. Add your first vehicle to get started!</p>
      )}
    </div>
  );
}

export default Cars;
