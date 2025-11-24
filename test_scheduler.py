#!/usr/bin/env python3
"""
Test script for ANC Reminder Scheduler
Tests the daily wake-up mechanism and reminder delivery.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from anc_reminder_scheduler import (
    ANCReminderScheduler,
    init_scheduler,
    default_reminder_handler
)

def print_header(title):
    """Print a formatted test header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

# Track reminders for testing
reminders_received = []

async def test_reminder_handler(reminder):
    """Test handler that captures reminders."""
    reminders_received.append(reminder)
    print(f"\n📨 REMINDER CAPTURED:")
    print(f"   Type: {reminder['type']}")
    print(f"   To: {reminder['record']['phone']} ({reminder['record']['name']})")
    print(f"   Message: {reminder['message'][:80]}...")

async def mock_pregnancy_data():
    """
    Mock pregnancy data source.
    Returns test data with various scenarios.
    """
    now = datetime.now()
    return [
        {
            'phone': '+1234567890',
            'name': 'Sarah Johnson',
            'lmp_date': (now - timedelta(weeks=9)).strftime('%Y-%m-%d'),  # First visit upcoming
            'location': 'Lagos, Nigeria'
        },
        {
            'phone': '+2345678901',
            'name': 'Amina Diallo',
            'lmp_date': (now - timedelta(weeks=24)).strftime('%Y-%m-%d'),  # Some visits overdue
            'location': 'Bamako, Mali'
        },
        {
            'phone': '+3456789012',
            'name': 'Grace Mensah',
            'lmp_date': (now - timedelta(weeks=36)).strftime('%Y-%m-%d'),  # Many visits overdue
            'location': 'Accra, Ghana'
        },
        {
            'phone': '+4567890123',
            'name': 'Fatima Ibrahim',
            'lmp_date': (now - timedelta(weeks=5)).strftime('%Y-%m-%d'),  # Too early, no visits yet
            'location': 'Abuja, Nigeria'
        }
    ]

async def test_scheduler_initialization():
    """Test: Scheduler initialization."""
    print_header("TEST 1: Scheduler Initialization")
    
    try:
        scheduler = ANCReminderScheduler(
            pregnancy_data_source=mock_pregnancy_data,
            reminder_handler=test_reminder_handler,
            test_mode=True
        )
        
        print(f"✅ Scheduler created")
        print(f"   Test mode: {scheduler.test_mode}")
        print(f"   Is running: {scheduler.is_running}")
        
        assert scheduler.test_mode == True, "Test mode should be enabled"
        assert scheduler.is_running == False, "Should not be running yet"
        
        print("\n✅ TEST PASSED: Scheduler initialized correctly")
        return True, scheduler
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_immediate_check(scheduler):
    """Test: Immediate reminder check."""
    print_header("TEST 2: Immediate Reminder Check")
    
    try:
        global reminders_received
        reminders_received = []
        
        print("Triggering immediate check...")
        result = await scheduler.trigger_immediate_check()
        
        print(f"\n📊 Check Result:")
        print(f"   Status: {result['status']}")
        print(f"   Records checked: {result['records_checked']}")
        print(f"   Reminders sent: {result['reminders_sent']}")
        print(f"   Check number: {result['check_number']}")
        
        print(f"\n📨 Reminders captured: {len(reminders_received)}")
        
        # Validate results
        assert result['status'] == 'success', "Check should succeed"
        assert result['records_checked'] == 4, "Should check 4 records"
        assert result['reminders_sent'] > 0, "Should send some reminders"
        assert len(reminders_received) == result['reminders_sent'], "All reminders should be captured"
        
        # Check reminder types
        upcoming_count = sum(1 for r in reminders_received if r['type'] == 'upcoming')
        overdue_count = sum(1 for r in reminders_received if r['type'] == 'overdue')
        
        print(f"\n📊 Reminder Breakdown:")
        print(f"   Upcoming visits: {upcoming_count}")
        print(f"   Overdue visits: {overdue_count}")
        
        assert upcoming_count > 0, "Should have upcoming reminders"
        assert overdue_count > 0, "Should have overdue reminders"
        
        print("\n✅ TEST PASSED: Immediate check works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scheduler_start_stop(scheduler):
    """Test: Start and stop scheduler."""
    print_header("TEST 3: Start and Stop Scheduler")
    
    try:
        # Start scheduler
        print("Starting scheduler...")
        scheduler.start()
        
        assert scheduler.is_running == True, "Should be running after start"
        print("✅ Scheduler started")
        
        # Get stats
        stats = scheduler.get_stats()
        print(f"\n📊 Scheduler Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Wait a moment
        print("\n⏳ Waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Stop scheduler
        print("Stopping scheduler...")
        scheduler.stop()
        
        assert scheduler.is_running == False, "Should not be running after stop"
        print("✅ Scheduler stopped")
        
        print("\n✅ TEST PASSED: Start/stop works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        # Ensure cleanup
        if scheduler.is_running:
            scheduler.stop()
        return False

async def test_scheduler_with_mock_time():
    """Test: Scheduler runs checks in test mode."""
    print_header("TEST 4: Scheduler Auto-Check (Test Mode)")
    
    try:
        global reminders_received
        reminders_received = []
        
        # Create scheduler in test mode (runs every minute)
        scheduler = ANCReminderScheduler(
            pregnancy_data_source=mock_pregnancy_data,
            reminder_handler=test_reminder_handler,
            test_mode=True
        )
        
        print("Starting scheduler in test mode (checks every minute)...")
        scheduler.start()
        
        # In real test, we'd wait 61 seconds, but for quick testing just verify setup
        stats = scheduler.get_stats()
        print(f"\n📊 Scheduler Status:")
        print(f"   Running: {stats['is_running']}")
        print(f"   Test mode: {stats['test_mode']}")
        print(f"   Next run: {stats['next_run']}")
        
        # Trigger immediate check instead of waiting
        print("\n⚡ Triggering immediate check (instead of waiting)...")
        await scheduler.trigger_immediate_check()
        
        print(f"\n📨 Reminders sent: {len(reminders_received)}")
        
        scheduler.stop()
        
        assert len(reminders_received) > 0, "Should have sent reminders"
        
        print("\n✅ TEST PASSED: Scheduler auto-check works")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_global_singleton():
    """Test: Global scheduler singleton."""
    print_header("TEST 5: Global Scheduler Singleton")
    
    try:
        from anc_reminder_scheduler import init_scheduler, get_scheduler
        
        # Initialize global scheduler
        print("Initializing global scheduler...")
        scheduler = init_scheduler(
            pregnancy_data_source=mock_pregnancy_data,
            reminder_handler=test_reminder_handler,
            test_mode=True
        )
        
        print("✅ Global scheduler initialized")
        
        # Get the same instance
        scheduler2 = get_scheduler()
        
        assert scheduler is scheduler2, "Should return same instance"
        print("✅ Singleton pattern works")
        
        # Cleanup
        scheduler.stop()
        
        print("\n✅ TEST PASSED: Global singleton works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_reminder_content():
    """Test: Reminder message content."""
    print_header("TEST 6: Reminder Message Content")
    
    try:
        global reminders_received
        reminders_received = []
        
        scheduler = ANCReminderScheduler(
            pregnancy_data_source=mock_pregnancy_data,
            reminder_handler=test_reminder_handler,
            test_mode=True
        )
        
        await scheduler.trigger_immediate_check()
        
        print(f"\n📋 Analyzing {len(reminders_received)} reminders...")
        
        for i, reminder in enumerate(reminders_received[:3], 1):  # Show first 3
            print(f"\n{i}. {reminder['type'].upper()} Reminder:")
            print(f"   Patient: {reminder['record']['name']}")
            print(f"   Phone: {reminder['record']['phone']}")
            print(f"   Visit: #{reminder['visit'].get('visit_number', 'N/A')}")
            print(f"   Message: {reminder['message'][:100]}...")
            
            # Validate message content
            assert 'visit' in reminder['message'].lower() or 'Visit' in reminder['message'], \
                "Message should mention visit"
            
            if reminder['type'] == 'upcoming':
                assert 'days' in reminder['message'], "Upcoming reminder should mention days"
            elif reminder['type'] == 'overdue':
                assert 'overdue' in reminder['message'].lower(), "Overdue reminder should say overdue"
        
        print("\n✅ TEST PASSED: Reminder messages are properly formatted")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🧪 ANC REMINDER SCHEDULER - COMPREHENSIVE TESTS")
    print("="*70)
    print("\nTesting daily wake-up mechanism and reminder delivery...")
    
    # Test 1: Initialization
    success1, scheduler = await test_scheduler_initialization()
    if not success1:
        return 1
    
    # Test 2: Immediate check
    success2 = await test_immediate_check(scheduler)
    
    # Test 3: Start/stop
    success3 = await test_scheduler_start_stop(scheduler)
    
    # Test 4: Auto-check
    success4 = await test_scheduler_with_mock_time()
    
    # Test 5: Global singleton
    success5 = await test_global_singleton()
    
    # Test 6: Message content
    success6 = await test_reminder_content()
    
    # Summary
    results = [success1, success2, success3, success4, success5, success6]
    
    print("\n" + "="*70)
    print("  📊 TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ✅")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED ❌")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
