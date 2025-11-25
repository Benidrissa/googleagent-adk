#!/usr/bin/env python3
"""
Test custom function calling with gemini-2.5-flash-lite model.
Based on Kaggle 5-day Agents course pattern.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# Set environment for Gemini API
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

logger.info("✅ Environment variables loaded from .env file")
logger.info("✅ Gemini API key setup complete.")
logger.info("✅ ADK components imported successfully.")

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# ============================================================================
# TEST 1: Simple Custom Functions (Auto-execution)
# ============================================================================


def calculate_pregnancy_weeks(lmp_date: str) -> dict:
    """
    Calculate pregnancy weeks from Last Menstrual Period (LMP) date.

    Args:
        lmp_date: LMP date in YYYY-MM-DD format

    Returns:
        Dictionary containing pregnancy information
    """
    try:
        lmp = datetime.strptime(lmp_date, "%Y-%m-%d")
        today = datetime.now()
        days_pregnant = (today - lmp).days
        weeks_pregnant = days_pregnant // 7
        days_remainder = days_pregnant % 7

        # Calculate EDD (280 days from LMP)
        edd = lmp + timedelta(days=280)
        days_until_edd = (edd - today).days

        logger.info(f"🔧 TOOL CALLED: calculate_pregnancy_weeks(lmp_date={lmp_date})")

        return {
            "weeks_pregnant": weeks_pregnant,
            "days_pregnant": days_pregnant,
            "days_remainder": days_remainder,
            "edd": edd.strftime("%Y-%m-%d"),
            "days_until_edd": days_until_edd,
            "lmp_date": lmp_date,
            "status": "success",
        }
    except ValueError as e:
        return {
            "error": f"Invalid date format. Please use YYYY-MM-DD: {e}",
            "status": "error",
        }


def assess_pregnancy_risk(age: int, symptoms: str) -> dict:
    """
    Assess pregnancy risk level based on age and symptoms.

    Args:
        age: Patient's age in years
        symptoms: Description of current symptoms

    Returns:
        Dictionary with risk assessment
    """
    logger.info(
        f"🔧 TOOL CALLED: assess_pregnancy_risk(age={age}, symptoms={symptoms[:50]}...)"
    )

    risk_level = "LOW"
    warnings = []

    # Check age-related risks
    if age < 18:
        risk_level = "MODERATE"
        warnings.append("Adolescent pregnancy requires additional monitoring")
    elif age > 35:
        risk_level = "MODERATE"
        warnings.append("Advanced maternal age - increased monitoring recommended")

    # Check for danger signs in symptoms
    symptoms_lower = symptoms.lower()
    danger_signs = {
        "bleeding": "HIGH",
        "hemorrhage": "HIGH",
        "severe headache": "HIGH",
        "blurred vision": "HIGH",
        "dizziness": "MODERATE",
        "fever": "HIGH",
        "severe pain": "HIGH",
    }

    for sign, level in danger_signs.items():
        if sign in symptoms_lower:
            if level == "HIGH":
                risk_level = "HIGH"
                warnings.append(f"Danger sign detected: {sign}")
            elif risk_level != "HIGH" and level == "MODERATE":
                risk_level = "MODERATE"
                warnings.append(f"Concerning symptom: {sign}")

    return {
        "risk_level": risk_level,
        "age": age,
        "symptoms": symptoms,
        "warnings": warnings,
        "requires_immediate_care": risk_level == "HIGH",
        "status": "success",
    }


# ============================================================================
# TEST 2: Long-Running Functions with Confirmation (Pausable)
# ============================================================================

EMERGENCY_THRESHOLD = 3  # Severity threshold requiring confirmation


def request_emergency_assistance(
    severity_level: int, location: str, symptoms: str, tool_context: ToolContext
) -> dict:
    """
    Request emergency medical assistance. Requires confirmation for high severity (>3).

    Args:
        severity_level: Severity from 1-10 (10 being most severe)
        location: Patient's current location
        symptoms: Description of symptoms
        tool_context: ADK tool context for managing confirmations

    Returns:
        Dictionary with emergency request status
    """

    # SCENARIO 1: Low severity (≤3) auto-approves
    if severity_level <= EMERGENCY_THRESHOLD:
        logger.info(f"✅ Auto-approved: severity {severity_level}")
        return {
            "status": "approved",
            "request_id": f"EMG-{severity_level}-AUTO",
            "severity_level": severity_level,
            "location": location,
            "message": f"Medical consultation recommended for severity {severity_level}. Visit nearest health facility.",
            "emergency_dispatch": False,
        }

    # SCENARIO 2: First call - high severity needs confirmation - PAUSE
    if not tool_context.tool_confirmation:
        logger.info(f"⏸️  Requesting confirmation for severity {severity_level}")
        tool_context.request_confirmation(
            hint=f"⚠️ HIGH SEVERITY ({severity_level}/10): {symptoms} at {location}. Dispatch emergency ambulance?",
            payload={
                "severity_level": severity_level,
                "location": location,
                "symptoms": symptoms,
            },
        )
        return {
            "status": "pending",
            "message": f"Emergency request requires confirmation",
            "severity_level": severity_level,
        }

    # SCENARIO 3: Resuming with confirmation response - RESUME
    if tool_context.tool_confirmation.confirmed:
        logger.info(f"✅ Emergency approved: severity {severity_level}")
        return {
            "status": "approved",
            "request_id": f"EMG-{severity_level}-CONFIRMED",
            "severity_level": severity_level,
            "location": location,
            "symptoms": symptoms,
            "message": f"🚨 Emergency ambulance dispatched to {location}",
            "emergency_dispatch": True,
            "estimated_arrival": "10-15 minutes",
        }
    else:
        logger.info(f"❌ Emergency rejected: severity {severity_level}")
        return {
            "status": "rejected",
            "message": f"Emergency request declined. Please contact local health facility.",
            "severity_level": severity_level,
        }


# ============================================================================
# CREATE AGENTS
# ============================================================================

# Simple agent with auto-executing tools
pregnancy_calculator_agent = LlmAgent(
    name="pregnancy_calculator",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a pregnancy care assistant.

When users provide their LMP date or ask about pregnancy duration:
1. Use the calculate_pregnancy_weeks tool with the LMP date in YYYY-MM-DD format
2. Provide clear, friendly information about their pregnancy progress
3. Include weeks pregnant, EDD, and days remaining

When users describe symptoms or concerns:
1. Use the assess_pregnancy_risk tool with their age and symptoms
2. Explain the risk level clearly
3. If HIGH risk, emphasize urgency to seek medical care
4. Provide supportive, caring responses
""",
    tools=[
        FunctionTool(func=calculate_pregnancy_weeks),
        FunctionTool(func=assess_pregnancy_risk),
    ],
)

logger.info("✅ Pregnancy Calculator Agent created")

# Pausable agent with confirmation workflow
emergency_agent = LlmAgent(
    name="emergency_coordinator",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an emergency medical coordinator for pregnancy care.

When users request emergency assistance:
1. Use the request_emergency_assistance tool with severity level (1-10), location, and symptoms
2. For severity ≤3: Inform them medical consultation is recommended
3. For severity >3: Explain that emergency dispatch requires confirmation
4. If status is 'pending', tell them the request is being processed
5. After final approval/rejection, provide clear next steps
6. Always maintain calm, professional tone

Severity guidelines:
- 1-3: Mild discomfort, routine care
- 4-6: Concerning symptoms, urgent care
- 7-10: Danger signs, emergency care
""",
    tools=[FunctionTool(func=request_emergency_assistance)],
)

logger.info("✅ Emergency Agent created")

# Wrap emergency agent in resumable app
emergency_app = App(
    name="emergency_coordinator_app",
    root_agent=emergency_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

logger.info("✅ Resumable Emergency App created")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def check_for_approval(events):
    """Check if events contain an approval request."""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "adk_request_confirmation"
                ):
                    return {
                        "approval_id": part.function_call.id,
                        "invocation_id": event.invocation_id,
                    }
    return None


def print_agent_response(events):
    """Print agent's text responses from events."""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"🤖 Agent: {part.text}")


def create_approval_response(approval_info, approved):
    """Create approval response message."""
    confirmation_response = types.FunctionResponse(
        id=approval_info["approval_id"],
        name="adk_request_confirmation",
        response={"confirmed": approved},
    )
    return types.Content(
        role="user", parts=[types.Part(function_response=confirmation_response)]
    )


# ============================================================================
# TEST FUNCTIONS
# ============================================================================


async def test_simple_functions():
    """Test simple auto-executing functions."""

    print("\n" + "=" * 80)
    print("TEST 1: Simple Custom Functions (Auto-execution)")
    print("=" * 80 + "\n")

    runner = InMemoryRunner(agent=pregnancy_calculator_agent)

    test_cases = [
        "My LMP was 2025-05-01. How many weeks pregnant am I?",
        "I am 17 years old and feeling dizzy and seeing spots. Should I be worried?",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"👤 User: {query}\n")

        response = await runner.run_debug(query)

        for event in response:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"🤖 Agent: {part.text}\n")

        print()


async def test_pausable_function(query: str, severity: int, auto_approve: bool):
    """Test pausable function with confirmation workflow."""

    print(f"\n{'='*80}")
    print(f"👤 User: {query}")
    print(f"   [Severity: {severity}, Auto-approve: {auto_approve}]")
    print()

    session_service = InMemorySessionService()
    runner = Runner(
        app=emergency_app,
        session_service=session_service,
    )

    session_id = f"emergency_{uuid.uuid4().hex[:8]}"

    await session_service.create_session(
        app_name="emergency_coordinator_app", user_id="test_user", session_id=session_id
    )

    query_content = types.Content(role="user", parts=[types.Part(text=query)])
    events = []

    # STEP 1: Send initial request
    async for event in runner.run_async(
        user_id="test_user", session_id=session_id, new_message=query_content
    ):
        events.append(event)

    # STEP 2: Check for approval request
    approval_info = check_for_approval(events)

    # STEP 3: Handle approval workflow if needed
    if approval_info:
        print(f"⏸️  Pausing for approval...")
        print(f"🤔 Decision: {'APPROVE ✅' if auto_approve else 'REJECT ❌'}\n")

        async for event in runner.run_async(
            user_id="test_user",
            session_id=session_id,
            new_message=create_approval_response(approval_info, auto_approve),
            invocation_id=approval_info["invocation_id"],
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"🤖 Agent: {part.text}")
    else:
        print_agent_response(events)

    print(f"{'='*80}\n")


async def main():
    """Run all tests."""
    try:
        print("\n" + "=" * 80)
        print("Custom Function Calling with gemini-2.5-flash-lite")
        print("Based on Kaggle 5-day Agents Course Pattern")
        print("=" * 80)

        # Test 1: Simple auto-executing functions
        await test_simple_functions()

        # Test 2: Pausable functions with confirmation
        print("\n" + "=" * 80)
        print("TEST 2: Long-Running Functions with Confirmation")
        print("=" * 80)

        # Low severity - auto-approved
        await test_pausable_function(
            "I have mild back pain (severity 2 out of 10). Location: Bamako, Mali. Symptoms: mild lower back discomfort.",
            severity=2,
            auto_approve=True,
        )

        # High severity - approved
        await test_pausable_function(
            "Emergency! I am bleeding heavily and very dizzy (severity 9 out of 10)! Location: Lagos, Nigeria. Symptoms: heavy vaginal bleeding, severe dizziness, weakness.",
            severity=9,
            auto_approve=True,
        )

        # High severity - rejected
        await test_pausable_function(
            "Severe headache and blurred vision (severity 8 out of 10). Location: Accra, Ghana. Symptoms: intense head pain, vision problems, nausea.",
            severity=8,
            auto_approve=False,
        )

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80 + "\n")

        return 0

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
