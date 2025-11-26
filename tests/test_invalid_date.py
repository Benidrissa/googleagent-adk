#!/usr/bin/env python3
"""
Test evaluation for invalid date input - error handling scenario.

This test verifies that the agent:
1. Detects invalid date formats
2. Handles errors gracefully (no crashes)
3. Provides helpful error messages
4. Asks for correct format (YYYY-MM-DD)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service
from google.adk.sessions import InMemorySessionService


async def test_invalid_date():
    """Test error handling: Patient provides invalid or future LMP date."""

    print("\n" + "=" * 80)
    print("TEST: Invalid Date Input (Error Handling Scenario)")
    print("=" * 80 + "\n")

    # Initialize session
    session_id = "test_invalid_date_001"
    user_id = "test_user_invalid"

    try:
        # Get or create session
        session = await session_service.get_or_create_session(session_id, user_id)

        # Test conversation - Part 1: Invalid date format
        user_input_1 = "Hi, I'm pregnant. My last period was yesterday."

        print(f"User Input (Part 1 - Invalid: 'yesterday'):\n{user_input_1}\n")
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

        # Brief pause
        await asyncio.sleep(1)

        # Test conversation - Part 2: Future date (impossible)
        user_input_2 = "Sorry, my LMP was 12/25/2026"

        print(f"\nUser Input (Part 2 - Invalid: Future date):\n{user_input_2}\n")
        print("-" * 80)
        print("Agent Processing...\n")

        response_2 = await root_agent.generate_streaming(
            session=session, user_message=user_input_2
        )

        full_response_2 = ""
        async for chunk in response_2:
            if hasattr(chunk, "text") and chunk.text:
                full_response_2 += chunk.text
                print(chunk.text, end="", flush=True)

        print("\n\n" + "-" * 80)

        # Brief pause
        await asyncio.sleep(1)

        # Test conversation - Part 3: Correct format
        user_input_3 = "Okay, my last menstrual period started on 2025-03-01"

        print(f"\nUser Input (Part 3 - Valid date):\n{user_input_3}\n")
        print("-" * 80)
        print("Agent Processing...\n")

        response_3 = await root_agent.generate_streaming(
            session=session, user_message=user_input_3
        )

        full_response_3 = ""
        async for chunk in response_3:
            if hasattr(chunk, "text") and chunk.text:
                full_response_3 += chunk.text
                print(chunk.text, end="", flush=True)

        print("\n\n" + "-" * 80)
        print("EVALUATION CRITERIA:")
        print("-" * 80)

        # Evaluation criteria
        criteria_met = []
        criteria_failed = []

        # Combine all responses for analysis
        all_responses = full_response_1 + " " + full_response_2 + " " + full_response_3

        # 1. Check for polite error handling (no harsh language)
        polite_words = [
            "could you",
            "please",
            "would you mind",
            "help me understand",
            "clarify",
            "provide",
            "share",
        ]
        rude_words = ["wrong", "incorrect", "error", "invalid", "bad"]

        polite_detected = any(word in all_responses.lower() for word in polite_words)
        harsh_detected = any(word in all_responses.lower() for word in rude_words)

        if polite_detected:
            criteria_met.append("✅ Polite error handling detected")
        else:
            criteria_failed.append("⚠️  Could be more polite in requesting information")

        # 2. Check for date format guidance
        format_guidance = [
            "yyyy-mm-dd" in all_responses.lower()
            or "format" in all_responses.lower()
            or "2025-03-01" in all_responses.lower()
            or "year-month-day" in all_responses.lower()
        ]

        if any(format_guidance):
            criteria_met.append("✅ Date format guidance provided")
        else:
            criteria_failed.append("❌ Date format NOT explicitly explained")

        # 3. Check that agent didn't crash/error out
        error_indicators = [
            "error occurred",
            "crashed",
            "failed to",
            "unable to process",
        ]
        no_crash = not any(
            indicator in all_responses.lower() for indicator in error_indicators
        )

        if no_crash:
            criteria_met.append("✅ No system errors/crashes")
        else:
            criteria_failed.append("❌ System error detected")

        # 4. Check if agent requested clarification for invalid inputs
        clarification_words = [
            "clarify",
            "confirm",
            "verify",
            "check",
            "specific date",
            "exact date",
            "actual date",
        ]
        clarification_asked = any(
            word in (full_response_1 + full_response_2).lower()
            for word in clarification_words
        )

        if clarification_asked:
            criteria_met.append("✅ Clarification requested for invalid input")
        else:
            criteria_failed.append("⚠️  Could explicitly request clarification")

        # 5. Check if agent eventually processed valid date
        success_indicators = ["due date", "edd", "december", "anc", "appointment"]
        success_detected = any(
            indicator in full_response_3.lower() for indicator in success_indicators
        )

        if success_detected:
            criteria_met.append("✅ Valid date processed successfully")
        else:
            criteria_failed.append("❌ Valid date NOT processed")

        # 6. Check for educational tone (explaining why date is needed)
        educational_words = [
            "because",
            "so that",
            "in order to",
            "helps me",
            "allows me",
            "calculate",
            "determine",
            "important",
        ]
        educational_detected = any(
            word in all_responses.lower() for word in educational_words
        )

        if educational_detected:
            criteria_met.append("✅ Educational/explanatory tone")
        else:
            criteria_failed.append("⚠️  Could explain why date is needed")

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

        # Test passes if at least 4 out of 6 criteria met (~67%)
        if score >= 0.67:
            print("\n✅ TEST PASSED")
            return True
        else:
            print("\n❌ TEST FAILED - Agent needs improvement in error handling")
            return False

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_invalid_date()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
