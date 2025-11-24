#!/usr/bin/env python3
"""
Interactive validation demo for Daily ANC Reminder Scheduler
Run this to manually test the scheduler feature
"""

import asyncio
from datetime import datetime, timedelta
from anc_reminder_scheduler import init_scheduler

# Track reminders for display
reminders_log = []

async def demo_reminder_handler(reminder):
    """Demo handler that displays reminders nicely."""
    reminders_log.append(reminder)
    
    # Visual display
    icon = "🔔" if reminder['type'] == 'upcoming' else "⚠️ "
    print(f"\n{icon} {reminder['type'].upper()} REMINDER:")
    print(f"   👤 Patient: {reminder['record']['name']}")
    print(f"   📞 Phone: {reminder['record']['phone']}")
    print(f"   📍 Location: {reminder['record']['location']}")
    print(f"   🗓️  Visit: #{reminder['visit'].get('visit_number', 'N/A')}")
    
    if reminder['type'] == 'upcoming':
        print(f"   📅 Date: {reminder['visit']['scheduled_date']}")
        print(f"   ⏰ In {reminder['visit']['days_until']} days")
    else:
        print(f"   📅 Was due: {reminder['visit']['scheduled_date']}")
        print(f"   ⏰ {reminder['visit']['days_overdue']} days overdue")
    
    print(f"   💬 {reminder['message']}")

async def mock_pregnancy_data():
    """Mock pregnancy data with realistic scenarios."""
    now = datetime.now()
    return [
        {
            'phone': '+234-801-234-5678',
            'name': 'Amina Bello',
            'lmp_date': (now - timedelta(weeks=9)).strftime('%Y-%m-%d'),
            'location': 'Lagos, Nigeria',
            'age': 28
        },
        {
            'phone': '+223-76-12-34-56',
            'name': 'Fatoumata Traoré',
            'lmp_date': (now - timedelta(weeks=24)).strftime('%Y-%m-%d'),
            'location': 'Bamako, Mali',
            'age': 32
        },
        {
            'phone': '+233-24-567-8901',
            'name': 'Ama Mensah',
            'lmp_date': (now - timedelta(weeks=36)).strftime('%Y-%m-%d'),
            'location': 'Accra, Ghana',
            'age': 25
        }
    ]

async def demo():
    print("\n" + "="*70)
    print("  🎯 DAILY ANC REMINDER SCHEDULER - VALIDATION DEMO")
    print("="*70)
    print("\nThis demo shows the daily wake-up mechanism in action.")
    print("The scheduler checks pregnancy records and sends reminders.")
    print("\n" + "="*70 + "\n")
    
    # Initialize scheduler
    print("📅 Initializing ANC Reminder Scheduler...")
    scheduler = init_scheduler(
        pregnancy_data_source=mock_pregnancy_data,
        reminder_handler=demo_reminder_handler,
        test_mode=True  # Test mode for demo
    )
    
    print("✅ Scheduler initialized")
    print(f"   • Test mode: {scheduler.test_mode}")
    print(f"   • Schedule time: {scheduler.schedule_time} (daily)")
    print(f"   • In test mode: Runs every minute")
    
    # Show initial stats
    stats = scheduler.get_stats()
    print(f"\n📊 Initial Stats:")
    print(f"   • Checks run: {stats['total_checks']}")
    print(f"   • Reminders sent: {stats['total_reminders_sent']}")
    
    input("\n⏸️  Press Enter to trigger an immediate check...")
    
    # Trigger immediate check
    print("\n" + "="*70)
    print("  ⚡ TRIGGERING IMMEDIATE REMINDER CHECK")
    print("="*70)
    
    global reminders_log
    reminders_log = []
    
    result = await scheduler.trigger_immediate_check()
    
    print(f"\n" + "="*70)
    print("  📊 CHECK RESULTS")
    print("="*70)
    print(f"✅ Status: {result['status']}")
    print(f"📋 Records checked: {result['records_checked']}")
    print(f"📨 Reminders sent: {result['reminders_sent']}")
    print(f"🔢 Check number: {result['check_number']}")
    
    # Summary
    upcoming = sum(1 for r in reminders_log if r['type'] == 'upcoming')
    overdue = sum(1 for r in reminders_log if r['type'] == 'overdue')
    
    print(f"\n📊 Reminder Breakdown:")
    print(f"   • Upcoming visits (within 7 days): {upcoming}")
    print(f"   • Overdue visits (>7 days past): {overdue}")
    print(f"   • Total: {len(reminders_log)}")
    
    # Show updated stats
    stats = scheduler.get_stats()
    print(f"\n📊 Updated Stats:")
    print(f"   • Total checks: {stats['total_checks']}")
    print(f"   • Total reminders: {stats['total_reminders_sent']}")
    
    # Demonstrate scheduling
    input("\n⏸️  Press Enter to start the scheduler (will run checks periodically)...")
    
    print("\n" + "="*70)
    print("  🚀 STARTING SCHEDULER")
    print("="*70)
    
    scheduler.start()
    
    stats = scheduler.get_stats()
    print(f"✅ Scheduler is running")
    print(f"   • Next scheduled run: {stats['next_run']}")
    print(f"   • In test mode: Will run again in ~1 minute")
    
    print("\n💡 In production mode, the scheduler would:")
    print("   1. Run daily at 8:00 AM (configurable)")
    print("   2. Check all active pregnancy records")
    print("   3. Identify patients with upcoming/overdue visits")
    print("   4. Resume their sessions and send reminders")
    print("   5. Log all reminder deliveries")
    
    input("\n⏸️  Press Enter to stop the scheduler...")
    
    scheduler.stop()
    print("\n🛑 Scheduler stopped")
    
    print("\n" + "="*70)
    print("  ✅ VALIDATION DEMO COMPLETE")
    print("="*70)
    print("\nKey features demonstrated:")
    print("  ✅ Scheduler initialization with configurable settings")
    print("  ✅ Immediate check capability (for testing)")
    print("  ✅ Automatic pregnancy record fetching")
    print("  ✅ ANC schedule calculation for each patient")
    print("  ✅ Reminder generation (upcoming + overdue)")
    print("  ✅ Reminder delivery with patient details")
    print("  ✅ Start/stop scheduler control")
    print("  ✅ Statistics tracking")
    print("\n")

if __name__ == "__main__":
    asyncio.run(demo())
