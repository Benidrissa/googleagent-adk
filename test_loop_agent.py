#!/usr/bin/env python3
"""
Test script for ANC Reminder LoopAgent
Tests the LoopAgent structure and sub-agent configuration.
"""

import asyncio
import sys
from anc_reminder_loop_agent import (
    create_check_schedule_agent,
    create_send_reminder_agent,
    create_anc_reminder_loop_agent,
    run_loop_agent_check,
    loop_agent_reminder_handler
)

def print_header(title):
    """Print a formatted test header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

async def test_check_schedule_agent():
    """Test: Check Schedule Agent creation."""
    print_header("TEST 1: Check Schedule Agent")
    
    try:
        agent = create_check_schedule_agent()
        
        print(f"✅ Agent created: {agent.name}")
        print(f"   • Model: {agent.model}")
        print(f"   • Tools: {len(agent.tools)}")
        print(f"   • Temperature: {agent.generate_content_config.temperature}")
        
        assert agent.name == "ANC_Schedule_Checker", "Agent name should be correct"
        assert len(agent.tools) > 0, "Should have tools"
        assert agent.model == "gemini-2.0-flash-exp", "Should use correct model"
        
        print("\n✅ TEST PASSED: Check Schedule Agent configured correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_send_reminder_agent():
    """Test: Send Reminder Agent creation."""
    print_header("TEST 2: Send Reminder Agent")
    
    try:
        agent = create_send_reminder_agent()
        
        print(f"✅ Agent created: {agent.name}")
        print(f"   • Model: {agent.model}")
        print(f"   • Temperature: {agent.generate_content_config.temperature}")
        print(f"   • Max tokens: {agent.generate_content_config.max_output_tokens}")
        
        assert agent.name == "ANC_Reminder_Sender", "Agent name should be correct"
        assert agent.model == "gemini-2.0-flash-exp", "Should use correct model"
        assert agent.generate_content_config.temperature == 0.7, "Should have higher temperature"
        
        print("\n✅ TEST PASSED: Send Reminder Agent configured correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_loop_agent_creation():
    """Test: LoopAgent creation and structure."""
    print_header("TEST 3: LoopAgent Creation")
    
    try:
        loop_agent = create_anc_reminder_loop_agent(max_iterations=50)
        
        print(f"✅ LoopAgent created: {loop_agent.name}")
        print(f"   • Description: {loop_agent.description}")
        print(f"   • Max iterations: 50")
        print(f"   • Sub-agents: {len(loop_agent.sub_agents)}")
        
        for i, sub_agent in enumerate(loop_agent.sub_agents, 1):
            print(f"      {i}. {sub_agent.name}")
        
        # Validate structure
        assert loop_agent.name == "ANC_Reminder_Loop", "LoopAgent name should be correct"
        assert len(loop_agent.sub_agents) == 2, "Should have 2 sub-agents"
        assert loop_agent.description is not None, "Should have description"
        
        # Check sub-agent names
        sub_agent_names = [a.name for a in loop_agent.sub_agents]
        assert "ANC_Schedule_Checker" in sub_agent_names, "Should have checker agent"
        assert "ANC_Reminder_Sender" in sub_agent_names, "Should have sender agent"
        
        print("\n✅ TEST PASSED: LoopAgent structure is correct")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_loop_agent_with_mock_data():
    """Test: LoopAgent processing with mock pregnancy data."""
    print_header("TEST 4: LoopAgent Processing")
    
    try:
        from datetime import datetime, timedelta
        
        # Mock pregnancy data
        mock_data = [
            {
                'phone': '+1234567890',
                'name': 'Test Patient 1',
                'lmp_date': (datetime.now() - timedelta(weeks=10)).strftime('%Y-%m-%d'),
                'location': 'Lagos'
            },
            {
                'phone': '+0987654321',
                'name': 'Test Patient 2',
                'lmp_date': (datetime.now() - timedelta(weeks=25)).strftime('%Y-%m-%d'),
                'location': 'Bamako'
            }
        ]
        
        print(f"📋 Processing {len(mock_data)} pregnancy records...")
        
        result = await run_loop_agent_check(mock_data)
        
        print(f"\n📊 Processing Result:")
        print(f"   • Status: {result['status']}")
        print(f"   • Records processed: {result['records_processed']}")
        print(f"   • LoopAgent: {result.get('loop_agent', 'N/A')}")
        print(f"   • Message: {result.get('message', 'N/A')}")
        
        assert result['status'] == 'success', "Processing should succeed"
        assert result['records_processed'] == 2, "Should process 2 records"
        
        print("\n✅ TEST PASSED: LoopAgent processing works")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_reminder_handler():
    """Test: LoopAgent reminder handler."""
    print_header("TEST 5: Reminder Handler")
    
    try:
        # Mock reminder
        mock_reminder = {
            'type': 'upcoming',
            'record': {
                'phone': '+1234567890',
                'name': 'Test Patient',
                'location': 'Lagos'
            },
            'visit': {
                'visit_number': 1,
                'scheduled_date': '2025-12-01',
                'days_until': 7
            },
            'message': 'Test reminder message'
        }
        
        print("📨 Testing reminder handler...")
        await loop_agent_reminder_handler(mock_reminder)
        
        print("✅ Reminder handler executed successfully")
        
        print("\n✅ TEST PASSED: Reminder handler works")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_instructions():
    """Test: Verify agent instructions are comprehensive."""
    print_header("TEST 6: Agent Instructions")
    
    try:
        loop_agent = create_anc_reminder_loop_agent()
        check_agent = create_check_schedule_agent()
        send_agent = create_send_reminder_agent()
        
        print("📝 Analyzing agent instructions...")
        
        # Check LoopAgent description
        assert loop_agent.description is not None, "LoopAgent should have description"
        assert len(loop_agent.description) > 10, "Description should be meaningful"
        assert "reminder" in loop_agent.description.lower(), "Should mention reminders"
        print("   ✅ LoopAgent description is clear")
        
        # Check Schedule Checker instruction
        assert check_agent.instruction is not None, "Check agent should have instruction"
        assert "schedule" in check_agent.instruction.lower(), "Should mention schedule"
        assert "calculate" in check_agent.instruction.lower(), "Should mention calculation"
        print("   ✅ Schedule Checker instruction is clear")
        
        # Check Reminder Sender instruction
        assert send_agent.instruction is not None, "Send agent should have instruction"
        assert "empathetic" in send_agent.instruction.lower() or "compassionate" in send_agent.instruction.lower(), \
            "Should emphasize empathy"
        assert "reminder" in send_agent.instruction.lower(), "Should mention reminders"
        print("   ✅ Reminder Sender instruction is empathetic")
        
        print("\n✅ TEST PASSED: All agent instructions are comprehensive")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🧪 ANC REMINDER LOOP AGENT - COMPREHENSIVE TESTS")
    print("="*70)
    print("\nTesting LoopAgent structure and configuration...")
    
    tests = [
        test_check_schedule_agent,
        test_send_reminder_agent,
        test_loop_agent_creation,
        test_loop_agent_with_mock_data,
        test_reminder_handler,
        test_agent_instructions
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(await test_func())
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
    sys.exit(asyncio.run(main()))
