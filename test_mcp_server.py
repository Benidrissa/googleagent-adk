#!/usr/bin/env python3
"""
Test script for Pregnancy MCP Server.
Tests all MCP tools with various scenarios.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Any, Dict

def print_header(title: str):
    """Print formatted test header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

async def test_mcp_server_basic():
    """Test basic MCP server functionality."""
    print_header("TEST 1: MCP Server Tool Listing")
    
    # For now, we'll test that the server can be imported
    try:
        import pregnancy_mcp_server
        print("✅ MCP server module imported successfully")
        
        # Check that required functions exist
        assert hasattr(pregnancy_mcp_server, 'app'), "Server app should exist"
        assert hasattr(pregnancy_mcp_server, 'list_tools'), "list_tools should exist"
        assert hasattr(pregnancy_mcp_server, 'call_tool'), "call_tool should exist"
        
        print("✅ All required functions present")
        print("\n✅ TEST PASSED: MCP server structure is correct")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_listing():
    """Test that tools are properly defined."""
    print_header("TEST 2: Tool Definitions")
    
    try:
        import pregnancy_mcp_server
        
        # Get tools
        tools = await pregnancy_mcp_server.list_tools()
        
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description[:60]}...")
        
        # Check expected tools
        tool_names = [t.name for t in tools]
        expected_tools = [
            "get_pregnancy_by_phone",
            "upsert_pregnancy_record",
            "list_active_pregnancies",
            "update_anc_visit",
            "delete_pregnancy_record"
        ]
        
        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"
            print(f"   ✓ {expected}")
        
        print("\n✅ TEST PASSED: All expected tools defined")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_get_pregnancy_record():
    """Test retrieving pregnancy record."""
    print_header("TEST 3: Get Pregnancy Record")
    
    try:
        import pregnancy_mcp_server
        
        # Test getting existing record
        print("1️⃣ Getting existing record...")
        result = await pregnancy_mcp_server.get_pregnancy_by_phone({
            "phone": "+1234567890"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Name: {response['record']['name']}")
        assert response['status'] == 'success'
        assert response['record']['name'] == 'Sarah Johnson'
        print("   ✅ Existing record retrieved")
        
        # Test getting non-existent record
        print("\n2️⃣ Getting non-existent record...")
        result = await pregnancy_mcp_server.get_pregnancy_by_phone({
            "phone": "+9999999999"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        assert response['status'] == 'not_found'
        print("   ✅ Non-existent record handled correctly")
        
        print("\n✅ TEST PASSED: Get pregnancy record works")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_upsert_pregnancy_record():
    """Test creating and updating pregnancy records."""
    print_header("TEST 4: Upsert Pregnancy Record")
    
    try:
        import pregnancy_mcp_server
        
        # Test creating new record
        print("1️⃣ Creating new record...")
        result = await pregnancy_mcp_server.upsert_pregnancy_record({
            "phone": "+3456789012",
            "name": "Grace Mensah",
            "lmp_date": "2025-01-05",
            "age": 32,
            "location": "Accra",
            "country": "Ghana"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Operation: {response['operation']}")
        print(f"   Name: {response['record']['name']}")
        assert response['status'] == 'success'
        assert response['operation'] == 'created'
        print("   ✅ New record created")
        
        # Test updating existing record
        print("\n2️⃣ Updating existing record...")
        result = await pregnancy_mcp_server.upsert_pregnancy_record({
            "phone": "+3456789012",
            "name": "Grace Mensah-Updated",
            "lmp_date": "2025-01-05",
            "risk_level": "moderate"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Operation: {response['operation']}")
        print(f"   Name: {response['record']['name']}")
        print(f"   Risk: {response['record']['risk_level']}")
        assert response['status'] == 'success'
        assert response['operation'] == 'updated'
        assert response['record']['name'] == 'Grace Mensah-Updated'
        print("   ✅ Record updated")
        
        print("\n✅ TEST PASSED: Upsert operations work")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_list_active_pregnancies():
    """Test listing pregnancy records."""
    print_header("TEST 5: List Active Pregnancies")
    
    try:
        import pregnancy_mcp_server
        
        # List active records
        print("1️⃣ Listing active pregnancies...")
        result = await pregnancy_mcp_server.list_active_pregnancies({
            "status": "active"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Count: {response['count']}")
        assert response['status'] == 'success'
        assert response['count'] >= 2  # At least sample records
        print("   ✅ Active records listed")
        
        # List all records
        print("\n2️⃣ Listing all pregnancies...")
        result = await pregnancy_mcp_server.list_active_pregnancies({
            "status": "all"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Total Count: {response['count']}")
        assert response['status'] == 'success'
        print("   ✅ All records listed")
        
        print("\n✅ TEST PASSED: List operations work")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_update_anc_visit():
    """Test updating ANC visit status."""
    print_header("TEST 6: Update ANC Visit")
    
    try:
        import pregnancy_mcp_server
        
        print("1️⃣ Marking visit as completed...")
        result = await pregnancy_mcp_server.update_anc_visit({
            "phone": "+1234567890",
            "visit_number": 1,
            "completed_date": "2025-11-20",
            "notes": "Normal checkup, all vitals good"
        })
        
        response = json.loads(result[0].text)
        print(f"   Status: {response['status']}")
        print(f"   Message: {response['message']}")
        assert response['status'] == 'success'
        print("   ✅ Visit marked as completed")
        
        print("\n✅ TEST PASSED: ANC visit update works")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🧪 PREGNANCY MCP SERVER - COMPREHENSIVE TESTS")
    print("="*70)
    print("\nTesting MCP server implementation...")
    
    tests = [
        test_mcp_server_basic,
        test_tool_listing,
        test_get_pregnancy_record,
        test_upsert_pregnancy_record,
        test_list_active_pregnancies,
        test_update_anc_visit
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(await test_func())
        except Exception as e:
            print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("  📊 TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ✅")
        return 0
    else:
        print(f"\n⚠️ {total - passed} TEST(S) FAILED ❌")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
