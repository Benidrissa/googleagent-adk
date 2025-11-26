#!/usr/bin/env python3
"""
Test script for observability implementation with LoggingPlugin.

This script demonstrates comprehensive logging output from the agent
including tool calls, agent transitions, and execution flow.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pregnancy_companion_agent import run_agent_interaction


async def test_observability():
    """
    Test observability with LoggingPlugin.
    
    This will demonstrate comprehensive logging output including:
    - Agent initialization
    - Tool selection and execution
    - Sub-agent delegation (nurse_agent)
    - Response generation
    - Session management
    """
    
    print("\n" + "=" * 80)
    print("OBSERVABILITY TEST - LoggingPlugin Demonstration")
    print("=" * 80 + "\n")
    
    print("📊 The LoggingPlugin will provide detailed logging for:")
    print("  1. Agent initialization and configuration")
    print("  2. Tool selection and execution")
    print("  3. Sub-agent delegation (nurse_agent)")
    print("  4. Response generation")
    print("  5. Session and memory management")
    print("  6. Error handling and retries")
    print("\n" + "-" * 80 + "\n")
    
    # Test Case 1: Basic interaction with tool calls
    print("TEST CASE 1: Basic Interaction with Tool Calls")
    print("-" * 80)
    
    user_id = "+221 77 555 1234"
    session_id = "observability_test_001"
    
    message_1 = (
        "Hello! My name is Aissata, phone +221 77 555 1234. "
        "I'm 25 years old. My last menstrual period was on June 1, 2025. "
        "I live in Dakar, Senegal."
    )
    
    print(f"\n👤 USER MESSAGE:\n{message_1}\n")
    print("🤖 AGENT PROCESSING (watch detailed logs below):\n")
    
    try:
        response_1 = await run_agent_interaction(
            user_input=message_1,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"\n✅ RESPONSE RECEIVED:\n{response_1[:200]}...\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-" * 80 + "\n")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Test Case 2: High-risk scenario with nurse agent delegation
    print("TEST CASE 2: High-Risk Scenario (Nurse Agent Delegation)")
    print("-" * 80)
    
    message_2 = (
        "I'm experiencing severe bleeding and intense abdominal pain. "
        "I feel dizzy and my vision is blurry."
    )
    
    print(f"\n👤 USER MESSAGE:\n{message_2}\n")
    print("🤖 AGENT PROCESSING (watch nurse_agent delegation):\n")
    
    try:
        response_2 = await run_agent_interaction(
            user_input=message_2,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"\n✅ RESPONSE RECEIVED:\n{response_2[:200]}...\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("OBSERVABILITY TEST COMPLETE")
    print("=" * 80)
    print("\n✅ Review the logs above to see:")
    print("  - Tool trajectory (which tools were called)")
    print("  - Agent transitions (root → nurse_agent)")
    print("  - Execution timing")
    print("  - Session state management")
    print("  - Memory operations")
    print("\n")


async def main():
    """Run the observability test."""
    try:
        await test_observability()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n🚀 Starting Observability Test with LoggingPlugin...\n")
    asyncio.run(main())
