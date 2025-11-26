#!/usr/bin/env python3
"""
Test evaluation for missing LMP date - data collection scenario.

This test verifies that the agent:
1. Detects missing LMP information
2. Asks for LMP date politely
3. Validates date format (YYYY-MM-DD)
4. Handles alternative dating methods (ultrasound)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service
from google.adk.sessions import InMemorySessionService


async def test_missing_lmp():
    """Test data collection: Patient doesn't provide LMP date initially."""

    print("\n" + "=" * 80)
    print("TEST: Missing LMP Date (Data Collection Scenario)")
    print("=" * 80 + "\n")

    # Initialize session
    session_id = "test_missing_lmp_001"
    user_id = "test_user_lmp"

    try:
        # Get or create session
        session = await session_service.get_or_create_session(session_id, user_id)

        # Test conversation - Part 1: Initial message without LMP
        user_input_1 = "Hello! I just found out I'm pregnant and I need help."

        print(f"User Input (Part 1):\n{user_input_1}\n")
        print("-" * 80)
        print("Agent Processing...\n")

        # Get agent response
        response_1 = await root_agent.generate_streaming(
            session=session, user_message=user_input_1
        )

        # Collect full response
        full_response_1 = ""
        async for chunk in response_1:
            if hasattr(chunk, "text") and chunk.text:
                full_response_1 += chunk.text
                print(chunk.text, end="", flush=True)

        print("\n\n" + "-" * 80)

        # Brief pause for natural conversation flow
        await asyncio.sleep(1)

        # Test conversation - Part 2: Provide LMP date
        user_input_2 = "My last menstrual period started on March 1st, 2025."

        print(f"\nUser Input (Part 2):\n{user_input_2}\n")
        print("-" * 80)
        print("Agent Processing...\n")

        # Get agent response for part 2
        response_2 = await root_agent.generate_streaming(
            session=session, user_message=user_input_2
        )

        # Collect full response
        full_response_2 = ""
        async for chunk in response_2:
            if hasattr(chunk, "text") and chunk.text:
                full_response_2 += chunk.text
                print(chunk.text, end="", flush=True)

        print("\n\n" + "-" * 80)
        print("EVALUATION CRITERIA:")
        print("-" * 80)

        # Evaluation criteria
        criteria_met = []
        criteria_failed = []

        # 1. Check if agent asked for LMP in first response
        lmp_questions = [
            "last menstrual period",
            "lmp",
            "last period",
            "when was your last period",
            "first day of your last period",
            "date of your last period",
        ]
        lmp_asked = any(phrase in full_response_1.lower() for phrase in lmp_questions)

        if lmp_asked:
            criteria_met.append("✅ Agent asked for LMP date")
        else:
            criteria_failed.append("❌ Agent did NOT ask for LMP date")

        # 2. Check for polite/supportive tone in initial response
        supportive_words = [
            "congratulations",
            "happy",
            "help",
            "support",
            "guide",
            "assist",
        ]
        supportive_tone = any(
            word in full_response_1.lower() for word in supportive_words
        )

        if supportive_tone:
            criteria_met.append("✅ Supportive/positive tone detected")
        else:
            criteria_failed.append("❌ Supportive tone NOT detected")

        # 3. Check if agent mentioned date format or alternative methods
        format_guidance = [
            "format" in full_response_1.lower()
            or "yyyy-mm-dd" in full_response_1.lower()
            or "ultrasound" in full_response_1.lower()
            or "scan" in full_response_1.lower()
        ]

        if any(format_guidance):
            criteria_met.append("✅ Date format guidance or alternatives mentioned")
        else:
            criteria_failed.append("⚠️  No explicit date format guidance provided")

        # 4. Check if agent processed LMP in second response
        combined_response = full_response_1 + " " + full_response_2
        edd_mentioned = any(
            phrase in combined_response.lower()
            for phrase in [
                "due date",
                "estimated delivery",
                "edd",
                "expected delivery",
                "baby will be born",
                "delivery date",
            ]
        )

        if edd_mentioned:
            criteria_met.append("✅ Agent calculated/mentioned due date")
        else:
            criteria_failed.append("❌ Agent did NOT calculate due date")

        # 5. Check if agent provided next steps after receiving LMP
        next_steps = any(
            phrase in combined_response.lower()
            for phrase in [
                "anc",
                "antenatal",
                "appointment",
                "visit",
                "checkup",
                "schedule",
                "care plan",
                "next step",
            ]
        )

        if next_steps:
            criteria_met.append("✅ Next steps/care plan mentioned")
        else:
            criteria_failed.append("❌ Next steps NOT mentioned")

        # Print results
        print("\nCriteria Met:")
        for item in criteria_met:
            print(f"  {item}")

        if criteria_failed:
            print("\nCriteria Failed:")
            for item in criteria_failed:
                print(f"  {item}")

        # Calculate score
        total_criteria = len(criteria_met) + len(criteria_failed)
        score = len(criteria_met) / total_criteria if total_criteria > 0 else 0

        print("\n" + "=" * 80)
        print(f"SCORE: {len(criteria_met)}/{total_criteria} ({score*100:.1f}%)")
        print("=" * 80)

        # Test passes if at least 3 out of 5 criteria met (60%)
        if score >= 0.6:
            print("\n✅ TEST PASSED")
            return True
        else:
            print("\n❌ TEST FAILED - Agent needs improvement in data collection")
            return False

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_missing_lmp()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
