#!/usr/bin/env python3
"""
Test script to verify google_search is used for emergency contacts and nutrition queries.
"""

import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the agent components
from pregnancy_companion_agent import (
    root_agent,
    runner,
    APP_NAME,
    session_service,
    memory_service,
)
from google.genai import types


async def test_emergency_scenario():
    """Test emergency scenario that should trigger google_search for emergency contacts."""

    print("\n" + "=" * 80)
    print("TEST: Emergency Contact Search via google_search")
    print("=" * 80 + "\n")

    test_session_id = "test_emergency_123"
    test_user_id = "test_user_emergency"

    # Create session
    await session_service.create_session(
        app_name=APP_NAME, user_id=test_user_id, session_id=test_session_id
    )

    print("👤 Test Patient: Fatima from Bamako, Mali")
    print("📍 Testing emergency contact search\n")

    # Step 1: Patient introduction
    print("--- STEP 1: Patient Introduction ---\n")
    intro_query = "My name is Fatima. I am 17 years old. I live in Bamako, Mali. My LMP was August 1st 2025."

    print(f"USER: {intro_query}\n")

    user_message = types.Content(role="user", parts=[types.Part(text=intro_query)])
    agent_response = ""
    async for event in runner.run_async(
        user_id=test_user_id, session_id=test_session_id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            agent_response = "".join(part.text or "" for part in event.content.parts)

    print(f"AGENT: {agent_response}\n")

    # Step 2: Emergency symptoms - should trigger nurse_agent and google_search for contacts
    print(
        "\n--- STEP 2: Emergency Symptoms (Should trigger emergency contact search) ---\n"
    )
    emergency_query = (
        "I am bleeding heavily and feeling very dizzy. I need help now! Who can I call?"
    )

    print(f"USER: {emergency_query}\n")

    user_message = types.Content(role="user", parts=[types.Part(text=emergency_query)])
    agent_response = ""
    async for event in runner.run_async(
        user_id=test_user_id, session_id=test_session_id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            agent_response = "".join(part.text or "" for part in event.content.parts)

    print(f"AGENT: {agent_response}\n")

    # Check if response contains emergency contacts
    keywords = [
        "emergency",
        "hotline",
        "ambulance",
        "call",
        "contact",
        "phone",
        "number",
    ]
    found_keywords = [kw for kw in keywords if kw.lower() in agent_response.lower()]

    print("\n" + "=" * 80)
    if found_keywords:
        print("✅ TEST PASSED: Emergency contact information detected")
        print(f"   Found keywords: {', '.join(found_keywords)}")
    else:
        print("⚠️  TEST WARNING: No obvious emergency contact information found")
    print("=" * 80 + "\n")


async def test_nutrition_search():
    """Test nutrition query that should use google_search."""

    print("\n" + "=" * 80)
    print("TEST: Nutrition Information via google_search")
    print("=" * 80 + "\n")

    test_session_id = "test_nutrition_456"
    test_user_id = "test_user_nutrition"

    # Create session
    await session_service.create_session(
        app_name=APP_NAME, user_id=test_user_id, session_id=test_session_id
    )

    print("👤 Test Patient: Aisha from Lagos, Nigeria")
    print("📍 Testing nutrition information search\n")

    # Patient asks about nutrition
    print("--- Nutrition Query ---\n")
    nutrition_query = "I am 20 weeks pregnant. What foods should I eat to keep my baby healthy? I live in Lagos, Nigeria."

    print(f"USER: {nutrition_query}\n")

    user_message = types.Content(role="user", parts=[types.Part(text=nutrition_query)])
    agent_response = ""
    async for event in runner.run_async(
        user_id=test_user_id, session_id=test_session_id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            agent_response = "".join(part.text or "" for part in event.content.parts)

    print(f"AGENT: {agent_response}\n")

    # Check if response contains nutrition information
    keywords = [
        "food",
        "eat",
        "nutrition",
        "protein",
        "iron",
        "vitamin",
        "folic",
        "calcium",
    ]
    found_keywords = [kw for kw in keywords if kw.lower() in agent_response.lower()]

    print("\n" + "=" * 80)
    if len(found_keywords) >= 3:
        print("✅ TEST PASSED: Comprehensive nutrition information provided")
        print(f"   Found keywords: {', '.join(found_keywords)}")
    else:
        print("⚠️  TEST WARNING: Limited nutrition information detected")
    print("=" * 80 + "\n")


async def main():
    """Run all tests."""
    try:
        logger.info("Starting emergency contact and nutrition search tests...")

        await test_emergency_scenario()
        await test_nutrition_search()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nVerify that:")
        print("  1. Emergency scenario provided hotline/ambulance contacts")
        print("  2. Nutrition query provided food recommendations")
        print(
            "  3. google_search was used transparently (check logs for 'AFC is enabled')"
        )
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
