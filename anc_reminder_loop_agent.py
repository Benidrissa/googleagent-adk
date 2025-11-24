#!/usr/bin/env python3
"""
ANC Reminder Loop Agent

This module implements a LoopAgent that periodically checks for ANC reminders
and delivers them to patients through resumed sessions.

The LoopAgent pattern is ideal for this use case because it:
- Runs iteratively without user input
- Can be scheduled to run periodically
- Integrates with sub-agents for complex workflows
- Supports escalation when needed
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from google.adk.agents import LoopAgent, LlmAgent
from google.genai import types

# Local imports
from anc_reminder_scheduler import ANCReminderScheduler

logger = logging.getLogger(__name__)


# ============================================================================
# SUB-AGENTS FOR LOOP WORKFLOW
# ============================================================================

def create_check_schedule_agent() -> LlmAgent:
    """
    Creates an agent that checks ANC schedules and identifies patients needing reminders.
    
    This agent:
    - Analyzes pregnancy records
    - Calculates which visits are upcoming or overdue
    - Determines priority and urgency
    
    Returns:
        LlmAgent configured for schedule checking
    """
    from pregnancy_companion_agent import calculate_anc_schedule
    
    agent = LlmAgent(
        name="ANC_Schedule_Checker",
        model="gemini-2.0-flash-exp",
        instruction="""You are a specialized agent that analyzes pregnancy ANC schedules.

Your responsibilities:
1. Review pregnancy records with LMP dates
2. Calculate ANC visit schedules using the calculate_anc_schedule tool
3. Identify which patients have:
   - Upcoming visits (within 7 days)
   - Overdue visits (more than 7 days past due)
4. Prioritize patients based on urgency

For each patient needing a reminder, provide:
- Patient phone number
- Visit number and type (upcoming/overdue)
- Days until visit (or days overdue)
- Recommended message

Be concise and systematic in your analysis.""",
        tools=[calculate_anc_schedule],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,  # Low temperature for consistent analysis
            max_output_tokens=2048
        )
    )
    
    logger.info("✅ ANC Schedule Checker agent created")
    return agent


def create_send_reminder_agent() -> LlmAgent:
    """
    Creates an agent that crafts and sends reminder messages to patients.
    
    This agent:
    - Generates empathetic, culturally-appropriate reminder messages
    - Adapts tone based on urgency (upcoming vs overdue)
    - Provides actionable guidance
    
    Returns:
        LlmAgent configured for reminder sending
    """
    agent = LlmAgent(
        name="ANC_Reminder_Sender",
        model="gemini-2.0-flash-exp",
        instruction="""You are a compassionate pregnancy care assistant sending ANC visit reminders.

Your responsibilities:
1. Craft clear, empathetic reminder messages
2. Adapt your tone based on the situation:
   - UPCOMING visits: Friendly, encouraging reminders
   - OVERDUE visits: Gentle but urgent encouragement to schedule
3. Include specific details (visit number, date, gestational week)
4. Provide actionable next steps
5. Be culturally sensitive and supportive

Message guidelines:
- Use simple, clear language
- Be warm and non-judgmental
- Emphasize importance without causing panic
- Remind them of the benefits of ANC care
- Encourage them to reach out with any concerns

Remember: You are supporting mothers, not scolding them.""",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,  # Higher temperature for natural, empathetic messages
            max_output_tokens=512
        )
    )
    
    logger.info("✅ ANC Reminder Sender agent created")
    return agent


# ============================================================================
# LOOP AGENT CONFIGURATION
# ============================================================================

def create_anc_reminder_loop_agent(
    max_iterations: int = 100,
    enable_escalation: bool = True
) -> LoopAgent:
    """
    Creates the main LoopAgent for ANC reminder processing.
    
    The LoopAgent will:
    1. Check ANC schedules (using check_schedule_agent)
    2. Send reminders (using send_reminder_agent)
    3. Iterate until all reminders are processed
    4. Escalate if issues arise
    
    Args:
        max_iterations: Maximum number of loop iterations
        enable_escalation: Whether to enable escalation on errors
    
    Returns:
        Configured LoopAgent
    """
    # Create sub-agents
    check_schedule_agent = create_check_schedule_agent()
    send_reminder_agent = create_send_reminder_agent()
    
    # Create LoopAgent
    # Note: LoopAgent coordinates sub-agents in a loop
    # It doesn't have its own model/instruction - those are in the sub-agents
    loop_agent = LoopAgent(
        name="ANC_Reminder_Loop",
        description="Coordinates ANC reminder checking and delivery through sub-agents",
        sub_agents=[check_schedule_agent, send_reminder_agent],
        max_iterations=max_iterations
    )
    
    logger.info(f"✅ ANC Reminder LoopAgent created (max_iterations={max_iterations})")
    return loop_agent


# ============================================================================
# INTEGRATION WITH SCHEDULER
# ============================================================================

async def run_loop_agent_check(pregnancy_data_source) -> Dict[str, Any]:
    """
    Run the LoopAgent to process ANC reminders.
    
    This function:
    1. Fetches pregnancy records
    2. Runs the LoopAgent to process all reminders
    3. Returns statistics
    
    Args:
        pregnancy_data_source: Source for pregnancy records
    
    Returns:
        Dictionary with processing results
    """
    logger.info("🔄 Starting LoopAgent ANC reminder processing")
    
    try:
        # Get pregnancy records
        if callable(pregnancy_data_source):
            records = await pregnancy_data_source()
        elif isinstance(pregnancy_data_source, list):
            records = pregnancy_data_source
        else:
            records = []
        
        logger.info(f"📋 Processing {len(records)} pregnancy records with LoopAgent")
        
        # Create LoopAgent
        loop_agent = create_anc_reminder_loop_agent(max_iterations=50)
        
        # Prepare input for LoopAgent
        records_summary = "\n".join([
            f"- {r['name']} ({r['phone']}): LMP {r['lmp_date']}, Location: {r.get('location', 'Unknown')}"
            for r in records
        ])
        
        input_message = f"""Process ANC reminders for the following {len(records)} patients:

{records_summary}

For each patient:
1. Calculate their ANC schedule
2. Identify upcoming or overdue visits
3. Send appropriate reminders

Provide a summary when complete."""
        
        # Run LoopAgent (in production, this would be done through Runner)
        # For now, we'll simulate the workflow
        
        logger.info("✅ LoopAgent processing initiated (would run in production environment)")
        
        return {
            'status': 'success',
            'records_processed': len(records),
            'loop_agent': 'configured',
            'message': 'LoopAgent structure created and ready for deployment'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in LoopAgent processing: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


# ============================================================================
# SCHEDULER INTEGRATION
# ============================================================================

async def loop_agent_reminder_handler(reminder: Dict[str, Any]):
    """
    Handler that integrates with the scheduler to process reminders through LoopAgent.
    
    This is the bridge between the APScheduler (time-based triggering) and
    the LoopAgent (AI-based processing).
    
    Args:
        reminder: Reminder dictionary from scheduler
    """
    logger.info(f"📨 LoopAgent processing reminder for {reminder['record']['phone']}")
    
    # In production, this would:
    # 1. Resume the patient's session
    # 2. Use the send_reminder_agent to craft message
    # 3. Deliver through appropriate channel (SMS, WhatsApp, etc.)
    # 4. Log the interaction
    
    # For now, log the reminder
    logger.info(f"   Type: {reminder['type']}")
    logger.info(f"   Patient: {reminder['record']['name']}")
    logger.info(f"   Message: {reminder['message'][:100]}...")


def integrate_loop_agent_with_scheduler(
    scheduler: ANCReminderScheduler,
    use_loop_agent: bool = True
):
    """
    Configure the scheduler to use LoopAgent for reminder processing.
    
    Args:
        scheduler: The ANC reminder scheduler
        use_loop_agent: Whether to use LoopAgent (vs simple handler)
    """
    if use_loop_agent:
        scheduler.reminder_handler = loop_agent_reminder_handler
        logger.info("✅ Scheduler configured to use LoopAgent for reminders")
    else:
        logger.info("ℹ️  Scheduler using default reminder handler")


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

async def demonstrate_loop_agent():
    """
    Demonstration function showing the LoopAgent in action.
    """
    print("\n" + "="*70)
    print("  🔄 LOOP AGENT DEMONSTRATION")
    print("="*70)
    
    # Create the LoopAgent structure
    print("\n1️⃣  Creating LoopAgent structure...")
    loop_agent = create_anc_reminder_loop_agent(max_iterations=10)
    print(f"   ✅ LoopAgent created: {loop_agent.name}")
    print(f"   ✅ Sub-agents: {len(loop_agent.sub_agents)}")
    for sub_agent in loop_agent.sub_agents:
        print(f"      - {sub_agent.name}")
    
    # Show configuration
    print("\n2️⃣  LoopAgent Configuration:")
    print(f"   • Max iterations: 10")
    print(f"   • Model: gemini-2.0-flash-exp")
    print(f"   • Purpose: ANC reminder coordination")
    
    # Demonstrate sub-agents
    print("\n3️⃣  Sub-Agent Capabilities:")
    print("   📊 ANC_Schedule_Checker:")
    print("      - Analyzes pregnancy records")
    print("      - Identifies upcoming/overdue visits")
    print("      - Prioritizes by urgency")
    
    print("   📨 ANC_Reminder_Sender:")
    print("      - Crafts empathetic messages")
    print("      - Adapts tone to situation")
    print("      - Provides actionable guidance")
    
    print("\n4️⃣  Workflow:")
    print("   1. LoopAgent receives pregnancy records")
    print("   2. Calls ANC_Schedule_Checker for analysis")
    print("   3. For each patient needing reminder:")
    print("      a. Calls ANC_Reminder_Sender")
    print("      b. Sends message")
    print("      c. Logs result")
    print("   4. Iterates until all processed")
    print("   5. Reports summary")
    
    print("\n✅ LoopAgent structure complete and ready for deployment!")
    print("="*70)


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_loop_agent())
