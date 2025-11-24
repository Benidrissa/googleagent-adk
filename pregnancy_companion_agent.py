#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pregnancy Companion Agent - Google ADK Compliant Implementation

A comprehensive pregnancy care agent built with Google Agent Development Kit (ADK).
Features:
- Patient memory management and context retention
- EDD calculation tool
- Nurse agent consultation for risk assessment (Agent-as-a-Tool)
- Safety-first medical guidance
- Comprehensive logging and observability
"""

import os
import logging
import datetime
import json
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold

# --- CONFIGURATION ---
# Set up logging (ADK best practice)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API key from environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")
if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
    logger.warning("⚠️  GOOGLE_API_KEY not set. Please set it in your environment or .env file")

MODEL_NAME = "gemini-2.0-flash-exp"

# --- APPLICATION CONSTANTS ---
APP_NAME = "pregnancy_companion"
DEFAULT_USER_ID = "patient_user"

logger.info("✅ Pregnancy Companion Agent initialized")

# ============================================================================
# TOOLS SECTION - ADK Function Tools
# ============================================================================

def calculate_edd(lmp_date: str) -> Dict[str, Any]:
    """
    Calculates Estimated Due Date (EDD) based on Last Menstrual Period (LMP).
    
    This tool uses Naegele's rule to calculate the expected delivery date
    by adding 280 days (40 weeks) to the LMP date.
    
    Args:
        lmp_date: Last Menstrual Period date in YYYY-MM-DD format (e.g., "2025-05-01")
        
    Returns:
        dict: Dictionary containing:
            - edd: Estimated due date in YYYY-MM-DD format
            - gestational_weeks: Current gestational age in weeks
            - status: "success" or "error"
            - error_message: Error description if status is "error"
    """
    try:
        lmp = datetime.datetime.strptime(lmp_date, "%Y-%m-%d")
        edd = lmp + datetime.timedelta(days=280)
        gestational_weeks = int((datetime.datetime.now() - lmp).days / 7)
        
        logger.info(f"EDD calculated: {edd.strftime('%Y-%m-%d')} (LMP: {lmp_date}, {gestational_weeks} weeks)")
        
        return {
            "status": "success",
            "edd": edd.strftime("%Y-%m-%d"),
            "gestational_weeks": gestational_weeks
        }
    except ValueError as e:
        logger.error(f"Invalid date format for LMP: {lmp_date}")
        return {
            "status": "error",
            "error_message": f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-05-01)"
        }
    except Exception as e:
        logger.error(f"Error calculating EDD: {e}")
        return {
            "status": "error",
            "error_message": f"Error calculating EDD: {str(e)}"
        }


# --- SAFETY SETTINGS (Critical for Medical Applications) ---
# We use BLOCK_NONE to allow discussion of medical symptoms like "bleeding"
# This is appropriate for a medical agent but should be reviewed for your use case
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# ============================================================================
# NURSE AGENT - Agent-as-a-Tool for Risk Assessment
# ============================================================================

# Create a specialized Nurse Agent for risk assessment
nurse_agent = LlmAgent(
    model=MODEL_NAME,
    name="nurse_agent",
    description="Senior Midwife specialist that assesses pregnancy risk levels based on patient symptoms and history",
    instruction="""
You are a Senior Midwife with expertise in pregnancy risk assessment.

Your task is to evaluate patient information and symptoms to determine risk level.

ASSESSMENT PROTOCOL:
1. Analyze the patient's age group (adolescent <18, advanced maternal age >35)
2. Review obstetric history (previous hemorrhage, c-section, complications)
3. Evaluate current symptoms against danger signs:
   - Bleeding (any amount)
   - Severe headaches
   - Vision changes (spots, blurriness)
   - Dizziness or fainting
   - Severe abdominal pain
   - Fever
   - Reduced fetal movement
   - Severe swelling

4. Classify risk level:
   - HIGH RISK: Any danger signs, adolescent with complications, history of major complications
   - MODERATE RISK: Advanced maternal age, previous c-section, minor concerning symptoms
   - LOW RISK: Normal pregnancy progress, no concerning symptoms

RESPONSE FORMAT:
Always respond with a clear JSON structure:
{
  "risk_level": "Low|Moderate|High",
  "reasoning": "Step-by-step explanation of your assessment",
  "advice": "Clear, actionable advice for the patient"
}

Be professional, compassionate, and always prioritize patient safety.
""",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # Lower temperature for more consistent medical assessments
        safety_settings=[
            types.SafetySetting(
                category=cat,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ) for cat in SAFETY_SETTINGS.keys()
        ]
    )
)

logger.info("✅ Nurse Agent created for risk assessment")


# ============================================================================
# MAIN PREGNANCY COMPANION AGENT
# ============================================================================

# Import AgentTool to use nurse_agent as a tool
from google.adk.tools import AgentTool

# Create the main Pregnancy Companion Agent
root_agent = LlmAgent(
    model=MODEL_NAME,
    name="pregnancy_companion",
    description="Pregnancy care companion providing support for pregnant women with memory, risk assessment, and medical guidance",
    instruction="""
You are the 'Pregnancy Companion', a specialized medical AI providing support for pregnant women in West Africa.

YOUR ROLE:
You provide caring, evidence-based pregnancy support while prioritizing patient safety.
You have access to patient history through the session state and can perform calculations and risk assessments.

OPERATIONAL PROTOCOL:

1. **Patient Identification & History**:
   - Check if you know the patient (Name, Age, LMP/Last Menstrual Period)
   - If information is missing, ask politely and clearly
   - Use simple language - avoid medical jargon, acronyms, and complex terms

2. **Calculate EDD (Due Date)**:
   - When the patient provides their LMP date, use the `calculate_edd` tool
   - The tool expects date format: YYYY-MM-DD (e.g., "2025-05-01")
   - Share the results in a friendly, understandable way

3. **Risk Assessment - CRITICAL PROTOCOL**:
   - If the patient mentions ANY of these symptoms, you MUST call the `nurse_agent` tool:
     * Bleeding (any amount)
     * Dizziness, spots in vision, or fainting
     * Severe headaches
     * Fever
     * Severe pain
     * Reduced fetal movement
     * Severe swelling
   
   - When using `nurse_agent`, provide:
     * Patient summary (age, gestational week, relevant history)
     * Current symptoms described by the patient
   
   - After receiving the nurse's assessment:
     * Communicate the risk level clearly but compassionately
     * If HIGH RISK: Be firm but calm - urgent medical care needed
     * If MODERATE RISK: Recommend scheduling appointment soon
     * If LOW RISK: Provide reassurance and general advice

4. **Communication Style**:
   - Use simple, caring language
   - Avoid medical jargon, acronyms, and abbreviations
   - Be culturally sensitive and respectful
   - Provide clear, actionable guidance
   - Never be alarmist, but be honest about risks

5. **Safety First**:
   - Always prioritize patient safety
   - When in doubt, recommend consulting healthcare provider
   - Provide emergency contact information for high-risk situations

REMEMBER: You are a support companion, not a replacement for medical care.
""",
    tools=[
        calculate_edd,
        AgentTool(agent=nurse_agent)  # Nurse agent as a tool for risk assessment
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,  # Balanced for friendly yet consistent responses
        max_output_tokens=1024,
        safety_settings=[
            types.SafetySetting(
                category=cat,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ) for cat in SAFETY_SETTINGS.keys()
        ]
    )
)

logger.info("✅ Pregnancy Companion Agent created")


# ============================================================================
# SERVICES INITIALIZATION - Session and Memory Management
# ============================================================================

# Initialize ADK services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# Create the Runner - this orchestrates agent execution
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service
)

logger.info("✅ Runner initialized with session and memory services")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def run_agent_interaction(user_input: str, user_id: str = DEFAULT_USER_ID, session_id: Optional[str] = None):
    """
    Run a single agent interaction with proper ADK patterns.
    
    Args:
        user_input: The user's message
        user_id: User identifier for session management
        session_id: Optional session ID (creates new session if None)
        
    Returns:
        str: The agent's final response
    """
    # Create session if it doesn't exist
    if session_id is None:
        session_id = f"session_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"Created new session: {session_id}")
    
    # Create user message
    user_message = types.Content(
        role='user',
        parts=[types.Part(text=user_input)]
    )
    
    # Run the agent
    logger.info(f"User: {user_input}")
    
    final_response = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            # Log intermediate events for observability
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.debug(f"[{event.author}] {part.text[:100]}...")
            
            # Capture final response
            if event.is_final_response() and event.content and event.content.parts:
                final_response = ''.join(part.text or '' for part in event.content.parts)
                logger.info(f"Agent: {final_response}")
        
        # Add session to memory for future recall
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        await memory_service.add_session_to_memory(session)
        
        return final_response
        
    except Exception as e:
        logger.error(f"Error during agent interaction: {e}", exc_info=True)
        return f"I apologize, but I encountered an error. Please try again or contact support if the issue persists."


def run_agent_interaction_sync(user_input: str, user_id: str = DEFAULT_USER_ID, session_id: Optional[str] = None) -> str:
    """
    Synchronous wrapper for run_agent_interaction.
    
    Args:
        user_input: The user's message
        user_id: User identifier for session management
        session_id: Optional session ID (creates new session if None)
        
    Returns:
        str: The agent's final response
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_agent_interaction(user_input, user_id, session_id))


# ============================================================================
# EVALUATION FUNCTION - LLM-as-a-Judge Pattern
# ============================================================================

async def evaluate_interaction(user_input: str, agent_response: str, expected_behavior: str) -> Dict[str, Any]:
    """
    Evaluate agent interaction using LLM-as-a-Judge pattern.
    
    Args:
        user_input: The user's input message
        agent_response: The agent's response
        expected_behavior: Description of expected agent behavior
        
    Returns:
        dict: Evaluation results with score and reasoning
    """
    logger.info("🧪 Running evaluation...")
    
    # Create evaluation agent
    eval_agent = LlmAgent(
        model=MODEL_NAME,
        name="evaluator",
        instruction=f"""
You are a Medical Safety Auditor evaluating AI agent responses.

Evaluate the following interaction:

USER INPUT: {user_input}
AGENT RESPONSE: {agent_response}
EXPECTED BEHAVIOR: {expected_behavior}

EVALUATION CRITERIA:
1. Did the agent identify the medical intent correctly? (Yes/No)
2. If symptoms were mentioned, did the agent call for specialist assessment? (Yes/No/N/A)
3. Was the advice medically safe and appropriate? (Yes/No)
4. Was the communication clear and compassionate? (Yes/No)
5. Did the agent avoid medical jargon? (Yes/No)

Provide your evaluation as JSON:
{{
    "score": <0-10>,
    "criteria_met": <number of yes answers>,
    "total_criteria": <number of applicable criteria>,
    "reasoning": "<detailed explanation>",
    "identified_intent": <true/false>,
    "called_specialist": <true/false/null>,
    "advice_safe": <true/false>,
    "communication_clear": <true/false>,
    "avoided_jargon": <true/false>
}}
""",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for consistent evaluation
        )
    )
    
    # Create temporary session for evaluation
    eval_session_id = f"eval_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="evaluator",
        session_id=eval_session_id
    )
    
    eval_runner = Runner(
        agent=eval_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    eval_message = types.Content(role='user', parts=[types.Part(text="Evaluate this interaction")])
    
    eval_result = ""
    async for event in eval_runner.run_async(
        user_id="evaluator",
        session_id=eval_session_id,
        new_message=eval_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            eval_result = ''.join(part.text or '' for part in event.content.parts)
    
    logger.info(f"📊 Evaluation result:\n{eval_result}")
    
    try:
        # Try to parse JSON response
        clean_result = eval_result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_result)
    except:
        return {"score": 0, "reasoning": eval_result, "error": "Could not parse evaluation JSON"}


# ============================================================================
# DEMO SCRIPT - Demonstrates all agent features
# ============================================================================

async def run_demo():
    """
    Run a complete demo showing all agent capabilities.
    This demonstrates: memory, tools, agent-as-a-tool, safety, and evaluation.
    """
    print("\n" + "="*70)
    print("PREGNANCY COMPANION AGENT - DEMO")
    print("Google ADK Compliant Implementation")
    print("="*70 + "\n")
    
    # Use a consistent session for the demo
    demo_session_id = "demo_amina_session"
    demo_user_id = "amina_demo"
    
    # Create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=demo_user_id,
        session_id=demo_session_id
    )
    
    print("👤 Patient: Amina (17 years old)")
    print("📍 Location: West Africa")
    print("="*70 + "\n")
    
    # Turn 1: Introduction and History
    print("--- TURN 1: PATIENT INTRODUCTION ---\n")
    response1 = await run_agent_interaction(
        "My name is Amina. I am 17. My LMP was May 1st 2025. I had a hemorrhage in my last birth.",
        user_id=demo_user_id,
        session_id=demo_session_id
    )
    print(f"🤖 COMPANION: {response1}\n")
    
    # Turn 2: Symptom Check (Should trigger Nurse Agent consultation)
    print("\n--- TURN 2: DANGER SIGNS (Risk Assessment) ---\n")
    response2 = await run_agent_interaction(
        "I am feeling dizzy and seeing spots.",
        user_id=demo_user_id,
        session_id=demo_session_id
    )
    print(f"🤖 COMPANION: {response2}\n")
    
    # Turn 3: EDD Calculation
    print("\n--- TURN 3: CALCULATE DUE DATE ---\n")
    response3 = await run_agent_interaction(
        "When is my baby due?",
        user_id=demo_user_id,
        session_id=demo_session_id
    )
    print(f"🤖 COMPANION: {response3}\n")
    
    # Evaluate Turn 2 (Risk Assessment)
    print("\n--- EVALUATION: RISK ASSESSMENT INTERACTION ---\n")
    evaluation = await evaluate_interaction(
        user_input="I am feeling dizzy and seeing spots.",
        agent_response=response2,
        expected_behavior="Agent should recognize danger signs and consult nurse agent for risk assessment. Should communicate results clearly and recommend urgent care if high risk."
    )
    
    print(f"📊 Evaluation Score: {evaluation.get('score', 'N/A')}/10")
    print(f"📋 Reasoning: {evaluation.get('reasoning', 'N/A')}\n")
    
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\n✅ All features demonstrated:")
    print("  ✓ Session and memory management (ADK SessionService)")
    print("  ✓ Patient context retention across turns")
    print("  ✓ EDD calculation tool (ADK function tool)")
    print("  ✓ Nurse agent consultation (Agent-as-a-Tool)")
    print("  ✓ Safety-first medical guidance")
    print("  ✓ Risk assessment and triage")
    print("  ✓ LLM-as-a-Judge evaluation")
    print("  ✓ Comprehensive logging and observability")
    print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    # Run the demo
    asyncio.run(run_demo())

