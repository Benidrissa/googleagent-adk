#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone test for google_search tool with ADK Agent
Based on working Kaggle example
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    print("✅ Gemini API key setup complete.")
except Exception as e:
    print(f"🔑 Authentication Error: {e}")
    exit(1)

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types

print("✅ ADK components imported successfully.")

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

# Create agent using Agent class (not LlmAgent)
root_agent = Agent(
    name="helpful_assistant",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="A simple agent that can answer general questions.",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search],
)

print("✅ Root Agent defined.")

# Create runner
runner = InMemoryRunner(agent=root_agent)

print("✅ Runner created.")


async def test_google_search():
    """Test google_search tool functionality"""
    print("\n" + "=" * 60)
    print("Testing google_search tool with Agent")
    print("=" * 60 + "\n")

    # Test query
    query = "What is Agent Development Kit from Google? What languages is the SDK available in?"
    print(f"Query: {query}\n")

    try:
        response = await runner.run_debug(query, verbose=True)
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        return response
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_google_search())
