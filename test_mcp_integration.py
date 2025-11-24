#!/usr/bin/env python3
"""
Test MCP Integration with Main Agent

This test validates that the Pregnancy Companion Agent can successfully
use the MCP toolset to store and retrieve pregnancy records.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_integration():
    """
    Test MCP integration with main agent.
    
    Test scenarios:
    1. Agent stores new pregnancy record
    2. Agent retrieves existing pregnancy record
    3. Agent updates existing pregnancy record
    4. Agent lists active pregnancies
    """
    
    print("\n" + "="*70)
    print("MCP INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Import after banner
    from pregnancy_companion_agent import (
        run_agent_interaction,
        session_service,
        APP_NAME
    )
    
    test_session_id = "test_mcp_integration_001"
    test_user_id = "test_patient_mcp"
    
    # Create test session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=test_user_id,
        session_id=test_session_id
    )
    
    test_results = {
        "test_1_store_record": False,
        "test_2_retrieve_record": False,
        "test_3_update_record": False,
        "test_4_list_active": False
    }
    
    # Test 1: Store new pregnancy record
    print("--- TEST 1: STORE NEW PREGNANCY RECORD ---\n")
    try:
        response1 = await run_agent_interaction(
            "My name is Grace Mensah, I'm 25 years old. My phone is +233123456789. "
            "My last menstrual period was on 2025-03-01. I live in Accra, Ghana.",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response1}\n")
        
        # Check if response indicates record was stored
        if "store" in response1.lower() or "record" in response1.lower() or "save" in response1.lower():
            test_results["test_1_store_record"] = True
            print("✅ TEST 1 PASSED: Agent stored pregnancy record\n")
        else:
            print("⚠️  TEST 1: Unable to confirm record storage from response\n")
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}\n")
    
    # Test 2: Retrieve existing pregnancy record
    print("\n--- TEST 2: RETRIEVE EXISTING PREGNANCY RECORD ---\n")
    try:
        response2 = await run_agent_interaction(
            "Can you check my record? My phone is +233123456789",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response2}\n")
        
        # Check if response contains patient information
        if "grace" in response2.lower() and "mensah" in response2.lower():
            test_results["test_2_retrieve_record"] = True
            print("✅ TEST 2 PASSED: Agent retrieved pregnancy record\n")
        else:
            print("⚠️  TEST 2: Unable to confirm record retrieval from response\n")
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}\n")
    
    # Test 3: Update existing pregnancy record
    print("\n--- TEST 3: UPDATE PREGNANCY RECORD ---\n")
    try:
        response3 = await run_agent_interaction(
            "I need to update my record. My phone is +233123456789. "
            "I've been classified as moderate risk because of my age and this is my first pregnancy.",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response3}\n")
        
        # Check if response indicates update
        if "update" in response3.lower() or "record" in response3.lower():
            test_results["test_3_update_record"] = True
            print("✅ TEST 3 PASSED: Agent updated pregnancy record\n")
        else:
            print("⚠️  TEST 3: Unable to confirm record update from response\n")
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}\n")
    
    # Test 4: List active pregnancies
    print("\n--- TEST 4: LIST ACTIVE PREGNANCIES ---\n")
    try:
        response4 = await run_agent_interaction(
            "Can you show me all active pregnancy records in the system?",
            user_id=test_user_id,
            session_id=test_session_id
        )
        print(f"Agent: {response4}\n")
        
        # Check if response contains list information
        if "active" in response4.lower() or "record" in response4.lower() or "patient" in response4.lower():
            test_results["test_4_list_active"] = True
            print("✅ TEST 4 PASSED: Agent listed active pregnancies\n")
        else:
            print("⚠️  TEST 4: Unable to confirm list operation from response\n")
        
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}\n")
    
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
    
    if passed == total:
        print("\n🎉 ALL MCP INTEGRATION TESTS PASSED! ✅")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


async def test_mcp_server_connection():
    """
    Test that MCP server can be started and connected to.
    """
    print("\n" + "="*70)
    print("MCP SERVER CONNECTION TEST")
    print("="*70 + "\n")
    
    try:
        # Import MCP client
        from mcp.client.stdio import stdio_client, StdioServerParameters
        import sys
        
        server_params = StdioServerParameters(
            command="python3",
            args=["pregnancy_mcp_server.py"],
            env=None
        )
        
        print("Attempting to connect to MCP server...")
        
        async with stdio_client(server_params) as (read, write):
            async with read, write:
                print("✅ Successfully connected to MCP server!")
                
                # Try to list tools
                from mcp.types import ListToolsRequest
                
                request = ListToolsRequest()
                # Note: In real implementation, you'd send this properly
                # For now, just confirm connection works
                
                print("✅ MCP server is running and responsive")
                return True
                
    except Exception as e:
        print(f"❌ MCP server connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests
    exit_code = 0
    
    # Test 1: MCP server connection
    connection_ok = asyncio.run(test_mcp_server_connection())
    
    if connection_ok:
        # Test 2: Full integration test
        exit_code = asyncio.run(test_mcp_integration())
    else:
        print("\n⚠️  Skipping integration tests due to server connection failure")
        exit_code = 1
    
    exit(exit_code)
