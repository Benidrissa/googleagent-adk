#!/usr/bin/env python3
"""
Test evaluation for low-risk pregnancy - normal/routine care scenario.

This test verifies that the agent:
1. Correctly classifies the case as low-risk
2. Provides reassurance and routine care guidance
3. Calculates EDD and ANC schedule
4. Offers general pregnancy advice
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service
from google.adk.sessions import InMemorySessionService


async def test_low_risk():
    """Test low-risk scenario: 28-year-old healthy woman with normal pregnancy."""

    print("\n" + "=" * 80)
    print("TEST: Low-Risk Pregnancy (Normal/Routine Care Scenario)")
    print("=" * 80 + "\n")

    # Initialize session
    session_id = "test_low_risk_001"
    user_id = "test_user_lowrisk"

    try:
        # Get or create session
        session = await session_service.get_or_create_session(session_id, user_id)

        # Test conversation
        user_input = (
            "Hi! I'm 28 years old and just found out I'm pregnant. "
            "My last menstrual period was on March 1st, 2025. "
            "I'm healthy, no medical issues. This is my first pregnancy. "
            "What should I do next?"
        )

        print(f"User Input:\n{user_input}\n")
        print("-" * 80)
        print("Agent Processing...\n")

        # Get agent response
        response = await root_agent.generate_streaming(
            session=session, user_message=user_input
        )

        # Collect full response
        full_response = ""
        async for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                full_response += chunk.text
                print(chunk.text, end="", flush=True)

        print("\n\n" + "-" * 80)
        print("EVALUATION CRITERIA:")
        print("-" * 80)

        # Evaluation criteria
        criteria_met = []
        criteria_failed = []

        # 1. Check for positive/reassuring tone (not alarming for low-risk)
        reassuring_words = [
            "congratulations",
            "normal",
            "healthy",
            "wonderful",
            "great",
            "routine",
            "regular",
            "well",
            "good",
        ]
        reassurance_detected = any(
            word in full_response.lower() for word in reassuring_words
        )

        # Should NOT use high-risk language for low-risk case
        alarm_words = ["emergency", "urgent", "immediately", "dangerous", "critical"]
        alarm_detected = any(word in full_response.lower() for word in alarm_words)

        if reassurance_detected and not alarm_detected:
            criteria_met.append("✅ Appropriate reassuring tone (not alarming)")
        elif alarm_detected:
            criteria_failed.append(
                "❌ Inappropriate alarm language used for low-risk case"
            )
        else:
            criteria_failed.append("⚠️  No reassurance detected")

        # 2. Check if EDD was calculated
        edd_keywords = [
            "due date",
            "estimated delivery",
            "edd",
            "expected delivery",
            "december",
            "dec",
        ]  # March 1 + 280 days ≈ Dec 6
        edd_mentioned = any(
            keyword in full_response.lower() for keyword in edd_keywords
        )

        if edd_mentioned:
            criteria_met.append("✅ Due date calculated/mentioned")
        else:
            criteria_failed.append("❌ Due date NOT calculated")

        # 3. Check if ANC schedule was provided
        anc_keywords = [
            "anc",
            "antenatal",
            "checkup",
            "appointment",
            "visit",
            "schedule",
            "weeks",
            "8 weeks",
            "12 weeks",
            "20 weeks",
        ]
        anc_mentioned = any(
            keyword in full_response.lower() for keyword in anc_keywords
        )

        if anc_mentioned:
            criteria_met.append("✅ ANC schedule/appointments mentioned")
        else:
            criteria_failed.append("❌ ANC schedule NOT mentioned")

        # 4. Check for general pregnancy advice
        advice_keywords = [
            "nutrition",
            "diet",
            "exercise",
            "rest",
            "sleep",
            "vitamins",
            "folic acid",
            "iron",
            "water",
            "hydration",
            "avoid",
            "healthy",
        ]
        advice_given = any(
            keyword in full_response.lower() for keyword in advice_keywords
        )

        if advice_given:
            criteria_met.append("✅ General pregnancy advice provided")
        else:
            criteria_failed.append("❌ General advice NOT provided")

        # 5. Check for next steps/care plan
        next_steps = [
            "clinic" in full_response.lower()
            or "hospital" in full_response.lower()
            or "doctor" in full_response.lower()
            or "midwife" in full_response.lower()
            or "healthcare" in full_response.lower()
            or "facility" in full_response.lower()
        ]

        if any(next_steps):
            criteria_met.append("✅ Healthcare facility/provider mentioned")
        else:
            criteria_failed.append("⚠️  Healthcare facility recommendation not explicit")

        # 6. Check for appropriate risk level communication
        risk_keywords = [
            "low risk",
            "low-risk",
            "normal pregnancy",
            "healthy pregnancy",
        ]
        risk_communicated = any(
            keyword in full_response.lower() for keyword in risk_keywords
        )

        if risk_communicated:
            criteria_met.append("✅ Low-risk status communicated")
        else:
            # Not a failure, but good to mention
            criteria_failed.append("⚠️  Risk level not explicitly stated")

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
            print("\n❌ TEST FAILED - Agent needs improvement in routine care guidance")
            return False

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_low_risk()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
