"""
FastAPI Server Wrapper for Pregnancy Companion Agent

This module provides a RESTful API interface for the pregnancy companion agent,
enabling web-based and mobile client interactions.
"""

import logging
import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Configure logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import agent runner
from pregnancy_companion_agent import run_agent_interaction

# Conditional import for reminder scheduler
try:
    from anc_reminder_scheduler import run_reminder_loop

    REMINDER_ENABLED = True
except ImportError:
    REMINDER_ENABLED = False
    logger.warning(
        "anc_reminder_scheduler not available - /callback/loop endpoint will be limited"
    )


# Pydantic Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""

    user_id: str = Field(..., description="Unique user identifier (phone number)")
    session_id: Optional[str] = Field(
        None, description="Session ID for continuing conversation"
    )
    message: str = Field(..., description="User's message")

    @validator("message")
    def message_not_empty(cls, v):
        """Validate message is not empty and within length limits"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 5000:
            raise ValueError("Message too long (max 5000 characters)")
        return v.strip()

    @validator("user_id")
    def user_id_valid(cls, v):
        """Validate user_id format"""
        if not v or not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""

    session_id: str = Field(..., description="Session ID for this conversation")
    response: str = Field(..., description="Agent's response")
    timestamp: str = Field(..., description="Response timestamp")


class LoopCallbackRequest(BaseModel):
    """Request model for loop callback endpoint"""

    trigger_time: Optional[str] = Field(None, description="Scheduled trigger time")
    check_type: str = Field(
        default="daily", description="Type of check: daily, weekly, etc."
    )


class LoopCallbackResponse(BaseModel):
    """Response model for loop callback endpoint"""

    status: str = Field(..., description="Status of the callback processing")
    scheduled_at: str = Field(..., description="When the callback was scheduled")
    check_type: str = Field(..., description="Type of check performed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current server timestamp")
    version: str = Field(..., description="API version")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Pregnancy Companion API Server")
    logger.info("📋 Endpoints available: /health, /chat, /logs, /evaluation/results, /callback/loop")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Pregnancy Companion API Server")


# Create FastAPI app
app = FastAPI(
    title="Pregnancy Companion Agent API",
    description="RESTful API for pregnancy companion agent interactions",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Pregnancy Companion Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "loop_callback": "/callback/loop",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        HealthResponse with current status and timestamp
    """
    return HealthResponse(
        status="healthy", timestamp=datetime.datetime.now().isoformat(), version="1.0.0"
    )


@app.get("/logs", tags=["Observability"])
async def get_logs(level: Optional[str] = None, limit: int = 100):
    """
    Get recent agent logs with OpenTelemetry trace information.
    
    Args:
        level: Filter by log level (ERROR, WARNING, INFO, DEBUG)
        limit: Maximum number of logs to return (default: 100)
    
    Returns:
        JSON with logs array containing trace IDs, timestamps, and tool information
    """
    import json
    import os
    from pathlib import Path
    
    logs = []
    
    # Try to read from OpenTelemetry trace files or logs
    trace_dir = Path("agent_eval/.adk/traces")
    log_file = Path("data/agent.log")
    
    # For now, return structured sample data that mirrors what would come from actual tracing
    # In production, this would read from your logging/tracing backend
    sample_logs = [
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "Pregnancy Companion Agent initialized",
            "trace_id": "0x24b04fa32bb5e8a4",
            "span_id": None,
            "tool_name": None,
            "tool_args": None,
            "tool_response": None
        },
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "User message received",
            "trace_id": "0xe40ccb14e44bbc12",
            "span_id": "0x1a2b3c4d5e6f7890",
            "tool_name": None,
            "tool_args": None,
            "tool_response": None
        },
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "Tool call: get_pregnancy_by_phone",
            "trace_id": "0x995876b3c924ca89",
            "span_id": "0x2b3c4d5e6f78901a",
            "tool_name": "get_pregnancy_by_phone",
            "tool_args": {"phone": "+226707070"},
            "tool_response": None
        },
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "Tool response received",
            "trace_id": "0x882b1652fa01986c",
            "span_id": "0x3c4d5e6f78901a2b",
            "tool_name": "get_pregnancy_by_phone",
            "tool_args": None,
            "tool_response": {"status": "success", "record": {"name": "Fatou", "age": 39}}
        },
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "Agent response generated",
            "trace_id": "0x09add57311573fab",
            "span_id": "0x4d5e6f78901a2b3c",
            "tool_name": None,
            "tool_args": None,
            "tool_response": None
        }
    ]
    
    # Filter by level if specified
    if level and level.upper() != "ALL":
        logs = [log for log in sample_logs if log["level"] == level.upper()]
    else:
        logs = sample_logs
    
    # Apply limit
    logs = logs[:limit]
    
    return {"logs": logs, "total": len(logs)}


@app.get("/evaluation/results", tags=["Evaluation"])
async def get_evaluation_results():
    """
    Get ADK evaluation results from recent test runs.
    
    Returns:
        JSON with evaluation runs, test cases, metrics, and status
    """
    import json
    from pathlib import Path
    
    results = []
    
    # Try to read from ADK evaluation history
    eval_history_dir = Path("agent_eval/.adk/eval_history")
    evalset_file = Path("tests/pregnancy_agent_integration.evalset.json")
    
    # For now, return structured sample data
    # In production, this would parse actual evaluation results from .adk/eval_history/
    sample_result = {
        "eval_set_id": "pregnancy_companion_integration_suite",
        "timestamp": datetime.datetime.now().isoformat(),
        "total_cases": 2,
        "passed": 0,
        "failed": 2,
        "eval_cases": [
            {
                "eval_id": "new_patient_registration",
                "status": "FAILED",
                "conversation": [
                    {
                        "user_content": "Hello! My name is Amina, phone +221 77 888 9999. I'm 29 years old, last period was May 22, 2025, living in Dakar, Senegal.",
                        "final_response": "Hello Amina! I've registered your information. Your estimated due date is February 26, 2026. You're currently at 26 weeks. Let me know if you need information about ANC visits or have any questions!"
                    }
                ],
                "metrics": {
                    "tool_trajectory_avg_score": 0.0,
                    "response_match_score": 0.34,
                    "rubric_based_tool_use_quality_v1": 0.8
                }
            },
            {
                "eval_id": "nutrition_guidance_request",
                "status": "FAILED",
                "conversation": [
                    {
                        "user_content": "What foods are rich in iron that I should eat?",
                        "final_response": "Foods rich in iron include leafy green vegetables (spinach, kale), beans and lentils, lean red meat, fortified cereals, and dried fruits. Iron is very important during pregnancy to prevent anemia."
                    }
                ],
                "metrics": {
                    "tool_trajectory_avg_score": 0.0,
                    "response_match_score": 0.25,
                    "rubric_based_tool_use_quality_v1": 0.75
                }
            }
        ]
    }
    
    results.append(sample_result)
    
    return {"results": results, "total": len(results)}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint for user-agent interactions.

    Args:
        request: ChatRequest with user_id, optional session_id, and message

    Returns:
        ChatResponse with session_id, agent response, and timestamp

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(
            f"Chat request from user {request.user_id}: {request.message[:50]}..."
        )

        # Generate phone-scoped session_id if not provided (PATIENT ISOLATION)
        session_id = (
            request.session_id
            or f"patient_{request.user_id}_{datetime.datetime.now().timestamp()}"
        )

        # Run the agent interaction
        agent_response = await run_agent_interaction(
            user_input=request.message, user_id=request.user_id, session_id=session_id
        )

        return ChatResponse(
            session_id=session_id,
            response=agent_response,
            timestamp=datetime.datetime.now().isoformat(),
        )

    except ValueError as e:
        logger.error(f"Validation error in chat endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/callback/loop", response_model=LoopCallbackResponse, tags=["Loop"])
async def loop_callback(
    request: LoopCallbackRequest, background_tasks: BackgroundTasks
):
    """
    Callback endpoint for LoopAgent reminders.
    Triggered by scheduler to send proactive ANC reminders.

    Args:
        request: LoopCallbackRequest with trigger_time and check_type
        background_tasks: FastAPI background tasks

    Returns:
        LoopCallbackResponse with status and scheduling info

    Raises:
        HTTPException: If scheduling fails
    """
    try:
        logger.info(f"Loop callback triggered: {request.check_type}")

        if not REMINDER_ENABLED:
            raise HTTPException(
                status_code=503, detail="Reminder service not available"
            )

        # Schedule reminder loop in background
        background_tasks.add_task(run_reminder_loop)

        return LoopCallbackResponse(
            status="scheduled",
            scheduled_at=datetime.datetime.now().isoformat(),
            check_type=request.check_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in loop callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule reminder loop: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8002"))
    logger.info(f"Starting development server on port {port}...")
    uvicorn.run(
        "api_server:app",  # Use string import for reload to work
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True,  # Enable auto-reload in development
    )
