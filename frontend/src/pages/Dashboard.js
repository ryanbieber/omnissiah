import React, { useState, useEffect } from 'react';
import { maintenanceAPI, tasksAPI, budgetsAPI, carsAPI } from '../api/client';
import '../styles/Dashboard.css';

function Dashboard() {
  const [pendingTasks, setPendingTasks] = useState(0);
  const [completedTasks, setCompletedTasks] = useState(0);
  const [totalBudget, setTotalBudget] = useState(0);
  const [spentBudget, setSpentBudget] = useState(0);
  const [upcomingItems, setUpcomingItems] = useState([]);
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load tasks
      const tasksRes = await tasksAPI.list();
      const pendingCount = tasksRes.data.filter(t => t.status === 'pending').length;
      const completedCount = tasksRes.data.filter(t => t.status === 'completed').length;
      setPendingTasks(pendingCount);
      setCompletedTasks(completedCount);
      setUpcomingItems(tasksRes.data.slice(0, 5));

      // Load cars
      const carsRes = await carsAPI.list();
      setCars(carsRes.data);

      // Load budgets
      const budgetsRes = await budgetsAPI.list();
      let total = 0;
      let spent = 0;
      budgetsRes.data.forEach(budget => {
        total += budget.limit;
        spent += budget.spent;
      });
      setTotalBudget(total);
      setSpentBudget(spent);

      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="dashboard loading">Loading...</div>;

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      {error && <div className="error-message">{error}</div>}

      <div className="dashboard-grid">
        <div className="card stats-card">
          <h3>Tasks Overview</h3>
          <div className="stats">
            <div className="stat">
              <div className="stat-value">{pendingTasks}</div>
              <div className="stat-label">Pending</div>
            </div>
            <div className="stat">
              <div className="stat-value">{completedTasks}</div>
              <div className="stat-label">Completed</div>
            </div>
          </div>
        </div>

        <div className="card stats-card">
          <h3>Budget Status</h3>
          <div className="stats">
            <div className="stat">
              <div className="stat-value">${spentBudget.toFixed(2)}</div>
              <div className="stat-label">Spent</div>
            </div>
            <div className="stat">
              <div className="stat-value">${totalBudget.toFixed(2)}</div>
              <div className="stat-label">Total Budget</div>
            </div>
          </div>
          {totalBudget > 0 && (
            <div className="budget-bar">
              <div 
                className="budget-progress" 
                style={{ width: `${Math.min((spentBudget / totalBudget) * 100, 100)}%` }}
              ></div>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Your Vehicles</h3>
          {cars.length > 0 ? (
            <ul className="car-list">
              {cars.map(car => (
                <li key={car.id}>
                  <strong>{car.name}</strong>
                  <span className="car-miles">{car.current_miles.toLocaleString()} miles</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No cars added yet. <a href="/cars">Add a car</a></p>
          )}
        </div>

        <div className="card">
          <h3>Upcoming Maintenance</h3>
          {upcomingItems.length > 0 ? (
            <ul className="maintenance-list">
              {upcomingItems.map(item => (
                <li key={item.id}>
                  <strong>{item.maintenance_item?.name || 'Maintenance Task'}</strong>
                  <span className="due-date">
                    Due: {new Date(item.next_due).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No upcoming maintenance. Great job! 🎉</p>
          )}
        </div>
      </div>

      <button className="refresh-btn" onClick={loadDashboardData}>
        Refresh Data
      </button>
    </div>
  );
}

export default Dashboard;
