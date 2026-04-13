import React, { useState, useEffect, useCallback } from 'react';
import { agentAPI } from '../api/client';
import '../styles/Pages.css';

function Admin() {
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const loadExecutions = useCallback(async () => {
    try {
      setLoading(true);
      const status = filter === 'all' ? null : filter;
      const response = await agentAPI.listExecutions(null, status);
      setExecutions(response.data);
    } catch (err) {
      console.error('Failed to load executions:', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadExecutions();
    // Refresh every 10 seconds
    const interval = setInterval(loadExecutions, 10000);
    return () => clearInterval(interval);
  }, [filter, loadExecutions]);

  if (loading) return <div className="page loading">Loading...</div>;

  return (
    <div className="page admin-page">
      <h1>Admin Panel</h1>

      <div className="admin-section">
        <h2>System Status</h2>
        <div className="status-cards">
          <div className="status-card">
            <h3>Total Agent Executions</h3>
            <p className="status-value">{executions.length}</p>
          </div>
          <div className="status-card">
            <h3>Pending</h3>
            <p className="status-value">
              {executions.filter(e => e.status === 'pending').length}
            </p>
          </div>
          <div className="status-card">
            <h3>Running</h3>
            <p className="status-value">
              {executions.filter(e => e.status === 'running').length}
            </p>
          </div>
          <div className="status-card">
            <h3>Completed</h3>
            <p className="status-value">
              {executions.filter(e => e.status === 'completed').length}
            </p>
          </div>
        </div>
      </div>

      <div className="admin-section">
        <h2>Agent Executions</h2>
        
        <div className="filter-buttons">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending
          </button>
          <button 
            className={`filter-btn ${filter === 'running' ? 'active' : ''}`}
            onClick={() => setFilter('running')}
          >
            Running
          </button>
          <button 
            className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            Completed
          </button>
          <button 
            className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
            onClick={() => setFilter('failed')}
          >
            Failed
          </button>
        </div>

        <div className="executions-table">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Agent Type</th>
                <th>Status</th>
                <th>Created</th>
                <th>Completed</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {executions.map(execution => (
                <tr key={execution.id}>
                  <td>{execution.id}</td>
                  <td>{execution.agent_type}</td>
                  <td><span className={`status-badge ${execution.status}`}>{execution.status}</span></td>
                  <td>{new Date(execution.created_at).toLocaleString()}</td>
                  <td>{execution.completed_at ? new Date(execution.completed_at).toLocaleString() : '-'}</td>
                  <td>{execution.error_message || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {executions.length === 0 && !loading && (
          <p className="empty-message">No agent executions found.</p>
        )}
      </div>
    </div>
  );
}

export default Admin;
