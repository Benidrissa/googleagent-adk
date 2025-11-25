#!/usr/bin/env python3
"""
Test the pregnancy companion agent implementation with gemini-2.5-flash-lite.
Simplified version without nested agents to validate FunctionTool pattern works.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment for Gemini API
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

# Import everything from the companion agent
from pregnancy_companion_agent import (
    calculate_edd,
    calculate_anc_schedule,
    assess_road_accessibility,
    google_search,
    FunctionTool,
    retry_config,
    MODEL_NAME,
)
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

logger.info("✅ Imports successful")

# Create a simplified agent WITHOUT nested agents for testing
test_agent = LlmAgent(
    name="pregnancy_test",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a pregnancy care assistant.

When users provide their LMP date:
1. Use the calculate_edd tool with the date in YYYY-MM-DD format
2. Provide clear information about pregnancy progress

When users ask about ANC visits:
1. Use the calculate_anc_schedule tool with the LMP date
2. Explain the visit schedule clearly

Keep responses friendly and informative.
""",
    tools=[
        FunctionTool(func=calculate_edd),
        FunctionTool(func=calculate_anc_schedule),
        FunctionTool(func=assess_road_accessibility),
        google_search,
    ],
)

logger.info("✅ Test Agent created")


async def test_companion_functions():
    """Test pregnancy companion functions with gemini-2.5-flash-lite."""

    print("\n" + "=" * 80)
    print("Testing Pregnancy Companion Functions with gemini-2.5-flash-lite")
    print("=" * 80 + "\n")

    runner = InMemoryRunner(agent=test_agent)

    test_cases = [
        "My LMP was 2025-05-01. When is my baby due?",
        "My LMP was May 1st 2025. When are my ANC visits scheduled?",
        "What foods should I eat during pregnancy?",  # Should use google_search
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"--- Test {i} ---")
        print(f"👤 USER: {query}\n")

        response = await runner.run_debug(query)

        for event in response:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"🤖 AGENT: {part.text}\n")

        print()


async def main():
    try:
        await test_companion_functions()
        logger.info("✅ All tests completed!")
        return 0
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
