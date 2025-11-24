#!/usr/bin/env python3
"""
Test script to verify all features of the Pregnancy Companion Agent
Run this after setting up your API key to ensure everything works correctly.
"""

import asyncio
import logging
import sys
from pregnancy_companion_agent import (
    run_agent_interaction,
    evaluate_interaction,
    session_service,
    APP_NAME
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_edd_calculation():
    """Test EDD calculation tool"""
    logger.info("Testing EDD calculation...")
    
    response = await run_agent_interaction(
        "My last menstrual period was May 1, 2025. What is my due date?",
        user_id="test_edd"
    )
    
    success = "due" in response.lower() or "edd" in response.lower()
    logger.info(f"EDD Test: {'✅ PASSED' if success else '❌ FAILED'}")
    return success


async def test_risk_assessment():
    """Test nurse agent consultation"""
    logger.info("Testing risk assessment...")
    
    # Create session with patient info
    await run_agent_interaction(
        "My name is Test Patient. I am 17 years old. My LMP was May 1, 2025.",
        user_id="test_risk",
        session_id="test_risk_session"
    )
    
    # Report symptoms
    response = await run_agent_interaction(
        "I am feeling very dizzy and seeing spots in my vision.",
        user_id="test_risk",
        session_id="test_risk_session"
    )
    
    success = any(keyword in response.lower() for keyword in ["risk", "urgent", "clinic", "doctor", "care"])
    logger.info(f"Risk Assessment Test: {'✅ PASSED' if success else '❌ FAILED'}")
    return success


async def test_memory_persistence():
    """Test session memory across turns"""
    logger.info("Testing memory persistence...")
    
    # First turn - provide name
    response1 = await run_agent_interaction(
        "Hello, my name is Memory Test.",
        user_id="test_memory",
        session_id="test_memory_session"
    )
    
    # Second turn - ask for name
    response2 = await run_agent_interaction(
        "What is my name?",
        user_id="test_memory",
        session_id="test_memory_session"
    )
    
    success = "memory test" in response2.lower()
    logger.info(f"Memory Test: {'✅ PASSED' if success else '❌ FAILED'}")
    return success


async def test_safety_discussion():
    """Test that safety settings allow medical discussion"""
    logger.info("Testing safety settings for medical content...")
    
    response = await run_agent_interaction(
        "I have bleeding during pregnancy. What should I do?",
        user_id="test_safety"
    )
    
    # Should not be blocked, should provide guidance
    success = len(response) > 50 and "sorry" not in response.lower()[:100]
    logger.info(f"Safety Settings Test: {'✅ PASSED' if success else '❌ FAILED'}")
    return success


async def test_evaluation():
    """Test evaluation system"""
    logger.info("Testing evaluation system...")
    
    try:
        evaluation = await evaluate_interaction(
            user_input="I feel dizzy",
            agent_response="You should consult a doctor immediately for dizziness during pregnancy.",
            expected_behavior="Should recognize symptom and recommend medical care"
        )
        
        success = "score" in evaluation or "reasoning" in evaluation
        logger.info(f"Evaluation Test: {'✅ PASSED' if success else '❌ FAILED'}")
        return success
    except Exception as e:
        logger.error(f"Evaluation Test: ❌ FAILED - {e}")
        return False


async def test_session_creation():
    """Test session service"""
    logger.info("Testing session creation...")
    
    try:
        test_session_id = "test_session_creation"
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=test_session_id
        )
        
        retrieved = await session_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=test_session_id
        )
        
        success = retrieved is not None and retrieved.id == test_session_id
        logger.info(f"Session Test: {'✅ PASSED' if success else '❌ FAILED'}")
        return success
    except Exception as e:
        logger.error(f"Session Test: ❌ FAILED - {e}")
        return False


async def test_error_handling():
    """Test error handling with invalid input"""
    logger.info("Testing error handling...")
    
    response = await run_agent_interaction(
        "Calculate my EDD from invalid-date-format",
        user_id="test_error"
    )
    
    # Should handle gracefully, not crash
    success = len(response) > 0 and "error" not in response.lower()[:50]
    logger.info(f"Error Handling Test: {'✅ PASSED' if success else '❌ FAILED'}")
    return success


async def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("PREGNANCY COMPANION AGENT - TEST SUITE")
    print("="*70 + "\n")
    
    tests = [
        ("Session Creation", test_session_creation),
        ("EDD Calculation", test_edd_calculation),
        ("Memory Persistence", test_memory_persistence),
        ("Risk Assessment", test_risk_assessment),
        ("Safety Settings", test_safety_discussion),
        ("Evaluation System", test_evaluation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Report results
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print("="*70)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your agent is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)
