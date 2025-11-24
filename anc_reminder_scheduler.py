#!/usr/bin/env python3
"""
ANC Reminder Scheduler - Daily Wake-up Mechanism

This module implements the daily scheduling mechanism for ANC reminders.
It checks pregnancy records daily and identifies which patients need reminders
for upcoming or overdue ANC visits.

Uses APScheduler for reliable job scheduling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logger = logging.getLogger(__name__)


class ANCReminderScheduler:
    """
    Scheduler for daily ANC reminder checks.
    
    Features:
    - Daily wake-up at configured time (default: 8:00 AM)
    - Checks all pregnancy records for upcoming/overdue visits
    - Triggers reminder delivery for qualifying patients
    - Supports testing mode with shorter intervals
    """
    
    def __init__(
        self,
        pregnancy_data_source,  # Will be MCP server in production
        reminder_handler,       # Function to send reminders
        schedule_time: str = "08:00",
        test_mode: bool = False
    ):
        """
        Initialize the ANC reminder scheduler.
        
        Args:
            pregnancy_data_source: Source for pregnancy records (MCP server or mock)
            reminder_handler: Async function to handle reminder delivery
            schedule_time: Daily time to run checks (HH:MM format, 24-hour)
            test_mode: If True, runs every minute instead of daily
        """
        self.pregnancy_data_source = pregnancy_data_source
        self.reminder_handler = reminder_handler
        self.schedule_time = schedule_time
        self.test_mode = test_mode
        
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.check_count = 0
        self.reminders_sent = 0
        
        logger.info(f"📅 ANC Reminder Scheduler initialized (test_mode={test_mode})")
    
    async def check_anc_reminders(self):
        """
        Main job: Check all pregnancy records and send reminders.
        
        This is the core function that runs on schedule.
        It:
        1. Fetches all active pregnancy records
        2. Calculates ANC schedule for each
        3. Identifies patients needing reminders
        4. Triggers reminder delivery
        """
        self.check_count += 1
        logger.info(f"🔔 Starting ANC reminder check #{self.check_count}")
        
        try:
            # Get all active pregnancy records
            records = await self._get_pregnancy_records()
            logger.info(f"📋 Found {len(records)} active pregnancy records")
            
            reminders_to_send = []
            
            for record in records:
                # Calculate ANC schedule
                from pregnancy_companion_agent import calculate_anc_schedule
                
                schedule_result = calculate_anc_schedule(record['lmp_date'])
                
                if schedule_result['status'] != 'success':
                    logger.warning(f"⚠️  Failed to calculate schedule for {record['phone']}")
                    continue
                
                # Check for upcoming visits (within 7 days)
                if schedule_result['next_visit']:
                    next_visit = schedule_result['next_visit']
                    if 0 <= next_visit['days_until'] <= 7:
                        reminders_to_send.append({
                            'type': 'upcoming',
                            'record': record,
                            'visit': next_visit,
                            'message': f"Reminder: You have an ANC visit coming up in {next_visit['days_until']} days (Visit #{next_visit['visit_number']} on {next_visit['scheduled_date']})"
                        })
                
                # Check for overdue visits
                if schedule_result['overdue_visits']:
                    for overdue in schedule_result['overdue_visits']:
                        reminders_to_send.append({
                            'type': 'overdue',
                            'record': record,
                            'visit': overdue,
                            'message': f"Important: Your ANC Visit #{overdue['visit_number']} is {overdue['days_overdue']} days overdue. Please schedule an appointment."
                        })
            
            # Send reminders
            logger.info(f"📨 Sending {len(reminders_to_send)} reminders")
            
            for reminder in reminders_to_send:
                try:
                    await self.reminder_handler(reminder)
                    self.reminders_sent += 1
                    logger.info(f"✅ Reminder sent to {reminder['record']['phone']} ({reminder['type']})")
                except Exception as e:
                    logger.error(f"❌ Failed to send reminder: {e}")
            
            logger.info(f"✅ ANC reminder check complete: {len(reminders_to_send)} reminders sent")
            
            return {
                'status': 'success',
                'records_checked': len(records),
                'reminders_sent': len(reminders_to_send),
                'check_number': self.check_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error during ANC reminder check: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'check_number': self.check_count
            }
    
    async def _get_pregnancy_records(self) -> List[Dict[str, Any]]:
        """
        Fetch all active pregnancy records.
        
        In production, this will query the MCP server.
        For now, it uses the provided data source.
        
        Returns:
            List of pregnancy record dictionaries
        """
        if callable(self.pregnancy_data_source):
            return await self.pregnancy_data_source()
        elif isinstance(self.pregnancy_data_source, list):
            return self.pregnancy_data_source
        else:
            # Mock data for testing
            logger.warning("📋 Using mock pregnancy data")
            return [
                {
                    'phone': '+1234567890',
                    'name': 'Test Patient 1',
                    'lmp_date': (datetime.now() - timedelta(weeks=20)).strftime('%Y-%m-%d'),
                    'location': 'Lagos, Nigeria'
                },
                {
                    'phone': '+0987654321',
                    'name': 'Test Patient 2',
                    'lmp_date': (datetime.now() - timedelta(weeks=35)).strftime('%Y-%m-%d'),
                    'location': 'Bamako, Mali'
                }
            ]
    
    def start(self):
        """
        Start the scheduler.
        
        In test mode: Runs every minute
        In production mode: Runs daily at configured time
        """
        if self.is_running:
            logger.warning("⚠️  Scheduler already running")
            return
        
        if self.test_mode:
            # Test mode: Run every minute
            trigger = IntervalTrigger(minutes=1)
            logger.info("🧪 Starting scheduler in TEST MODE (every minute)")
        else:
            # Production mode: Run daily at scheduled time
            hour, minute = map(int, self.schedule_time.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
            logger.info(f"🚀 Starting scheduler in PRODUCTION MODE (daily at {self.schedule_time})")
        
        self.scheduler.add_job(
            self.check_anc_reminders,
            trigger=trigger,
            id='anc_reminder_check',
            name='ANC Reminder Daily Check',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("✅ ANC Reminder Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("⚠️  Scheduler not running")
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("🛑 ANC Reminder Scheduler stopped")
    
    async def trigger_immediate_check(self):
        """
        Trigger an immediate reminder check (for testing).
        
        Returns:
            Result of the check
        """
        logger.info("⚡ Triggering immediate ANC reminder check")
        return await self.check_anc_reminders()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary with scheduler stats
        """
        return {
            'is_running': self.is_running,
            'total_checks': self.check_count,
            'total_reminders_sent': self.reminders_sent,
            'test_mode': self.test_mode,
            'schedule_time': self.schedule_time,
            'next_run': self.scheduler.get_jobs()[0].next_run_time.isoformat() if self.scheduler.get_jobs() else None
        }


# Default reminder handler (can be overridden)
async def default_reminder_handler(reminder: Dict[str, Any]):
    """
    Default handler for reminder delivery.
    
    In production, this would:
    - Resume the patient's session
    - Send the reminder message
    - Log the interaction
    
    For now, it just logs the reminder.
    
    Args:
        reminder: Reminder dictionary with record, visit, and message
    """
    logger.info(f"📨 REMINDER: {reminder['type'].upper()}")
    logger.info(f"   To: {reminder['record']['phone']} ({reminder['record']['name']})")
    logger.info(f"   Message: {reminder['message']}")
    
    # In production, this would call:
    # await run_agent_interaction(
    #     user_input="",  # System-initiated
    #     user_id=reminder['record']['phone'],
    #     session_id=f"reminder_{datetime.now().isoformat()}",
    #     system_message=reminder['message']
    # )


# Singleton instance (will be initialized by main module)
_scheduler_instance: Optional[ANCReminderScheduler] = None


def get_scheduler() -> Optional[ANCReminderScheduler]:
    """Get the global scheduler instance."""
    return _scheduler_instance


def init_scheduler(
    pregnancy_data_source,
    reminder_handler=None,
    schedule_time: str = "08:00",
    test_mode: bool = False
) -> ANCReminderScheduler:
    """
    Initialize the global scheduler instance.
    
    Args:
        pregnancy_data_source: Source for pregnancy records
        reminder_handler: Custom reminder handler (optional)
        schedule_time: Daily time to run checks (HH:MM)
        test_mode: Enable test mode (every minute)
    
    Returns:
        Initialized scheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        logger.warning("⚠️  Scheduler already initialized, stopping previous instance")
        _scheduler_instance.stop()
    
    handler = reminder_handler or default_reminder_handler
    
    _scheduler_instance = ANCReminderScheduler(
        pregnancy_data_source=pregnancy_data_source,
        reminder_handler=handler,
        schedule_time=schedule_time,
        test_mode=test_mode
    )
    
    return _scheduler_instance
