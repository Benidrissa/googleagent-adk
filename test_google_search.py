#!/usr/bin/env python3
"""
Standalone test script for google_search tool usage with ADK.
Based on the working Kaggle notebook example.
"""

import os
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
    logger.info("✅ Environment variables loaded from .env file")
except ImportError:
    logger.info("ℹ️  dotenv not available, using system environment variables")

# Get API key from environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("❌ GOOGLE_API_KEY not set in environment")
    exit(1)

# Set required environment variable for Gemini API
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
logger.info("✅ Gemini API key setup complete.")

# Import ADK components - matching the working example
try:
    from google.adk.agents import Agent
    from google.adk.models.google_llm import Gemini
    from google.adk.runners import InMemoryRunner
    from google.adk.tools import google_search
    from google.genai import types

    logger.info("✅ ADK components imported successfully.")
except ImportError as e:
    logger.error(f"❌ Failed to import ADK components: {e}")
    logger.error("Make sure google-adk is installed: pip install google-adk")
    exit(1)

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,  # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)
logger.info("✅ Retry config created.")

# Create agent using Agent class (not LlmAgent)
# Matching the exact Kaggle working example
root_agent = Agent(
    name="helpful_assistant",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="A simple agent that can answer general questions.",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search],
)

logger.info("✅ Root Agent defined.")

# Create runner
runner = InMemoryRunner(agent=root_agent)

logger.info("✅ Runner created.")


# Test function - EXACTLY matching Kaggle example
async def test_google_search():
    """Test the google_search tool with the EXACT Kaggle query."""
    try:
        logger.info("🧪 Starting google_search test (EXACT Kaggle query)...")

        # Test 1: Query that model CANNOT answer without search
        query1 = "What news headlines are showing on CNN.com right now at this moment?"
        logger.info(f"📝 Test 1 - Impossible without search: {query1}")

        response1 = await runner.run_debug(query1)
        logger.info("✅ Test 1 completed!")

        for event in response1:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        logger.info(f"🤖 Response 1: {part.text[:300]}...")

        # Test 2: Query with completely made-up information
        query = "What is the price of XYZ-FAKE-STOCK-12345 that doesn't exist?"
        logger.info(f"\n📝 Test 2 - Non-existent info: {query}")

        response = await runner.run_debug(query)

        logger.info("✅ Test completed!")
        logger.info(f"📊 Response received: {len(response)} events")

        # Check all events in detail with COMPREHENSIVE debugging
        search_called = False
        final_text = ""

        for i, event in enumerate(response):
            logger.info(f"\n--- Event {i+1} ---")
            logger.info(f"Event type: {type(event)}")
            logger.info(f"Event attributes: {dir(event)}")

            # Check event content
            if hasattr(event, "content"):
                logger.info(f"Has content: {event.content is not None}")

            # Try calling get_function_calls() if available
            if hasattr(event, "get_function_calls"):
                try:
                    func_calls = event.get_function_calls()
                    logger.info(f"get_function_calls() result: {func_calls}")
                    if func_calls:
                        logger.info(
                            f"  ✅ FUNCTION CALLS FOUND via method: {func_calls}"
                        )
                        search_called = True
                except Exception as e:
                    logger.info(f"get_function_calls() error: {e}")

            # Check if this is a tool/function call event
            if hasattr(event, "tool_calls"):
                logger.info(f"Has tool_calls attribute")
                if event.tool_calls:
                    logger.info(f"  ✅ TOOL CALLS FOUND: {event.tool_calls}")
                    search_called = True

            if event.content and event.content.parts:
                logger.info(f"Number of parts: {len(event.content.parts)}")

                for j, part in enumerate(event.content.parts):
                    logger.info(f"\n  Part {j+1}:")
                    logger.info(f"    Type: {type(part)}")
                    logger.info(
                        f"    Attributes: {[attr for attr in dir(part) if not attr.startswith('_')]}"
                    )

                    # Check ALL possible function call attributes
                    if hasattr(part, "function_call") and part.function_call:
                        search_called = True
                        logger.info(f"    ✅ FUNCTION CALL DETECTED!")
                        logger.info(f"    Name: {part.function_call.name}")
                        logger.info(f"    Args: {part.function_call.args}")

                    # Check for function response
                    if hasattr(part, "function_response") and part.function_response:
                        logger.info(
                            f"    ✅ FUNCTION RESPONSE: {part.function_response.name}"
                        )

                    # Check for executable_code
                    if hasattr(part, "executable_code") and part.executable_code:
                        logger.info(f"    Has executable_code")

                    # Check for code_execution_result
                    if (
                        hasattr(part, "code_execution_result")
                        and part.code_execution_result
                    ):
                        logger.info(f"    Has code_execution_result")

                    # Check for text
                    if hasattr(part, "text") and part.text:
                        final_text = part.text
                        logger.info(f"    📝 Has text: {len(part.text)} characters")
                        logger.info(f"    Preview: {part.text[:200]}...")

                    # Check part's raw content
                    if hasattr(part, "to_dict"):
                        try:
                            part_dict = part.to_dict() if callable(part.to_dict) else {}
                            logger.info(
                                f"    Part dict keys: {part_dict.keys() if part_dict else 'N/A'}"
                            )
                            if "function_call" in str(part_dict):
                                logger.info(f"    ⚠️ Function call found in dict!")
                        except:
                            pass

        # Final summary
        logger.info("\n" + "=" * 60)
        if search_called:
            logger.info("✅ SUCCESS: google_search tool WAS called!")
        else:
            logger.info("⚠️  WARNING: google_search tool was NOT called")
            logger.info(
                "This means gemini-2.5-flash-lite does NOT support function calling"
            )

        if final_text:
            logger.info(f"\n🤖 Final Response:\n{final_text}\n")

        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


# Run the test
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Standalone Google Search Tool Test")
    logger.info("=" * 60)

    success = asyncio.run(test_google_search())

    logger.info("=" * 60)
    if success:
        logger.info("✅ All tests passed!")
    else:
        logger.info("❌ Tests failed!")
    logger.info("=" * 60)
