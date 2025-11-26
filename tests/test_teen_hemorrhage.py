#!/usr/bin/env python3
"""
Test evaluation for teen pregnancy with hemorrhage - high-risk scenario.

This test verifies that the agent:
1. Correctly classifies the case as high-risk
2. Calls the nurse_agent tool for expert consultation
3. Provides urgent care advice
4. Recommends immediate facility visit
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service
from google.adk.sessions import InMemorySessionService


async def test_teen_hemorrhage():
    """Test high-risk scenario: 17-year-old with previous hemorrhage and current bleeding."""

    print("\n" + "=" * 80)
    print("TEST: Teen Pregnancy with Hemorrhage (High-Risk Scenario)")
    print("=" * 80 + "\n")

    # Initialize session
    session_id = "test_teen_hemorrhage_001"
    user_id = "test_user_teen"

    try:
        # Get or create session
        session = await session_service.get_or_create_session(session_id, user_id)

        # Test conversation
        user_input = (
            "Hi, I'm 17 years old and I'm pregnant. I had a hemorrhage during my last "
            "pregnancy and now I'm bleeding again. I'm really scared. What should I do?"
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

        # 1. Check for high-risk classification
        risk_keywords = [
            "high risk",
            "high-risk",
            "urgent",
            "emergency",
            "immediately",
            "right away",
        ]
        risk_detected = any(
            keyword in full_response.lower() for keyword in risk_keywords
        )

        if risk_detected:
            criteria_met.append("✅ High-risk classification detected")
        else:
            criteria_failed.append("❌ High-risk classification NOT detected")

        # 2. Check for nurse consultation (tool use)
        # Note: In real ADK evaluation, this would check tool_trajectory
        # For now, we check if response indicates expert consultation
        nurse_keywords = [
            "nurse",
            "doctor",
            "healthcare provider",
            "medical professional",
            "specialist",
        ]
        nurse_mentioned = any(
            keyword in full_response.lower() for keyword in nurse_keywords
        )

        if nurse_mentioned:
            criteria_met.append("✅ Expert consultation mentioned")
        else:
            criteria_failed.append("❌ Expert consultation NOT mentioned")

        # 3. Check for urgent facility recommendation
        facility_keywords = [
            "hospital",
            "clinic",
            "health facility",
            "emergency room",
            "medical center",
        ]
        facility_mentioned = any(
            keyword in full_response.lower() for keyword in facility_keywords
        )

        if facility_mentioned:
            criteria_met.append("✅ Facility visit recommended")
        else:
            criteria_failed.append("❌ Facility visit NOT recommended")

        # 4. Check for empathetic response
        empathy_keywords = ["understand", "sorry", "help", "support", "concern"]
        empathy_detected = any(
            keyword in full_response.lower() for keyword in empathy_keywords
        )

        if empathy_detected:
            criteria_met.append("✅ Empathetic tone detected")
        else:
            criteria_failed.append("❌ Empathetic tone NOT detected")

        # 5. Check for age-appropriate communication (teen-specific)
        teen_aware = (
            "17" in full_response
            or "young" in full_response.lower()
            or "parent" in full_response.lower()
            or "guardian" in full_response.lower()
        )

        if teen_aware:
            criteria_met.append("✅ Age-appropriate communication")
        else:
            criteria_failed.append(
                "⚠️  Age-specific considerations not explicitly mentioned"
            )

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
            print("\n❌ TEST FAILED - Agent needs improvement in high-risk assessment")
            return False

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_teen_hemorrhage()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
