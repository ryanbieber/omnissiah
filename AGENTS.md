# Omnissiah - Agent Architecture & Design


## CODE STANDARDS
When working on thsi code base do not use a try except, I want to fail hard if things break. This will allow for faster iterations and for
solving shitty problems you make.


## Overview

Omnissiah is a multi-agent home maintenance management system designed to coordinate maintenance scheduling, budget optimization, and user notifications across house, car, and lawn maintenance domains.

## Agent Types

### 1. Chainlit Chat Agent
**Purpose:** Natural language interface for user interactions  
**Location:** `app/chainlit.py`  
**Responsibilities:**
- Parse user queries for maintenance-related requests
- Create and update maintenance tasks through conversation
- Provide maintenance status summaries
- Answer questions about upcoming maintenance and budgets
- Accept task status updates via chat

**Flow:**
```
User Message → Chainlit Agent → Pattern Matching/NLP → Database Updates → Response
```

**MVP Implementation:**
- Simple pattern matching for common queries
- Direct database updates for task management
- Status queries and reporting

**Future Enhancement:**
- LLM integration (GPT-4, Claude) for better understanding
- Intent recognition for complex multi-step requests
- Maintenance recommendation system

### 2. Deep Reasoning Agent
**Purpose:** Intelligent decision-making for maintenance optimization  
**Location:** `agents/deep_agent.py` (to be implemented)  
**Responsibilities:**
- Analyze maintenance schedules across all vehicles
- Predict maintenance needs based on vehicle mileage/age
- Optimize maintenance scheduling to minimize costs
- Detect maintenance patterns and anomalies
- Generate recommendations for preventive maintenance

**Input Data:**
- Current maintenance schedule
- Task history and completion rates
- Vehicle mileage and usage patterns
- Budget constraints
- Historical maintenance costs

**Output Data:**
- Maintenance recommendations with priority scores
- Optimized scheduling suggestions
- Cost predictions and alerts
- Risk assessments (e.g., "high chance of failure if not serviced")

**Example Logic:**
```python
# Pseudocode
def analyze_vehicle_maintenance(car, tasks, budget_history):
    # Calculate wear rate based on mileage
    wear_rate = calculate_wear(car.current_miles, car.age)
    
    # Predict next failure points
    predictions = predict_failures(car.model, wear_rate, tasks)
    
    # Optimize scheduling within budget
    optimal_schedule = optimize_schedule(predictions, budget_history)
    
    return {
        "urgent_items": identify_urgent(predictions),
        "recommended_schedule": optimal_schedule,
        "cost_estimate": calculate_costs(optimal_schedule),
        "risk_level": assess_risk(predictions)
    }
```

### 3. Telegram Orchestration Agent
**Purpose:** Send notifications and collect user responses via Telegram  
**Location:** `app/telegram/handler.py`  
**Responsibilities:**
- Send maintenance alerts based on schedules
- Receive task updates from user via Telegram
- Send budget warnings when limits approached
- Provide quick status checks via commands
- Handle maintenance photos/evidence submissions

**Telegram Commands:**
```
/status           - Get current maintenance status
/upcoming         - List upcoming maintenance
/complete [id]    - Mark task as completed
/budget           - Show budget status
/cars             - List vehicles and mileage
/remind [days]    - Set custom reminders
```

**Notification Types:**
1. **Scheduled Alerts:** "Oil change due in 3 days"
2. **Overdue Alerts:** "Air filter maintenance is overdue!"
3. **Budget Warnings:** "Maintenance budget 80% spent this month"
4. **Completion Confirmations:** "Confirmed: Oil change completed on [date]"

## Agent Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interactions                         │
├──────────────┬──────────────┬──────────────────┬─────────────┤
│              │              │                  │             │
▼              ▼              ▼                  ▼             ▼
Chainlit    Telegram      REST API          React UI      Admin Panel
Chat         Bot         (Direct calls)     Dashboard     (Management)
│              │              │                  │             │
└──────────────┴──────────────┴──────────────────┴─────────────┘
               │
               ▼
        ┌──────────────────┐
        │  API Layer       │
        │  /api/agent/*    │
        └──────────────────┘
               │
    ┌──────────┴──────────────┐
    │                         │
    ▼                         ▼
┌─────────────────┐   ┌──────────────────┐
│  Deep Agent     │   │  Database        │
│  (Reasoning)    │   │  (PostgreSQL)    │
│  - Scheduling  │   │  - Tasks         │
│  - Optimization│   │  - Maintenance   │
│  - Prediction  │   │  - History       │
└─────────────────┘   │  - Budgets       │
    │                 └──────────────────┘
    │
    ▼
┌─────────────────┐
│ Execution Queue │
│ (Agent Logs)    │
└─────────────────┘

## Skills System

### Overview
The agents leverage a **skill.md-based knowledge system** for expert maintenance guidance. Skills are organized by domain (car maintenance, house maintenance, lawncare) with detailed procedures, schedules, and best practices.

**Location:** `agents/skills/`

### Skill Structure

```
agents/skills/
├── car_maintenance/
│   └── skill.md          (Oil changes, tire maintenance, brakes, fluids, etc.)
├── house_maintenance/
│   └── skill.md          (HVAC, plumbing, electrical, roof, foundation, etc.)
└── lawncare/
    └── skill.md          (Iowa/Waverly-specific: fertilization, aeration, seeding, etc.)
```

### Skill Loading Architecture

1. **SkillLoader** (`agents/skill_loader.py`)
   - Parses skill.md files from disk on startup
   - Extracts skill names and detailed content
   - Indexes all skills by category
   - Exports skill summary as JSON for reference

2. **DeepAgent Integration**
   - Loads all skills during initialization
   - Includes skill summaries in LLM system prompt
   - Provides rich maintenance expertise context
   - Enables expert-level recommendations

### Creating/Updating Skills

#### Standard Format
Each skill.md file follows this structure:

```markdown
# [Category] Skills

## Skill Name
### Subtopic
Details, procedures, best practices...

## Another Skill
Comprehensive maintenance information...
```

#### Key Guidelines
- **Headings:** Use `## Skill Name` for extractable sections
- **Content:** Include schedules, intervals, procedures, costs
- **Regional Data:** Lawncare includes Iowa/Waverly specifics
- **Actionable:** Every skill should guide real maintenance tasks
- **Complete:** Cover the full scope of the maintenance domain

### Testing Skills

Test skill ingestion with uv:

```bash
# Using uv (recommended for all testing)
uv run test-skills

# Or direct Python
python -m agents.skill_loader
```

Expected output shows all loaded categories and skills.

### Accessing Skills Programmatically

```python
from agents.skill_loader import get_skill_loader

loader = get_skill_loader()

# Get category summary
summary = loader.get_all_categories_summary()

# Get specific category skills
car_skills = loader.get_category_skills('car_maintenance')

# Get skill content
content = loader.get_skill_content('lawncare', 'Lawn Fertilization')

# Get formatted for LLM
descriptions = loader.get_formatted_skill_descriptions()

# Export to JSON
loader.export_to_json()
```

## Database Schema for Agents

### AgentExecution Table
```python
AgentExecution(
    id: int,
    agent_type: str,           # 'chainlit', 'deep_agent', 'telegram_orchestrator'
    input_data: JSON,          # Serialized input parameters
    output_data: JSON,         # Serialized output/results
    status: str,               # 'pending', 'running', 'completed', 'failed'
    error_message: str,        # Error details if failed
    created_at: datetime,
    completed_at: datetime
)
```

## Agent Lifecycle & Execution

### Execution Sequence
1. **User Action** → Triggers API endpoint or webhook
2. **Agent Creation** → Create execution record with `status='pending'`
3. **Agent Processing** → Update status to `'running'`
4. **Result Processing** → Update status to `'completed'` or `'failed'`
5. **Side Effects** → Telegram notifications, database updates
6. **Response** → Return result to user/caller

### Error Handling
- Automatic retry for transient failures
- Detailed error logging in `error_message` field
- Fallback notifications to user
- Manual intervention queue for critical failures

## Integration Points

### API Endpoints for Agents
```
POST   /api/agent/execute              - Execute an agent task
GET    /api/agent/{id}                 - Get execution status
GET    /api/agent?status=pending       - List pending executions
PUT    /api/agent/{id}                 - Update with results
POST   /api/telegram/webhook           - Telegram webhook
GET    /api/maintenance/{id}           - Get task details
PUT    /api/tasks/{id}                 - Update task status
```

### Data Flow Example: User Completes Task via Telegram

```
User sends: /complete oil_change_001
    ↓
Telegram webhook receives update
    ↓
Telegram Orchestration Agent processes
    ↓
Calls: PUT /api/tasks/{task_id} 
       with status='completed', last_completed=now
    ↓
Database updated
    ↓
Deep Agent triggered to recalculate next maintenance due date
    ↓
Chainlit Agent notified to suggest next task
    ↓
Telegram confirmation sent to user
```

## Configuration & Environment

### Agent Configuration
```python
# config/agent_config.py (to be created)
DEEP_AGENT_CONFIG = {
    "enabled": True,
    "check_interval_minutes": 60,
    "prediction_lookahead_days": 90,
}

TELEGRAM_ORCHESTRATOR_CONFIG = {
    "enabled": True,
    "notification_times": ["09:00", "18:00"],  # UTC
    "alert_threshold_days": 7,
}

CHAINLIT_CONFIG = {
    "enabled": True,
    "model": "gpt-4",  # Future
    "temperature": 0.7,
}
```

## Future Enhancements

### Phase 2: LLM Integration
- Replace pattern matching with LLM reasoning
- Use Claude/GPT-4 for natural language understanding
- Multi-turn conversation context

### Phase 3: Advanced Analytics
- Machine learning for failure prediction
- Seasonal maintenance pattern detection
- Cost optimization recommendations
- Cross-vehicle maintenance correlation

### Phase 4: Automation & Workflow
- Automatic task creation based on vehicle mileage
- Smart scheduling to consolidate appointments
- Third-party API integrations (weather for lawn care, fuel prices)
- Photo evidence collection and storage

### Phase 5: Multi-User & Sharing
- Family member notifications
- Shared calendars
- Permission levels (admin, contributor, viewer)
- Notification customization per user

## Agent Testing Strategy

### Unit Tests
- Test agent decision logic in isolation
- Mock database responses
- Validate output formats

### Integration Tests
- Test full workflow from user action to database update
- Telegram webhook simulation
- Agent chain interactions

### Mock Scenarios
```python
# tests/agents/test_deep_agent.py
def test_oil_change_overdue_prediction():
    car = Car(make="Ford", model="Fiesta", current_miles=84500)
    # Oil change every 5000 miles, last at 84000
    # Should predict due at 89000 miles
    prediction = deep_agent.predict_maintenance(car)
    assert prediction.oil_change.due_miles == 89000

def test_budget_warning_threshold():
    budget = Budget(category="maintenance", limit=500, spent=400)
    # 80% threshold reached
    warning = deep_agent.check_budget_alerts([budget])
    assert warning[0].severity == "warning"
    assert "80%" in warning[0].message
```

## Deployment & Monitoring

### Agent Health Checks
- Monitor execution success rates
- Alert if any agent is down
- Track average execution time
- Log all failures for debugging

### Metrics to Track
- Agents execution count per hour/day
- Average execution time per agent type
- Error rate and types
- User interaction patterns
- Telegram notification delivery rate

### Logging
```python
# All agent actions logged with context
logger.info(
    "Agent execution",
    extra={
        "agent_type": "deep_agent",
        "execution_id": 123,
        "duration_ms": 450,
        "status": "completed",
        "input_hash": "abc123",
        "output_size": 1024,
    }
)
```

---

## Summary

The Omnissiah agent architecture is designed to be:
- **Modular:** Each agent has clear responsibility
- **Extensible:** Easy to add new agent types
- **Observable:** Comprehensive logging and monitoring
- **Resilient:** Error handling and retry logic
- **User-Centric:** Multiple interaction channels (chat, Telegram, UI)

The system grows from basic pattern matching (MVP) to sophisticated LLM-powered reasoning and automation in future phases.
