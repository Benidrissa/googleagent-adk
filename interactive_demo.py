#!/usr/bin/env python3
"""
Interactive command-line demo for the Pregnancy Companion Agent.
Allows users to chat with the agent in real-time.
"""

import asyncio
import sys
from datetime import datetime
from pregnancy_companion_agent import run_agent_interaction

BANNER = """
╔═══════════════════════════════════════════════════════════════════════╗
║        🤰 PREGNANCY COMPANION AGENT - Interactive Demo 🤰              ║
║                                                                       ║
║  Your AI companion for maternal health in West Africa                ║
║  Features: EDD calculation, location services, health facility finder║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

TIPS = """
💡 Tips:
  • Ask about your expected delivery date (EDD)
  • Request nearby health facilities
  • Get nutrition advice for your region
  • Ask emergency questions
  • Type 'quit' or 'exit' to end
"""

async def interactive_chat():
    """Main interactive chat loop."""
    user_id = "interactive_user"
    session_id = f"interactive_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(BANNER)
    print(TIPS)
    print("="*70)
    print(f"\n🔑 Session ID: {session_id}")
    print(f"👤 User ID: {user_id}\n")
    print("="*70)
    
    # Initial greeting from agent
    print("\n🤖 Agent: Hello! I'm your Pregnancy Companion Agent. I'm here to support")
    print("         you through your pregnancy journey with personalized guidance.")
    print("         Please tell me your name, location, and when your last menstrual")
    print("         period (LMP) was, and I'll help you with your pregnancy care.\n")
    print("-"*70)
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            try:
                user_input = input("\n💬 You: ").strip()
            except EOFError:
                print("\n\n👋 Session ended. Take care!")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n👋 Agent: Take care! Remember to attend your prenatal appointments.")
                print("          Wishing you a healthy pregnancy! 💚\n")
                break
            
            # Show thinking indicator
            print("\n🤔 Agent is thinking...", flush=True)
            
            # Get agent response
            try:
                response = await run_agent_interaction(
                    user_input=user_input,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Display response
                print(f"\n🤖 Agent: {response}\n")
                print("-"*70)
                
                conversation_count += 1
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'quit' to exit.\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Take care!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Please try again or type 'quit' to exit.\n")
    
    print(f"\n📊 Session Summary:")
    print(f"   Total interactions: {conversation_count}")
    print(f"   Session ID: {session_id}")
    print("\n" + "="*70 + "\n")

def main():
    """Entry point for the interactive demo."""
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
