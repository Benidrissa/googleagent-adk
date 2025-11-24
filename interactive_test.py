#!/usr/bin/env python3
"""
Interactive Command-Line Test for Pregnancy Companion Agent

This script provides a user-friendly command-line interface to interact with
the pregnancy companion agent in real-time.
"""

import asyncio
import sys
from datetime import datetime
from pregnancy_companion_agent import run_agent_interaction, APP_NAME

# ANSI color codes for better UX
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_banner():
    """Display welcome banner."""
    banner = f"""
{Colors.HEADER}{'='*70}
    🤰 PREGNANCY COMPANION AGENT - Interactive Test 🤰
{'='*70}{Colors.ENDC}

{Colors.OKCYAN}Welcome! I'm your AI pregnancy companion, designed to support
expectant mothers in West Africa with personalized care guidance.

Features:
  • Calculate Expected Due Date (EDD)
  • Provide nutrition guidance
  • Assess road accessibility for delivery
  • Find nearby health facilities
  • Risk assessment with specialized nurse agent
  • Multi-language support (English, French)

Commands:
  • Type your questions naturally
  • Type 'help' for example questions
  • Type 'exit' or 'quit' to end session
  • Type 'new' to start a new session
{Colors.ENDC}
{'='*70}
"""
    print(banner)


def print_help():
    """Display example questions."""
    help_text = f"""
{Colors.OKGREEN}Example Questions You Can Ask:{Colors.ENDC}

{Colors.BOLD}Getting Started:{Colors.ENDC}
  • "Hi, my name is Aminata and I'm from Mali"
  • "I am 28 years old and pregnant for the first time"

{Colors.BOLD}EDD Calculation:{Colors.ENDC}
  • "My last menstrual period was March 1, 2025. When is my baby due?"
  • "What week of pregnancy am I in?"

{Colors.BOLD}Nutrition Guidance:{Colors.ENDC}
  • "What foods should I eat during pregnancy in Mali?"
  • "I need recommendations for iron-rich foods available locally"

{Colors.BOLD}Health Facilities:{Colors.ENDC}
  • "Where are the nearest hospitals in Bamako?"
  • "Can you find health facilities near me in Accra?"

{Colors.BOLD}Road Accessibility:{Colors.ENDC}
  • "I live in a rural area. How accessible are roads for delivery?"
  • "What should I know about traveling to hospital when labor starts?"

{Colors.BOLD}Risk Assessment:{Colors.ENDC}
  • "I have high blood pressure, should I be concerned?"
  • "I'm experiencing severe headaches"
  • "I need to speak to a nurse about complications"

{Colors.BOLD}Multi-language:{Colors.ENDC}
  • "Parlez-vous français?" (The agent can switch to French)
  • "Je suis enceinte de 7 mois"

{'='*70}
"""
    print(help_text)


async def interactive_session():
    """Run interactive chat session with the agent."""
    
    # Generate unique session ID
    session_id = f"interactive_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_id = "interactive_user"
    
    print_banner()
    print(f"{Colors.OKBLUE}Session ID: {session_id}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}User ID: {user_id}{Colors.ENDC}\n")
    
    message_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}You:{Colors.ENDC} ").strip()
            
            # Handle special commands
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print(f"\n{Colors.OKGREEN}Thank you for using Pregnancy Companion Agent!")
                print(f"Total messages: {message_count}")
                print(f"Session ID: {session_id}")
                print(f"Take care! 🤰💚{Colors.ENDC}\n")
                break
                
            if user_input.lower() == 'help':
                print_help()
                continue
                
            if user_input.lower() == 'new':
                session_id = f"interactive_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                message_count = 0
                print(f"\n{Colors.OKGREEN}✅ New session started!{Colors.ENDC}")
                print(f"{Colors.OKBLUE}Session ID: {session_id}{Colors.ENDC}\n")
                continue
            
            # Show thinking indicator
            print(f"\n{Colors.OKCYAN}🤔 Agent is thinking...{Colors.ENDC}")
            
            # Get agent response
            response = await run_agent_interaction(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )
            
            message_count += 1
            
            # Clear thinking indicator and show response
            print(f"\r{' ' * 50}\r", end='')  # Clear line
            print(f"{Colors.BOLD}{Colors.OKGREEN}Agent:{Colors.ENDC} {response}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}Session interrupted by user.{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Total messages: {message_count}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Session ID: {session_id}{Colors.ENDC}\n")
            break
            
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error: {str(e)}{Colors.ENDC}\n")
            print(f"{Colors.WARNING}You can continue chatting or type 'exit' to quit.{Colors.ENDC}\n")


def main():
    """Main entry point."""
    try:
        asyncio.run(interactive_session())
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
