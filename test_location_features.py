"""
Test suite for location-aware features in Pregnancy Companion Agent.
Tests country inference, Google Search, Maps integration, and agent usage.
"""

import asyncio
import logging
from pregnancy_companion_agent import (
    infer_country_from_location,
    find_nearby_health_facilities,
    assess_road_accessibility,
    run_agent_interaction,
    session_service,
    APP_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST: Country Inference
# ============================================================================

def test_country_inference():
    """Test country inference from various location formats."""
    print("\n" + "="*70)
    print("TEST 1: COUNTRY INFERENCE FROM LOCATION")
    print("="*70 + "\n")
    
    test_cases = [
        "Bamako",
        "Ouagadougou, Burkina Faso",
        "Accra, Ghana",
        "Lagos",
        "Paris, France"
    ]
    
    for location in test_cases:
        print(f"Testing location: {location}")
        result = infer_country_from_location(location)
        
        if result["status"] == "success":
            print(f"  ✅ Country: {result['country']}")
            print(f"  📍 Formatted: {result['formatted_location']}")
        else:
            print(f"  ❌ Error: {result['error_message']}")
        print()
    
    print("Country inference test complete.\n")


# ============================================================================
# TEST: Health Facility Search
# ============================================================================

def test_health_facility_search():
    """Test finding nearby health facilities."""
    print("\n" + "="*70)
    print("TEST 2: HEALTH FACILITY SEARCH")
    print("="*70 + "\n")
    
    test_locations = [
        ("Bamako, Mali", 5000),
        ("Accra, Ghana", 10000),
    ]
    
    for location, radius in test_locations:
        print(f"Searching near: {location} (radius: {radius/1000}km)")
        result = find_nearby_health_facilities(location, radius)
        
        if result["status"] == "success":
            print(f"  ✅ Found {result['count']} facilities")
            for i, facility in enumerate(result["facilities"][:3], 1):  # Show top 3
                print(f"  {i}. {facility['name']}")
                print(f"     Address: {facility['address']}")
                print(f"     Rating: {facility.get('rating', 'N/A')}")
                print(f"     Types: {', '.join(facility['types'][:3])}")
        else:
            print(f"  ❌ Error: {result['error_message']}")
        print()
    
    print("Health facility search test complete.\n")


# ============================================================================
# TEST: Road Accessibility
# ============================================================================

def test_road_accessibility():
    """Test road accessibility assessment."""
    print("\n" + "="*70)
    print("TEST 3: ROAD ACCESSIBILITY ASSESSMENT")
    print("="*70 + "\n")
    
    test_routes = [
        ("Bamako city center, Mali", None),  # Will find nearest hospital
        ("Accra, Ghana", "Ridge Hospital, Accra"),
    ]
    
    for origin, destination in test_routes:
        if destination:
            print(f"Route: {origin} → {destination}")
        else:
            print(f"Route: {origin} → [Nearest Hospital]")
        
        result = assess_road_accessibility(origin, destination)
        
        if result["status"] == "success":
            print(f"  ✅ Route found")
            print(f"  📏 Distance: {result['distance']}")
            print(f"  ⏱️  Duration: {result['duration']}")
            print(f"  🚗 Mode: {result['travel_mode']}")
            print(f"  🏥 Destination: {result['end_address']}")
        else:
            print(f"  ❌ Error: {result['error_message']}")
        print()
    
    print("Road accessibility test complete.\n")


# ============================================================================
# TEST: Agent Integration - Location Awareness
# ============================================================================

async def test_agent_location_awareness():
    """Test agent's ability to handle location information."""
    print("\n" + "="*70)
    print("TEST 4: AGENT LOCATION AWARENESS")
    print("="*70 + "\n")
    
    test_user = "test_user_location"
    test_session = "test_session_location"
    
    # Create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=test_user,
        session_id=test_session
    )
    
    # Test 1: Patient provides location
    print("Test 4.1: Patient provides location")
    response1 = await run_agent_interaction(
        "Hi, I'm Sarah from Accra, Ghana. I'm 25 and pregnant.",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent Response: {response1[:200]}...\n")
    
    # Test 2: Patient asks about nutrition (should trigger Google Search)
    print("Test 4.2: Nutrition question (Google Search)")
    response2 = await run_agent_interaction(
        "What foods are good for my pregnancy?",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent Response: {response2[:300]}...\n")
    
    print("Agent location awareness test complete.\n")


# ============================================================================
# TEST: Agent Integration - Emergency with Location
# ============================================================================

async def test_agent_emergency_with_location():
    """Test agent's emergency response with location features."""
    print("\n" + "="*70)
    print("TEST 5: EMERGENCY RESPONSE WITH LOCATION")
    print("="*70 + "\n")
    
    test_user = "test_user_emergency"
    test_session = "test_session_emergency"
    
    # Create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=test_user,
        session_id=test_session
    )
    
    # Setup patient
    print("Setup: Patient introduction with location")
    response1 = await run_agent_interaction(
        "I'm Fatima, 30 years old, from Bamako, Mali. My LMP was 2025-03-01.",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent: {response1[:150]}...\n")
    
    # Emergency situation
    print("Emergency: Patient reports danger signs")
    response2 = await run_agent_interaction(
        "I have severe headache and blurry vision. Where can I get help?",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent Response (should include risk assessment + facilities):")
    print(f"{response2[:500]}...\n")
    
    print("Emergency response test complete.\n")


# ============================================================================
# TEST: Agent Integration - Pre-delivery Planning
# ============================================================================

async def test_agent_predelivery_planning():
    """Test agent's pre-delivery road accessibility features."""
    print("\n" + "="*70)
    print("TEST 6: PRE-DELIVERY PLANNING")
    print("="*70 + "\n")
    
    test_user = "test_user_delivery"
    test_session = "test_session_delivery"
    
    # Create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=test_user,
        session_id=test_session
    )
    
    # Setup patient near due date
    print("Setup: Patient near due date (36 weeks)")
    response1 = await run_agent_interaction(
        "Hi, I'm Aminata from Ouagadougou, Burkina Faso. I'm 28. My LMP was 2024-09-01.",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent: {response1[:150]}...\n")
    
    # Ask about hospital distance
    print("Query: Distance to hospital")
    response2 = await run_agent_interaction(
        "How far is the nearest hospital from me? How long will it take to get there?",
        user_id=test_user,
        session_id=test_session
    )
    print(f"Agent Response (should include route info):")
    print(f"{response2[:400]}...\n")
    
    print("Pre-delivery planning test complete.\n")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all location feature tests."""
    print("\n" + "="*70)
    print("PREGNANCY COMPANION AGENT - LOCATION FEATURES TEST SUITE")
    print("="*70)
    
    try:
        # Test 1: Country Inference (synchronous)
        test_country_inference()
        
        # Test 2: Health Facility Search (synchronous)
        test_health_facility_search()
        
        # Test 3: Road Accessibility (synchronous)
        test_road_accessibility()
        
        # Test 4: Agent Location Awareness (async)
        await test_agent_location_awareness()
        
        # Test 5: Emergency Response (async)
        await test_agent_emergency_with_location()
        
        # Test 6: Pre-delivery Planning (async)
        await test_agent_predelivery_planning()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETE")
        print("="*70)
        print("\n✅ Test Summary:")
        print("  1. Country inference from locations - TESTED")
        print("  2. Health facility search - TESTED")
        print("  3. Road accessibility assessment - TESTED")
        print("  4. Agent location awareness - TESTED")
        print("  5. Emergency response with locations - TESTED")
        print("  6. Pre-delivery planning - TESTED")
        print("\n⚠️  Note: Tests require valid API keys in .env file")
        print("   - GOOGLE_API_KEY for Gemini and Search")
        print("   - GOOGLE_MAPS_API_KEY for Maps APIs")
        
    except Exception as e:
        logger.error(f"Test suite error: {e}", exc_info=True)
        print(f"\n❌ Test suite failed with error: {e}")


if __name__ == "__main__":
    print("\n🧪 Starting Location Features Test Suite...\n")
    asyncio.run(run_all_tests())
