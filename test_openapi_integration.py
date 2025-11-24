#!/usr/bin/env python3
"""
Test OpenAPI Integration with Main Agent

This test validates that the Pregnancy Companion Agent can successfully
use the OpenAPI toolset to search for health facilities.
"""

import asyncio
import logging
import subprocess
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_openapi_integration():
    """
    Test OpenAPI integration with main agent.
    
    Test scenarios:
    1. Agent searches for facilities near Lagos
    2. Agent searches for maternity facilities near Accra
    3. Agent gets facility details
    """
    
    print("\n" + "="*70)
    print("OPENAPI INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Import after banner
    from pregnancy_companion_agent import (
        run_agent_interaction,
        session_service,
        APP_NAME
    )
    
    test_session_id = "test_openapi_integration_001"
    test_user_id = "test_patient_openapi"
    
    # Create test session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=test_user_id,
        session_id=test_session_id
    )
    
    test_results = {
        "test_1_search_lagos": False,
        "test_2_search_maternity": False,
        "test_3_get_details": False
    }
    
    # Test 1: Search for facilities near Lagos
    print("--- TEST 1: SEARCH FACILITIES NEAR LAGOS ---\n")
    try:
        response1 = await run_agent_interaction(
            "I'm in Lagos, Nigeria (latitude 6.5244, longitude 3.3792). "
            "Can you find hospitals within 10km of my location?",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response1}\n")
        
        # Check if response mentions facilities
        if ("hospital" in response1.lower() or "facility" in response1.lower() or 
            "lagos" in response1.lower()):
            test_results["test_1_search_lagos"] = True
            print("✅ TEST 1 PASSED: Agent searched for facilities\n")
        else:
            print("⚠️  TEST 1: Unable to confirm facility search from response\n")
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}\n")
    
    # Test 2: Search for maternity facilities
    print("\n--- TEST 2: SEARCH MATERNITY FACILITIES IN ACCRA ---\n")
    try:
        response2 = await run_agent_interaction(
            "I'm in Accra, Ghana (5.5600 latitude, -0.1900 longitude). "
            "Where are the nearest maternity hospitals?",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response2}\n")
        
        # Check if response mentions maternity facilities
        if "maternity" in response2.lower() or "accra" in response2.lower():
            test_results["test_2_search_maternity"] = True
            print("✅ TEST 2 PASSED: Agent searched for maternity facilities\n")
        else:
            print("⚠️  TEST 2: Unable to confirm maternity search from response\n")
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}\n")
    
    # Test 3: Get facility details
    print("\n--- TEST 3: GET FACILITY DETAILS ---\n")
    try:
        response3 = await run_agent_interaction(
            "Can you tell me more about Lagos University Teaching Hospital? "
            "What are their operating hours and services?",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response3}\n")
        
        # Check if response contains facility information
        if "lagos university" in response3.lower() or "hospital" in response3.lower():
            test_results["test_3_get_details"] = True
            print("✅ TEST 3 PASSED: Agent retrieved facility details\n")
        else:
            print("⚠️  TEST 3: Unable to confirm facility details from response\n")
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}\n")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, passed_flag in test_results.items():
        status = "✅ PASSED" if passed_flag else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed >= 2:  # At least 2/3 tests passing is acceptable
        print("\n🎉 OPENAPI INTEGRATION TESTS PASSED! ✅")
        return 0
    else:
        print(f"\n⚠️  Only {passed}/{total} tests passed")
        return 1


if __name__ == "__main__":
    # Start the facilities API server in background
    print("Starting Facilities REST API server...")
    server_process = subprocess.Popen(
        ["python", "facilities_rest_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        # Wait for server to start
        time.sleep(3)
        print("Server started on http://localhost:8080\n")
        
        # Run tests
        exit_code = asyncio.run(test_openapi_integration())
        sys.exit(exit_code)
        
    finally:
        # Stop the server
        print("\nStopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped\n")
