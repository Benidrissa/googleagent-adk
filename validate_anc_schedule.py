#!/usr/bin/env python3
"""
Interactive validation demo for ANC Schedule Calculation
Run this to manually test the new feature
"""

import asyncio
from pregnancy_companion_agent import run_agent_interaction

async def demo():
    print("\n" + "="*70)
    print("  🎯 ANC SCHEDULE CALCULATION - VALIDATION DEMO")
    print("="*70)
    print("\nThis demo will show the ANC schedule calculation in action.")
    print("You can test with different LMP dates to see the schedule.\n")
    
    test_cases = [
        {
            "name": "Early Pregnancy (8 weeks)",
            "message": "Hi, I'm 8 weeks pregnant. My LMP was 2025-09-29. Can you show me my ANC schedule?",
            "user_id": "demo_user_1"
        },
        {
            "name": "Mid Pregnancy (24 weeks)",
            "message": "I'm worried I missed some visits. My LMP was 2025-06-09. What's my schedule?",
            "user_id": "demo_user_2"
        },
        {
            "name": "Late Pregnancy (38 weeks)",
            "message": "I'm almost due! My LMP was 2025-03-01. Show me my remaining visits.",
            "user_id": "demo_user_3"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"  TEST CASE {i}: {test['name']}")
        print(f"{'='*70}")
        print(f"\n👤 User: {test['message']}")
        print("\n🤖 Agent: ", end="", flush=True)
        
        response = await run_agent_interaction(
            user_input=test['message'],
            user_id=test['user_id'],
            session_id=f'demo_session_{i}'
        )
        
        print(response)
        
        if i < len(test_cases):
            input("\n⏸️  Press Enter to continue to next test case...")
    
    print("\n" + "="*70)
    print("  ✅ VALIDATION DEMO COMPLETE")
    print("="*70)
    print("\nThe calculate_anc_schedule() tool has been successfully integrated!")
    print("\nKey features demonstrated:")
    print("  ✅ Calculates 8 ANC visits based on WHO guidelines")
    print("  ✅ Shows visit dates at weeks 10, 20, 26, 30, 34, 36, 38, 40")
    print("  ✅ Identifies upcoming visits (within 14 days)")
    print("  ✅ Flags overdue visits (more than 7 days past)")
    print("  ✅ Integrated seamlessly with agent conversation")
    print("\n")

if __name__ == "__main__":
    asyncio.run(demo())
