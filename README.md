# Omnissiah - Home Assistant Maintenance Management

A comprehensive home maintenance tracking application with FastAPI backend, React frontend, PostgreSQL database, and multi-agent support. Manage house, car, and lawn maintenance all in one place with Telegram notifications.

## Features

- 🏠 **Maintenance Tracking:** House, car, and lawn maintenance schedules
- 🚗 **Vehicle Management:** Track multiple vehicles with maintenance histories
- 📋 **Task Management:** Create, update, and track maintenance tasks
- 💰 **Budget Management:** Set and monitor maintenance budgets
- 🤖 **Multi-Agent System:** 
  - Chainlit chat interface for natural language interactions
  - **LangChain DeepAgents** for intelligent reasoning and planning
  - PostgreSQL checkpointer for persistent memory
  - Telegram orchestration agent for notifications
- 📱 **Telegram Integration:** Receive alerts and update tasks via Telegram (long polling mode)
- 🎨 **React Dashboard:** Modern, responsive UI with real-time updates
- ⚙️ **Admin Panel:** System monitoring and agent execution logs
- 🐳 **Docker Compose:** Easy deployment with all services containerized

## Tech Stack

**Backend:**
- FastAPI 0.104+
- SQLAlchemy 2.0+ (ORM)
- PostgreSQL 15
- **LangChain DeepAgents** (AI reasoning)
- LangGraph (orchestration)
- Chainlit 1.0+ (Chat UI)
- python-telegram-bot 20.0+ (Telegram integration)
- Uvicorn (ASGI Server)

**Frontend:**
- React 18.2+
- React Router 6.18+
- Axios 1.6+ (API client)
- CSS3 (responsive design)

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL (database + LangGraph checkpoints)
- Uvicorn (FastAPI server)
- Node.js 18 (React development)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd omnissiah
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL (port 5432)
   - FastAPI backend (port 8000)
   - React frontend (port 3000)

4. **Access the application**
   - Dashboard: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Chainlit Chat: http://localhost:8000/chainlit (requires route setup)

5. **Import car maintenance schedules**
   ```bash
   # Edit data/car_schedules.json with your vehicles
   # Then use the import endpoint or admin panel
   curl -X POST http://localhost:8000/api/maintenance/import \
     -H "Content-Type: application/json" \
     -d @data/car_schedules.json
   ```

## Project Structure

```
omnissiah/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── routes/                   # API endpoints
│   │   ├── maintenance.py        # Maintenance items CRUD
│   │   ├── cars.py              # Vehicle management
│   │   ├── tasks.py             # Task management
│   │   ├── budgets.py           # Budget tracking
│   │   └── agent.py             # Agent orchestration
│   ├── chainlit.py              # Chainlit chat integration
│   ├── telegram/                # Telegram bot handlers
│   │   └── handler.py           # Webhook handler
│   └── utils/                   # Utilities
│       └── car_schedule_loader.py
│
├── frontend/                     # React application
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── api/                 # API client
│   │   ├── styles/              # CSS files
│   │   ├── App.js               # Root component
│   │   └── index.js             # Entry point
│   ├── public/
│   └── Dockerfile
│
├── database/                     # Database layer
│   ├── models.py                # SQLAlchemy models
│   ├── database.py              # Connection & session
│   └── migrations/              # Alembic migrations (future)
│
├── config/                       # Configuration
│   └── settings.py              # Environment settings
│
├── agents/                       # Agent implementations
│   ├── deep_agent.py            # Reasoning agent (future)
│   └── telegram_orchestrator.py  # Notification agent (future)
│
├── data/                         # Data files
│   └── car_schedules.json        # Example car maintenance schedules
│
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # FastAPI Docker image
├── pyproject.toml              # Python dependencies
├── agents.md                    # Agent architecture documentation
├── .env.example                # Environment variables template
└── README.md                    # This file
```

## API Endpoints

### Maintenance Items
```
GET    /api/maintenance              # List all items
GET    /api/maintenance/{id}         # Get item details
POST   /api/maintenance              # Create new item
PUT    /api/maintenance/{id}         # Update item
DELETE /api/maintenance/{id}         # Delete item
```

### Vehicles
```
GET    /api/cars                     # List all vehicles
GET    /api/cars/{id}                # Get vehicle details
POST   /api/cars                     # Add new vehicle
PUT    /api/cars/{id}                # Update vehicle
DELETE /api/cars/{id}                # Delete vehicle
```

### Tasks
```
GET    /api/tasks                    # List tasks (filterable by status)
GET    /api/tasks/{id}               # Get task details
POST   /api/tasks                    # Create new task
PUT    /api/tasks/{id}               # Update task status
DELETE /api/tasks/{id}               # Delete task
```

### Budgets
```
GET    /api/budgets                  # List budgets
GET    /api/budgets/{id}             # Get budget details
POST   /api/budgets                  # Create budget
PUT    /api/budgets/{id}             # Update budget
DELETE /api/budgets/{id}             # Delete budget
POST   /api/budgets/{id}/expenses    # Add expense
GET    /api/budgets/{id}/expenses    # Get expenses
```

### Agent Orchestration
```
POST   /api/agent/execute            # Execute agent task
GET    /api/agent/{id}               # Get execution status
GET    /api/agent                    # List executions
PUT    /api/agent/{id}               # Update execution results
```

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://omnissiah:omnissiah@postgres:5432/omnissiah

# FastAPI
FASTAPI_ENV=development
FASTAPI_DEBUG=true

# Telegram (set after creating bot)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
REACT_PORT=3000

# Frontend API URL
REACT_APP_API_URL=http://localhost:8000
```

## Setting Up Telegram Bot

1. Create a bot with [BotFather](https://t.me/botfather) on Telegram
2. Get your bot token
3. Set up webhook (if deploying to server):
   ```bash
   curl https://api.telegram.org/bot{BOT_TOKEN}/setWebhook \
     -d url="https://your-domain.com/api/telegram/webhook" \
     -d secret_token="your_webhook_secret"
   ```
4. Update `.env` with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET`

## Car Schedule JSON Format

```json
{
  "cars": [
    {
      "name": "Ford Fiesta 2016 ST",
      "make": "Ford",
      "model": "Fiesta",
      "year": 2016,
      "current_miles": 84000,
      "maintenance_schedule": [
        {
          "name": "Oil Change",
          "description": "Engine oil and filter replacement",
          "interval_miles": 5000,
          "interval_days": 365,
          "estimated_cost": 50.0,
          "notes": "Synthetic oil"
        }
      ]
    }
  ]
}
```

See [data/car_schedules.json](data/car_schedules.json) for complete examples.

## Database Models

### MaintenanceItem
- Tracks maintenance tasks (house, car, lawn)
- Links to Car if vehicle-specific
- Stores interval and cost information

### MaintenanceTask
- Individual task instances
- Tracks status (pending, in-progress, completed)
- Records due dates and completion dates

### Car
- Vehicle information (make, model, year)
- Current mileage
- Associated maintenance items

### Budget
- Monthly budget allocation by category
- Tracks spending against limit
- Linked to expenses

### TaskHistory
- Audit trail for task updates
- Records status changes and completion dates

### AgentExecution
- Logs all agent activities
- Tracks execution status and results
- Used for debugging and monitoring

## Development

### Running Locally (without Docker)

1. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Set up PostgreSQL** (or use Docker just for DB)
   ```bash
   docker run -d \
     -e POSTGRES_USER=omnissiah \
     -e POSTGRES_PASSWORD=omnissiah \
     -e POSTGRES_DB=omnissiah \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Run FastAPI**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Run React** (in another terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Running Tests

```bash
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/ -cov  # Coverage report
```

## Agent Architecture

See [agents.md](agents.md) for detailed documentation on:
- Chainlit Chat Agent
- Deep Reasoning Agent
- Telegram Orchestration Agent
- Agent communication flows
- Integration examples

## Future Enhancements

- [ ] LLM integration (GPT-4, Claude) for intelligent chat
- [ ] Machine learning for maintenance prediction
- [ ] Photo evidence submission via Telegram
- [ ] Multi-user support with permissions
- [ ] Third-party API integrations (weather, fuel prices, etc.)
- [ ] Mobile app (native iOS/Android)
- [ ] Calendar view for maintenance schedule
- [ ] Maintenance history analytics
- [ ] Cost trending and predictions
- [ ] Automated reminders based on usage patterns

## Deployment

### Production Deployment Checklist

- [ ] Set `FASTAPI_DEBUG=false` in production
- [ ] Use strong database password
- [ ] Configure CORS for frontend domain
- [ ] Set up SSL certificates
- [ ] Configure Telegram webhook with HTTPS
- [ ] Set up monitoring and alerting
- [ ] Configure database backups
- [ ] Run database migrations
- [ ] Set up error logging (e.g., Sentry)

### Deploying to Server

1. **SSH into your server**
2. **Clone the repository**
3. **Set up `.env` with production values**
4. **Run Docker Compose in production mode**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```
5. **Set up Telegram webhook**
6. **Configure reverse proxy (nginx/Apache)**

## Troubleshooting

### FastAPI won't start
- Check PostgreSQL is running: `docker ps | grep postgres`
- Check DATABASE_URL in .env
- View logs: `docker-compose logs fastapi`

### React can't connect to API
- Check REACT_APP_API_URL matches FastAPI URL
- Check CORS settings in app/main.py
- Verify FastAPI is running: `curl http://localhost:8000/health`

### Database connection fails
- Verify PostgreSQL container is running
- Check credentials in DATABASE_URL
- Run: `docker-compose logs postgres`

### Telegram webhook not receiving updates
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_WEBHOOK_SECRET` matches bot settings
- Verify webhook URL is HTTPS and accessible

## Deep Agents Integration

Omnissiah uses **LangChain's DeepAgents SDK** for intelligent maintenance management:

- **LLM-Powered Reasoning:** Claude, GPT, or other models understand maintenance needs
- **Tool Calling:** Automatically executes 8 maintenance management tools
- **Planning:** Breaks down complex requests into actionable steps
- **Memory:** PostgreSQL checkpointer persists conversation state

For detailed information, see [DEEPAGENTS_INTEGRATION.md](DEEPAGENTS_INTEGRATION.md).

**Quick Example:**
```
User: "Oil change due in 2 days, update my Honda to 85500 miles, and check my budget"

Agent thinks:
1. Set reminder for oil change (2 days)
2. Update Honda Odyssey to 85500 miles
3. Check maintenance budget
4. Provide summary

Response: ✓ Done! Reminder set. Car updated. Budget at 90% ($450/$500).
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check [agents.md](agents.md) for architecture questions
- Review [DEEPAGENTS_INTEGRATION.md](DEEPAGENTS_INTEGRATION.md) for AI agent details
- View [API documentation](http://localhost:8000/api/docs) 

## Author

Created as a personal home assistant maintenance management system.

---

**Last Updated:** April 2026  
**Agent System:** LangChain DeepAgents SDK v0.1+  
**Version:** 0.1.0 (Beta)
