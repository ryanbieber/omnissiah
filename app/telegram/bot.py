"""Telegram bot handler for Omnissiah (using long polling)"""
from fastapi import APIRouter
import asyncio
import json
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config.settings import get_settings
from database.database import SessionLocal
from database.models import MaintenanceTask, MaintenanceItem, Budget
from agents.deep_agent import DeepAgent
from agents.telegram_orchestrator import TelegramOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize agents
deep_agent = DeepAgent()
telegram_orchestrator = TelegramOrchestrator()

# Global polling task
polling_task = None
bot = None


async def start_polling():
    """
    Start the Telegram bot in polling mode.
    Does not require a public webhook URL.
    """
    global bot, polling_task
    
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        logger.info("✅ Telegram bot polling started")
        
        offset = 0
        while True:
            try:
                # Get updates from Telegram
                updates = await bot.get_updates(offset=offset, timeout=30, allowed_updates=["message"])
                
                for update in updates:
                    try:
                        if update.message and update.message.text:
                            message = update.message
                            chat_id = message.chat.id
                            text = message.text.strip()
                            user_id = message.from_user.id
                            username = message.from_user.username or "Unknown"
                            
                            logger.info(f"📨 Message from @{username} (ID: {user_id}): {text}")
                            
                            # Process through deep agent
                            db = SessionLocal()
                            try:
                                # Load previous checkpoint if exists
                                thread_id = f"user_{user_id}"
                                checkpoint = deep_agent.load_checkpoint(thread_id)
                                
                                response = await deep_agent.process_user_message(
                                    text,
                                    chat_id,
                                    user_id,
                                    db
                                )
                                
                                # Save checkpoint after processing
                                checkpoint_data = {
                                    "last_message": text,
                                    "last_response": response,
                                    "chat_id": chat_id,
                                    "username": username
                                }
                                deep_agent.save_checkpoint(thread_id, checkpoint_data)
                                
                                # Send response back to Telegram
                                await telegram_orchestrator.send_message(chat_id, response)
                            finally:
                                db.close()
                        
                        offset = update.update_id + 1
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}", exc_info=True)
                        offset = update.update_id + 1
                
            except TelegramError as e:
                logger.error(f"Telegram API error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry
            except Exception as e:
                logger.error(f"Polling error: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    except Exception as e:
        logger.error(f"Failed to start polling: {str(e)}", exc_info=True)


async def stop_polling():
    """
    Stop the Telegram bot polling.
    """
    global polling_task, bot
    
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
        polling_task = None
    
    if bot:
        await bot.close()
        bot = None
    
    logger.info("🛑 Telegram bot polling stopped")


@router.get("/")
async def telegram_status():
    """Get Telegram bot status"""
    return {
        "status": "Telegram bot polling",
        "mode": "polling",
        "configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "running": polling_task is not None and not polling_task.done()
    }


@router.get("/commands")
async def get_commands():
    """Get list of available Telegram commands"""
    return {
        "commands": [
            {
                "command": "/start",
                "description": "Initialize the bot"
            },
            {
                "command": "/help",
                "description": "Show available commands"
            },
            {
                "command": "/status",
                "description": "Get maintenance status"
            },
            {
                "command": "/upcoming",
                "description": "Show upcoming maintenance"
            },
            {
                "command": "/add",
                "description": "Add new maintenance task"
            },
            {
                "command": "/complete",
                "description": "Mark task as completed"
            },
            {
                "command": "/budget",
                "description": "Show budget status"
            },
            {
                "command": "/cars",
                "description": "List your vehicles"
            }
        ],
        "natural_language": "Send any message to interact naturally with the agent"
    }
