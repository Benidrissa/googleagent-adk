#!/usr/bin/env python3
"""
Test script for Facilities REST API

Tests the mock REST API server to ensure all endpoints work correctly.
"""

import requests
import time
import subprocess
import sys
import signal
import os


def print_header(title: str):
    """Print formatted test header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def test_api():
    """Test the Facilities REST API."""
    
    base_url = "http://localhost:8080"
    
    print_header("FACILITIES REST API TEST")
    
    # Test 1: Root endpoint
    print("--- TEST 1: Root Endpoint ---\n")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "name" in data, "Missing 'name' in response"
        assert "version" in data, "Missing 'version' in response"
        print(f"✅ Root endpoint OK: {data['name']} v{data['version']}")
        print(f"   Endpoints: {list(data['endpoints'].keys())}\n")
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}\n")
        return False
    
    # Test 2: Get facilities near Lagos
    print("--- TEST 2: Get Facilities near Lagos ---\n")
    try:
        params = {
            "lat": 6.5244,
            "long": 3.3792,
            "radius": 10000
        }
        response = requests.get(f"{base_url}/facilities", params=params, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["status"] == "success", f"Expected success, got {data['status']}"
        assert data["count"] >= 0, "Count should be non-negative"
        assert "facilities" in data, "Missing 'facilities' in response"
        
        print(f"✅ Found {data['count']} facilities near Lagos")
        for facility in data["facilities"][:3]:  # Show first 3
            print(f"   • {facility['name']} ({facility['type']})")
            print(f"     Distance: {facility['distance_meters']}m, Rating: {facility['rating']}⭐")
        print()
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}\n")
        return False
    
    # Test 3: Get facilities with type filter
    print("--- TEST 3: Get Maternity Facilities ---\n")
    try:
        params = {
            "lat": 12.6392,
            "long": -8.0029,
            "radius": 15000,
            "type": "maternity"
        }
        response = requests.get(f"{base_url}/facilities", params=params, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["status"] == "success", f"Expected success, got {data['status']}"
        print(f"✅ Found {data['count']} maternity facilities near Bamako")
        for facility in data["facilities"]:
            assert facility['type'] == 'maternity', f"Expected maternity, got {facility['type']}"
            print(f"   • {facility['name']}")
        print()
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}\n")
        return False
    
    # Test 4: Get facility detail
    print("--- TEST 4: Get Facility Detail ---\n")
    try:
        facility_id = "fac_lag_001"
        response = requests.get(f"{base_url}/facilities/{facility_id}", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["status"] == "success", f"Expected success, got {data['status']}"
        facility = data["facility"]
        assert facility["id"] == facility_id, f"Expected {facility_id}, got {facility['id']}"
        
        print(f"✅ Facility Details for {facility['name']}:")
        print(f"   Type: {facility['type']}")
        print(f"   Address: {facility['address']}")
        print(f"   Staff: {facility['staff_count']}")
        print(f"   Beds: {facility['bed_capacity']}")
        print(f"   Departments: {', '.join(facility['departments'])}")
        print(f"   24/7: {facility['open_24_7']}")
        print(f"   Wheelchair Accessible: {facility['wheelchair_accessible']}\n")
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}\n")
        return False
    
    # Test 5: Invalid coordinates
    print("--- TEST 5: Error Handling (Invalid Latitude) ---\n")
    try:
        params = {
            "lat": 95.0,  # Invalid latitude
            "long": 3.3792,
            "radius": 5000
        }
        response = requests.get(f"{base_url}/facilities", params=params, timeout=5)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        error = response.json()
        assert "detail" in error or "status" in error, "Missing error information"
        print(f"✅ Error handling OK: Invalid latitude rejected\n")
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}\n")
        return False
    
    # Test 6: Facility not found
    print("--- TEST 6: Error Handling (Facility Not Found) ---\n")
    try:
        response = requests.get(f"{base_url}/facilities/invalid_id", timeout=5)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        error = response.json()
        assert "detail" in error or "status" in error, "Missing error information"
        print(f"✅ Error handling OK: Non-existent facility returns 404\n")
    except Exception as e:
        print(f"❌ TEST 6 FAILED: {e}\n")
        return False
    
    print_header("TEST SUMMARY")
    print("🎉 ALL TESTS PASSED! ✅\n")
    print("API is ready for integration with OpenApiTool\n")
    return True


if __name__ == "__main__":
    # Start the server in background
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
        success = test_api()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    finally:
        # Stop the server
        print("Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped\n")
