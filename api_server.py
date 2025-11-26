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
    
    # Try to read from actual log files
    log_file = Path("data/agent.log")
    
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[-limit:]  # Get last N lines
                for line in lines:
                    try:
                        # Parse log line format: timestamp - level - message
                        parts = line.strip().split(' - ', 2)
                        if len(parts) >= 3:
                            log_entry = {
                                "timestamp": parts[0],
                                "level": parts[1],
                                "message": parts[2],
                                "trace_id": None,
                                "span_id": None,
                                "tool_name": None,
                                "tool_args": None,
                                "tool_response": None
                            }
                            
                            # Filter by level if specified
                            if not level or level.upper() == "ALL" or parts[1] == level.upper():
                                logs.append(log_entry)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
    
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
    import os
    
    results = []
    
    # Read from ADK evaluation history
    eval_history_dir = Path("agent_eval/.adk/eval_history")
    
    if eval_history_dir.exists():
        # Get all eval result files, sorted by modification time (newest first)
        eval_files = sorted(
            eval_history_dir.glob("*.evalset_result.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for eval_file in eval_files:
            try:
                with open(eval_file, 'r') as f:
                    data = json.load(f)
                    
                    # Parse eval cases
                    eval_cases = []
                    passed = 0
                    failed = 0
                    not_evaluated = 0
                    
                    for case in data.get("eval_case_results", []):
                        # Map final_eval_status: 1=PASSED, 2=FAILED, 3=NOT_EVALUATED
                        status_map = {1: "PASSED", 2: "FAILED", 3: "NOT_EVALUATED"}
                        status = status_map.get(case.get("final_eval_status", 3), "NOT_EVALUATED")
                        
                        if status == "PASSED":
                            passed += 1
                        elif status == "FAILED":
                            failed += 1
                        else:
                            not_evaluated += 1
                        
                        # Extract conversation
                        conversation = []
                        invocations = case.get("eval_metric_result_per_invocation", [])
                        if invocations:
                            inv = invocations[0].get("actual_invocation", {})
                            user_content = ""
                            final_response = ""
                            
                            # Get user content
                            user_parts = inv.get("user_content", {}).get("parts", [])
                            if user_parts:
                                user_content = user_parts[0].get("text", "")
                            
                            # Get final response
                            response_parts = inv.get("final_response", {}).get("parts", [])
                            if response_parts:
                                final_response = response_parts[0].get("text", "")
                            
                            conversation.append({
                                "user_content": user_content,
                                "final_response": final_response
                            })
                        
                        # Extract metrics
                        metrics = {}
                        for metric_result in case.get("overall_eval_metric_results", []):
                            metric_name = metric_result.get("metric_name")
                            score = metric_result.get("score")
                            if metric_name and score is not None:
                                metrics[metric_name] = score
                        
                        eval_cases.append({
                            "eval_id": case.get("eval_id", "unknown"),
                            "status": status,
                            "conversation": conversation,
                            "metrics": metrics
                        })
                    
                    # Create result entry
                    result = {
                        "eval_set_id": data.get("eval_set_id", "unknown"),
                        "timestamp": datetime.datetime.fromtimestamp(eval_file.stat().st_mtime).isoformat(),
                        "total_cases": len(eval_cases),
                        "passed": passed,
                        "failed": failed,
                        "not_evaluated": not_evaluated,
                        "eval_cases": eval_cases
                    }
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error parsing eval file {eval_file}: {e}")
                continue
    
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
