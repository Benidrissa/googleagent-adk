#!/usr/bin/env python3
"""
Interactive simulation test - demonstrates all tools without requiring GOOGLE_API_KEY.
This simulates what the agent would do without actually calling the LLM.
"""

import asyncio
from datetime import datetime
from pregnancy_companion_agent import (
    calculate_edd,
    infer_country_from_location,
    find_nearby_health_facilities,
    assess_road_accessibility,
    get_local_health_facilities
)

BANNER = """
╔═══════════════════════════════════════════════════════════════════════╗
║     🎭 SIMULATION MODE - Interactive Tool Demo (No API Key Needed)   ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

def parse_user_input(user_input: str):
    """Extract information from user input."""
    info = {
        "name": None,
        "location": None,
        "lmp": None,
        "age": None
    }
    
    # Simple parsing
    if "name" in user_input.lower() or "i'm" in user_input.lower() or "i am" in user_input.lower():
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["i'm", "i am", "name", "called"]:
                if i + 1 < len(words):
                    info["name"] = words[i + 1].strip(".,!?")
                    break
    
    # Location detection
    cities = ["lagos", "bamako", "accra", "abuja", "kumasi"]
    for city in cities:
        if city in user_input.lower():
            info["location"] = city.capitalize()
            break
    
    # LMP detection
    if "lmp" in user_input.lower() or "last menstrual" in user_input.lower():
        words = user_input.split()
        for i, word in enumerate(words):
            if "lmp" in word.lower() or "period" in word.lower():
                # Look for date after
                for j in range(i, min(i+10, len(words))):
                    if any(month in words[j].lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                        date_str = " ".join(words[j:j+3])
                        info["lmp"] = date_str
                        break
    
    return info

def simulate_agent_response(user_input: str, conversation_history: list):
    """Simulate what the agent would respond based on user input."""
    info = parse_user_input(user_input)
    response_parts = []
    
    # Greeting
    if info["name"]:
        response_parts.append(f"Hello {info['name']}! Welcome to your Pregnancy Companion.")
    else:
        response_parts.append("Hello! I'm here to support you through your pregnancy journey.")
    
    # Location-based response
    if info["location"]:
        country_result = infer_country_from_location(info["location"])
        if country_result["status"] == "success":
            country = country_result["country"]
            response_parts.append(f"\nI see you're in {info['location']}, {country}. ")
            
            # Get local facilities
            mcp_result = get_local_health_facilities(info["location"], "emergency")
            if mcp_result["status"] == "success":
                response_parts.append(f"I have information about {mcp_result['count']} emergency facilities in your area.")
    
    # EDD calculation
    if info["lmp"]:
        # Try to parse the date
        try:
            from dateutil import parser
            lmp_date = parser.parse(info["lmp"])
            lmp_str = lmp_date.strftime("%Y-%m-%d")
            
            edd_result = calculate_edd(lmp_str)
            if edd_result["status"] == "success":
                response_parts.append(f"\n\n📅 Based on your LMP of {info['lmp']}:")
                response_parts.append(f"   • Your Expected Delivery Date (EDD) is: {edd_result['edd']}")
                response_parts.append(f"   • You are currently {edd_result['gestational_weeks']} weeks pregnant")
                response_parts.append(f"   • Approximately {edd_result['weeks_remaining']} weeks remaining")
        except:
            response_parts.append("\n\nI'd like to calculate your due date. Please provide your last menstrual period in format like 'January 1, 2025' or '2025-01-01'.")
    
    # Facilities info
    if info["location"] and not info["lmp"]:
        nearby_result = find_nearby_health_facilities(info["location"])
        if nearby_result["status"] == "success":
            response_parts.append(f"\n\n🏥 Nearby Health Facilities:")
            for i, fac in enumerate(nearby_result["facilities"][:3], 1):
                response_parts.append(f"\n   {i}. {fac['name']} ({fac['rating']}⭐)")
                response_parts.append(f"      📍 {fac['address']}")
            
            # Road accessibility
            road_result = assess_road_accessibility(info["location"])
            if road_result["status"] == "success":
                response_parts.append(f"\n\n🚗 Travel Information to Nearest Facility:")
                response_parts.append(f"   • Distance: {road_result['distance']}")
                response_parts.append(f"   • Estimated time: {road_result['duration']}")
    
    # Helpful suggestions
    if not info["lmp"] and info["name"]:
        response_parts.append("\n\n💡 To help you better, please tell me:")
        response_parts.append("   • When was your last menstrual period (LMP)?")
        response_parts.append("   • Are you experiencing any symptoms or concerns?")
    
    return "".join(response_parts)

async def interactive_simulation():
    """Main interactive loop."""
    print(BANNER)
    print("🎭 This is a SIMULATION mode demo - all tools work without API keys!")
    print("💡 The agent will use simulated data for location services.")
    print("📍 Supported cities: Lagos, Bamako, Accra")
    print("\nType 'quit' or 'exit' to end.\n")
    print("="*70)
    
    conversation_history = []
    session_id = f"sim_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n🔑 Session ID: {session_id}")
    print("👤 User ID: simulation_user\n")
    print("="*70)
    
    # Initial greeting
    print("\n🤖 Agent: Hello! I'm your Pregnancy Companion Agent. I'm here to support")
    print("         you through your pregnancy journey with personalized guidance.")
    print("         Please tell me your name, location, and when your last menstrual")
    print("         period (LMP) was, and I'll help you with your pregnancy care.\n")
    print("-"*70)
    
    interaction_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n👋 Agent: Take care! Remember to attend your prenatal appointments.")
                print("          Wishing you a healthy pregnancy! 💚\n")
                break
            
            # Add to history
            conversation_history.append({"role": "user", "content": user_input})
            
            # Show thinking indicator
            print("\n🤔 Agent is processing (using simulated tools)...", flush=True)
            
            # Simulate agent response
            response = simulate_agent_response(user_input, conversation_history)
            
            # Add to history
            conversation_history.append({"role": "agent", "content": response})
            
            # Display response
            print(f"\n🤖 Agent: {response}\n")
            print("-"*70)
            
            interaction_count += 1
            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Take care!")
            break
        except EOFError:
            print("\n\n👋 Session ended. Take care!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.\n")
    
    print(f"\n📊 Session Summary:")
    print(f"   Total interactions: {interaction_count}")
    print(f"   Session ID: {session_id}")
    print(f"   Mode: Simulation (no API keys required)")
    print("\n" + "="*70)
    print("\n✨ All tool calls used simulated data!")
    print("💡 To use real LLM responses, set GOOGLE_API_KEY and run interactive_demo.py\n")

if __name__ == "__main__":
    try:
        asyncio.run(interactive_simulation())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
