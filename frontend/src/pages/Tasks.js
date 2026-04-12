import React, { useState, useEffect } from 'react';
import { tasksAPI } from '../api/client';
import '../styles/Pages.css';

function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await tasksAPI.list(filter === 'all' ? null : filter);
      setTasks(response.data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await tasksAPI.update(taskId, { 
        status: newStatus,
        last_completed: newStatus === 'completed' ? new Date().toISOString() : null
      });
      loadTasks();
    } catch (err) {
      console.error('Failed to update task:', err);
    }
  };

  if (loading) return <div className="page loading">Loading...</div>;

  return (
    <div className="page">
      <h1>Maintenance Tasks</h1>

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
          className={`filter-btn ${filter === 'in-progress' ? 'active' : ''}`}
          onClick={() => setFilter('in-progress')}
        >
          In Progress
        </button>
        <button 
          className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          Completed
        </button>
      </div>

      <div className="tasks-list">
        {tasks.map(task => (
          <div key={task.id} className="task-card">
            <div className="task-header">
              <h3>{task.maintenance_item?.name || 'Task'}</h3>
              <span className={`status ${task.status}`}>
                {task.status.replace('-', ' ').toUpperCase()}
              </span>
            </div>
            <p className="due-date">
              Due: {new Date(task.next_due).toLocaleDateString()}
            </p>
            {task.last_completed && (
              <p className="completed-date">
                Completed: {new Date(task.last_completed).toLocaleDateString()}
              </p>
            )}
            <div className="task-actions">
              <button 
                className="btn-pending"
                onClick={() => handleStatusChange(task.id, 'pending')}
              >
                Pending
              </button>
              <button 
                className="btn-progress"
                onClick={() => handleStatusChange(task.id, 'in-progress')}
              >
                In Progress
              </button>
              <button 
                className="btn-completed"
                onClick={() => handleStatusChange(task.id, 'completed')}
              >
                Completed
              </button>
            </div>
          </div>
        ))}
      </div>

      {tasks.length === 0 && !loading && (
        <p className="empty-message">No tasks found.</p>
      )}
    </div>
  );
}

export default Tasks;
