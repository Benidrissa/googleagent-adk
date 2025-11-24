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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agent runner (will be implemented after deployment structure is ready)
# from pregnancy_companion_agent import run_agent_interaction

# Conditional import for reminder scheduler
try:
    from anc_reminder_scheduler import run_reminder_loop
    REMINDER_ENABLED = True
except ImportError:
    REMINDER_ENABLED = False
    logger.warning("anc_reminder_scheduler not available - /callback/loop endpoint will be limited")

# Pydantic Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    user_id: str = Field(..., description="Unique user identifier (phone number)")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    message: str = Field(..., description="User's message")
    
    @validator('message')
    def message_not_empty(cls, v):
        """Validate message is not empty and within length limits"""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 characters)')
        return v.strip()
    
    @validator('user_id')
    def user_id_valid(cls, v):
        """Validate user_id format"""
        if not v or not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    session_id: str = Field(..., description="Session ID for this conversation")
    response: str = Field(..., description="Agent's response")
    timestamp: str = Field(..., description="Response timestamp")


class LoopCallbackRequest(BaseModel):
    """Request model for loop callback endpoint"""
    trigger_time: Optional[str] = Field(None, description="Scheduled trigger time")
    check_type: str = Field(default="daily", description="Type of check: daily, weekly, etc.")


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
    logger.info("📋 Endpoints available: /health, /chat, /callback/loop")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Pregnancy Companion API Server")


# Create FastAPI app
app = FastAPI(
    title="Pregnancy Companion Agent API",
    description="RESTful API for pregnancy companion agent interactions",
    version="1.0.0",
    lifespan=lifespan
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
            "loop_callback": "/callback/loop"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        HealthResponse with current status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.datetime.now().isoformat(),
        version="1.0.0"
    )


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
        logger.info(f"Chat request from user {request.user_id}: {request.message[:50]}...")
        
        # TODO: Implement agent interaction once runner is set up
        # For now, return a placeholder response
        # Uncomment when agent integration is ready:
        # result = await run_agent_interaction(
        #     user_input=request.message,
        #     user_id=request.user_id,
        #     session_id=request.session_id
        # )
        
        # Placeholder implementation
        result = {
            "session_id": request.session_id or f"session_{request.user_id}_{datetime.datetime.now().timestamp()}",
            "response": "Hello! I am your pregnancy companion. This is a placeholder response. The agent will be integrated soon."
        }
        
        return ChatResponse(
            session_id=result.get("session_id", "unknown"),
            response=result.get("response", ""),
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except ValueError as e:
        logger.error(f"Validation error in chat endpoint: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/callback/loop", response_model=LoopCallbackResponse, tags=["Loop"])
async def loop_callback(
    request: LoopCallbackRequest,
    background_tasks: BackgroundTasks
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
                status_code=503,
                detail="Reminder service not available"
            )
        
        # Schedule reminder loop in background
        background_tasks.add_task(run_reminder_loop)
        
        return LoopCallbackResponse(
            status="scheduled",
            scheduled_at=datetime.datetime.now().isoformat(),
            check_type=request.check_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in loop callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule reminder loop: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "api_server:app",  # Use string import for reload to work
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # Enable auto-reload in development
    )
