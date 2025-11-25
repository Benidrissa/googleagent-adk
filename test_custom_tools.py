#!/usr/bin/env python3
"""
Test script to verify custom function tools work with LlmAgent.
This tests that gemini-2.5-flash-lite can call Python function tools.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# Set environment for Gemini API
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

logger.info("✅ Environment variables loaded from .env file")
logger.info("✅ Gemini API key setup complete.")


# Define custom test tools
def calculate_age(birth_year: int) -> dict:
    """
    Calculate a person's age from their birth year.

    Args:
        birth_year: The year the person was born

    Returns:
        dict: Dictionary containing age and birth_year
    """
    current_year = datetime.now().year
    age = current_year - birth_year

    logger.info(f"🔧 TOOL CALLED: calculate_age(birth_year={birth_year})")

    return {
        "age": age,
        "birth_year": birth_year,
        "current_year": current_year,
        "tool_called": True,
    }


def add_numbers(a: int, b: int) -> dict:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        dict: Dictionary containing the sum
    """
    result = a + b

    logger.info(f"🔧 TOOL CALLED: add_numbers(a={a}, b={b})")

    return {"result": result, "a": a, "b": b, "tool_called": True}


def get_pregnancy_weeks(lmp_date: str) -> dict:
    """
    Calculate pregnancy weeks from Last Menstrual Period (LMP) date.

    Args:
        lmp_date: LMP date in YYYY-MM-DD format

    Returns:
        dict: Dictionary containing pregnancy information
    """
    try:
        lmp = datetime.strptime(lmp_date, "%Y-%m-%d")
        today = datetime.now()
        days_pregnant = (today - lmp).days
        weeks_pregnant = days_pregnant // 7

        logger.info(f"🔧 TOOL CALLED: get_pregnancy_weeks(lmp_date={lmp_date})")

        return {
            "weeks_pregnant": weeks_pregnant,
            "days_pregnant": days_pregnant,
            "lmp_date": lmp_date,
            "tool_called": True,
        }
    except ValueError as e:
        return {"error": f"Invalid date format: {e}", "tool_called": True}


async def test_custom_tools():
    """Test custom Python function tools with LlmAgent."""

    print("\n" + "=" * 80)
    print("TEST: Custom Python Function Tools with LlmAgent")
    print("Model: gemini-2.5-flash-lite")
    print("=" * 80 + "\n")

    # Create agent with custom tools
    test_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite"),
        name="test_agent",
        description="Test agent that can perform calculations and process dates",
        instruction="""
You are a helpful assistant with access to calculation tools.

When users ask you to:
- Calculate someone's age: Use the `calculate_age` tool with their birth year
- Add numbers: Use the `add_numbers` tool
- Calculate pregnancy weeks: Use the `get_pregnancy_weeks` tool with the LMP date

Always use the appropriate tool when the user's question requires it.
Provide clear, friendly responses based on the tool results.
""",
        tools=[calculate_age, add_numbers, get_pregnancy_weeks],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=512,
        ),
    )

    logger.info("✅ Test Agent created with custom tools")

    # Create runner
    runner = InMemoryRunner(agent=test_agent)
    logger.info("✅ Runner created")

    # Test cases
    test_cases = [
        {
            "name": "Age Calculation",
            "query": "I was born in 1990. How old am I?",
            "expected_tool": "calculate_age",
            "expected_keywords": [
                "age",
                "1990",
                "35",
                "34",
            ],  # Could be 34 or 35 depending on birthday
        },
        {
            "name": "Number Addition",
            "query": "What is 47 plus 53?",
            "expected_tool": "add_numbers",
            "expected_keywords": ["100", "47", "53", "sum"],
        },
        {
            "name": "Pregnancy Weeks",
            "query": "My LMP was 2025-05-01. How many weeks pregnant am I?",
            "expected_tool": "get_pregnancy_weeks",
            "expected_keywords": ["weeks", "pregnant", "29", "30"],  # Approximate
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- TEST {i}: {test_case['name']} ---\n")
        print(f"USER: {test_case['query']}\n")

        tool_called = False
        response_text = ""

        try:
            response = await runner.run_debug(test_case["query"])

            for event in response:
                # Check for tool calls
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            tool_called = True
                            logger.info(f"✅ Tool called: {part.function_call.name}")

                        if hasattr(part, "text") and part.text:
                            response_text += part.text

                if event.is_final_response():
                    break

            print(f"AGENT: {response_text}\n")

            # Check results
            keywords_found = [
                kw
                for kw in test_case["expected_keywords"]
                if kw.lower() in response_text.lower()
            ]

            test_result = {
                "name": test_case["name"],
                "tool_called": tool_called,
                "expected_tool": test_case["expected_tool"],
                "keywords_found": keywords_found,
                "response_length": len(response_text),
                "passed": tool_called and len(keywords_found) > 0,
            }

            results.append(test_result)

            if test_result["passed"]:
                print(
                    f"✅ TEST PASSED: Tool was called and response contains relevant keywords"
                )
            else:
                print(
                    f"⚠️  TEST FAILED: Tool called={tool_called}, Keywords found={len(keywords_found)}"
                )

        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            results.append(
                {
                    "name": test_case["name"],
                    "tool_called": False,
                    "error": str(e),
                    "passed": False,
                }
            )

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80 + "\n")

    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)

    for result in results:
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        print(f"{status} - {result['name']}")
        if "error" in result:
            print(f"       Error: {result['error']}")
        elif result.get("tool_called"):
            print(f"       Tool called successfully")
        else:
            print(f"       Tool was NOT called")

    print(f"\n{passed}/{total} tests passed\n")
    print("=" * 80 + "\n")

    return passed == total


async def main():
    """Run all tests."""
    try:
        logger.info("Starting custom tools test...")
        success = await test_custom_tools()

        if success:
            logger.info("✅ All tests passed!")
            return 0
        else:
            logger.error("❌ Some tests failed")
            return 1

    except Exception as e:
        logger.error(f"Test suite failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
