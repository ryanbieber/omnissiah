"""Telegram orchestration agent for sending notifications"""
import httpx
import logging
from config.settings import get_settings
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramOrchestrator:
    """
    Orchestrates Telegram notifications and bot interactions.
    Sends messages, reminders, and handles bot communication.
    """
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (Markdown, HTML, or None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent to {chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def send_notification(
        self,
        chat_id: int,
        title: str,
        message: str,
        urgency: str = "normal"
    ) -> bool:
        """
        Send a notification with formatting based on urgency.
        
        Args:
            chat_id: Telegram chat ID
            title: Notification title
            message: Notification message
            urgency: "low", "normal", or "high"
            
        Returns:
            True if successful
        """
        if urgency == "high":
            emoji = "🚨"
        elif urgency == "low":
            emoji = "ℹ️"
        else:
            emoji = "📢"
        
        formatted_message = f"{emoji} **{title}**\n{message}"
        return await self.send_message(chat_id, formatted_message)
    
    async def send_maintenance_alert(
        self,
        chat_id: int,
        maintenance_name: str,
        due_date: str,
        vehicle: Optional[str] = None
    ) -> bool:
        """
        Send a maintenance alert notification.
        
        Args:
            chat_id: Telegram chat ID
            maintenance_name: Name of maintenance task
            due_date: When it's due
            vehicle: Vehicle name (optional)
            
        Returns:
            True if successful
        """
        vehicle_info = f" on {vehicle}" if vehicle else ""
        message = (
            f"🔧 **Maintenance Reminder**\n"
            f"Task: {maintenance_name}{vehicle_info}\n"
            f"Due: {due_date}"
        )
        return await self.send_message(chat_id, message)
    
    async def send_budget_warning(
        self,
        chat_id: int,
        budget_name: str,
        spent: float,
        limit: float
    ) -> bool:
        """
        Send a budget warning when spending approaches limit.
        
        Args:
            chat_id: Telegram chat ID
            budget_name: Budget category name
            spent: Amount spent
            limit: Budget limit
            
        Returns:
            True if successful
        """
        percentage = (spent / limit * 100) if limit > 0 else 0
        
        if percentage > 100:
            emoji = "🚨"
            status = "OVER BUDGET"
        elif percentage > 80:
            emoji = "⚠️"
            status = "WARNING"
        else:
            emoji = "💰"
            status = "OK"
        
        message = (
            f"{emoji} **{budget_name} Budget**\n"
            f"Status: {status}\n"
            f"Spent: ${spent:.2f} / ${limit:.2f}\n"
            f"Progress: {percentage:.1f}%"
        )
        return await self.send_message(chat_id, message)
    
    async def send_task_confirmation(
        self,
        chat_id: int,
        task_name: str,
        action: str = "created"
    ) -> bool:
        """
        Send confirmation when a task is created or updated.
        
        Args:
            chat_id: Telegram chat ID
            task_name: Name of task
            action: What was done (created, updated, completed)
            
        Returns:
            True if successful
        """
        emoji_map = {
            "created": "✨",
            "updated": "🔄",
            "completed": "✅",
            "deleted": "🗑️"
        }
        emoji = emoji_map.get(action, "📝")
        
        message = f"{emoji} Task {action}: **{task_name}**"
        return await self.send_message(chat_id, message)
    
    async def send_help_message(self, chat_id: int) -> bool:
        """Send help/instructions message"""
        help_text = (
            "🤖 **Omnissiah Maintenance Assistant**\n\n"
            "I can help you manage your maintenance:\n\n"
            "**Commands:**\n"
            "/status - Show maintenance status\n"
            "/upcoming - List upcoming tasks\n"
            "/add - Add new maintenance task\n"
            "/budget - Check budget status\n"
            "/help - Show this message\n\n"
            "**Or just chat naturally:**\n"
            "• 'Remind me about oil change in 3 days'\n"
            "• 'Mark task 5 complete'\n"
            "• 'Update Honda to 68000 miles'\n"
            "• 'Show pending maintenance'"
        )
        return await self.send_message(chat_id, help_text)
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Register webhook URL with Telegram.
        
        Args:
            webhook_url: Full URL where Telegram will send updates
            
        Returns:
            True if successful
        """
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/setWebhook",
                    json={
                        "url": webhook_url,
                        "secret_token": settings.TELEGRAM_WEBHOOK_SECRET
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook set to {webhook_url}")
                    return True
                else:
                    logger.error(f"Failed to set webhook: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error setting webhook: {str(e)}")
            return False
    
    async def get_bot_info(self) -> Optional[dict]:
        """Get bot information from Telegram"""
        if not self.bot_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/getMe")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error getting bot info: {str(e)}")
        
        return None


# Global instance
telegram_orchestrator = TelegramOrchestrator()
