"""FastAPI main application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
import time
from config.settings import get_settings
from database.database import engine, Base
from app.routes import maintenance, cars, tasks, budgets, agent
from app.telegram import bot

logger = logging.getLogger(__name__)

# Create database tables with retry logic
def init_db_with_retry(max_retries=10, initial_delay=1):
    """Initialize database tables with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database initialization (attempt {attempt + 1}/{max_retries})")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Database connection failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to initialize database after {max_retries} attempts")
                raise

init_db_with_retry()

settings = get_settings()

app = FastAPI(
    title="Omnissiah",
    description="Home Assistant Maintenance Management App",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["maintenance"])
app.include_router(cars.router, prefix="/api/cars", tags=["cars"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(bot.router, prefix="/api/telegram", tags=["telegram"])


@app.on_event("startup")
async def startup_event():
    """Start Telegram bot polling on application startup"""
    logger.info("🚀 Starting Omnissiah...")
    # Start polling in background
    bot.polling_task = asyncio.create_task(bot.start_polling())


@app.on_event("shutdown")
async def shutdown_event():
    """Stop Telegram bot polling on application shutdown"""
    logger.info("💤 Shutting down Omnissiah...")
    await bot.stop_polling()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Omnissiah - Home Assistant Maintenance Management",
        "version": "0.1.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.FASTAPI_DEBUG,
    )
