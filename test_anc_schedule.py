#!/usr/bin/env python3
"""
Test script for ANC Schedule Calculation Tool
Tests the calculate_anc_schedule function with various scenarios.
"""

import sys
import datetime
from pregnancy_companion_agent import calculate_anc_schedule

def print_header(title):
    """Print a formatted test header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_schedule(schedule_data):
    """Pretty print the ANC schedule."""
    if schedule_data["status"] != "success":
        print(f"❌ Error: {schedule_data.get('error_message', 'Unknown error')}")
        return False
    
    print(f"\n📅 LMP Date: {schedule_data['lmp_date']}")
    print(f"🤰 Current Gestational Age: {schedule_data['current_gestational_age']}")
    print(f"📊 Total ANC Visits: {schedule_data['total_visits']}")
    
    # Next visit
    if schedule_data['next_visit']:
        nv = schedule_data['next_visit']
        print(f"\n🔔 NEXT VISIT:")
        print(f"   Visit #{nv['visit_number']} - Week {nv['week']}")
        print(f"   Date: {nv['scheduled_date']}")
        print(f"   In {nv['days_until']} days")
    else:
        print(f"\n✅ No upcoming visits within next 14 days")
    
    # Overdue visits
    if schedule_data['overdue_visits']:
        print(f"\n⚠️  OVERDUE VISITS: {len(schedule_data['overdue_visits'])}")
        for ov in schedule_data['overdue_visits']:
            print(f"   Visit #{ov['visit_number']} - Week {ov['week']}")
            print(f"   Was due: {ov['scheduled_date']} ({ov['days_overdue']} days ago)")
    else:
        print(f"\n✅ No overdue visits")
    
    # Full schedule
    print(f"\n📋 COMPLETE SCHEDULE:")
    print(f"{'Visit':<8} {'Week':<6} {'Date':<12} {'Status':<12} {'Days Until':<12}")
    print("-" * 60)
    for visit in schedule_data['anc_schedule']:
        status_icon = {
            'overdue': '⚠️ ',
            'due_now': '🔔',
            'upcoming': '📅',
            'scheduled': '  '
        }.get(visit['status'], '  ')
        
        print(f"#{visit['visit_number']:<7} {visit['week']:<6} {visit['scheduled_date']:<12} "
              f"{status_icon}{visit['status']:<10} {visit['days_until']:>6}")
    
    return True

def test_early_pregnancy():
    """Test: Woman in early pregnancy (8 weeks)."""
    print_header("TEST 1: Early Pregnancy (8 weeks)")
    
    # LMP was 8 weeks ago
    lmp_date = (datetime.datetime.now() - datetime.timedelta(weeks=8)).strftime("%Y-%m-%d")
    print(f"Scenario: Woman with LMP date {lmp_date} (8 weeks ago)")
    print("Expected: First visit is upcoming/due now, rest are scheduled")
    
    result = calculate_anc_schedule(lmp_date)
    success = print_schedule(result)
    
    # Validation
    if success:
        assert result['anc_schedule'][0]['status'] in ['due_now', 'upcoming'], \
            "First visit should be due now or upcoming"
        print("\n✅ TEST PASSED: Early pregnancy schedule calculated correctly")
        return True
    return False

def test_mid_pregnancy():
    """Test: Woman in mid pregnancy (24 weeks)."""
    print_header("TEST 2: Mid Pregnancy (24 weeks)")
    
    # LMP was 24 weeks ago
    lmp_date = (datetime.datetime.now() - datetime.timedelta(weeks=24)).strftime("%Y-%m-%d")
    print(f"Scenario: Woman with LMP date {lmp_date} (24 weeks ago)")
    print("Expected: Some visits overdue, some upcoming")
    
    result = calculate_anc_schedule(lmp_date)
    success = print_schedule(result)
    
    # Validation
    if success:
        assert len(result['overdue_visits']) > 0, "Should have overdue visits"
        print("\n✅ TEST PASSED: Mid pregnancy schedule calculated correctly")
        return True
    return False

def test_late_pregnancy():
    """Test: Woman in late pregnancy (38 weeks)."""
    print_header("TEST 3: Late Pregnancy (38 weeks)")
    
    # LMP was 38 weeks ago
    lmp_date = (datetime.datetime.now() - datetime.timedelta(weeks=38)).strftime("%Y-%m-%d")
    print(f"Scenario: Woman with LMP date {lmp_date} (38 weeks ago)")
    print("Expected: Most visits overdue, final visits upcoming")
    
    result = calculate_anc_schedule(lmp_date)
    success = print_schedule(result)
    
    # Validation
    if success:
        assert len(result['overdue_visits']) >= 5, "Should have multiple overdue visits"
        print("\n✅ TEST PASSED: Late pregnancy schedule calculated correctly")
        return True
    return False

def test_specific_date():
    """Test: Specific LMP date (2025-03-01)."""
    print_header("TEST 4: Specific Date (2025-03-01)")
    
    lmp_date = "2025-03-01"
    print(f"Scenario: Woman with LMP date {lmp_date}")
    print("Expected: Schedule calculated with specific dates")
    
    result = calculate_anc_schedule(lmp_date)
    success = print_schedule(result)
    
    # Validation
    if success:
        # Check that all 8 visits are present
        assert len(result['anc_schedule']) == 8, "Should have exactly 8 ANC visits"
        
        # Check that visit weeks are correct
        expected_weeks = [10, 20, 26, 30, 34, 36, 38, 40]
        actual_weeks = [v['week'] for v in result['anc_schedule']]
        assert actual_weeks == expected_weeks, f"Visit weeks should be {expected_weeks}"
        
        print("\n✅ TEST PASSED: Specific date schedule calculated correctly")
        return True
    return False

def test_invalid_date_format():
    """Test: Invalid date format."""
    print_header("TEST 5: Invalid Date Format")
    
    lmp_date = "01-03-2025"  # Wrong format
    print(f"Scenario: Invalid date format '{lmp_date}'")
    print("Expected: Error message about date format")
    
    result = calculate_anc_schedule(lmp_date)
    
    if result['status'] == 'error':
        print(f"\n✅ Error correctly caught: {result['error_message']}")
        print("✅ TEST PASSED: Invalid date format handled correctly")
        return True
    else:
        print("\n❌ TEST FAILED: Should have returned error for invalid format")
        return False

def test_future_date():
    """Test: Future LMP date (should still work)."""
    print_header("TEST 6: Future LMP Date")
    
    # LMP in the future (edge case)
    lmp_date = (datetime.datetime.now() + datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    print(f"Scenario: Future LMP date {lmp_date}")
    print("Expected: Schedule calculated (all visits in future)")
    
    result = calculate_anc_schedule(lmp_date)
    success = print_schedule(result)
    
    if success:
        # All visits should be scheduled (in the future)
        future_visits = [v for v in result['anc_schedule'] if v['days_until'] > 7]
        print(f"\n✅ TEST PASSED: Future date handled ({len(future_visits)} scheduled visits)")
        return True
    return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🧪 ANC SCHEDULE CALCULATION - COMPREHENSIVE TESTS")
    print("="*70)
    print("\nTesting calculate_anc_schedule() with various scenarios...")
    
    tests = [
        test_early_pregnancy,
        test_mid_pregnancy,
        test_late_pregnancy,
        test_specific_date,
        test_invalid_date_format,
        test_future_date
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
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
    sys.exit(main())
