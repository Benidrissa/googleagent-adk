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
import requests
import asyncio
import sqlite3
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    logger_dotenv = logging.getLogger(__name__)
    logger_dotenv.info("✅ Environment variables loaded from .env file")
except ImportError:
    # dotenv not installed, environment variables will be loaded from system only
    pass

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import AgentTool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold
from mcp.client.stdio import StdioServerParameters, stdio_client

# --- CONFIGURATION ---
# Set up logging (ADK best practice)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# OpenTelemetry for advanced observability (optional enhancement)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    # Initialize tracer
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )
    tracer = trace.get_tracer(__name__)
    TRACING_ENABLED = True
    logger.info("✅ OpenTelemetry tracing enabled")
except ImportError:
    TRACING_ENABLED = False
    tracer = None
    logger.info("ℹ️  OpenTelemetry not available, running without tracing")

# Get API keys from environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")
if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
    logger.warning(
        "⚠️  GOOGLE_API_KEY not set. Please set it in your environment or .env file"
    )
else:
    # Set the environment variable as required by google-genai SDK
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    logger.info("✅ Google API configured for direct Gemini API access")

# Google Maps API key (can be same as GOOGLE_API_KEY or separate)
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", GOOGLE_API_KEY)
if GOOGLE_MAPS_API_KEY == "YOUR_API_KEY_HERE":
    logger.warning(
        "⚠️  GOOGLE_MAPS_API_KEY not set. Maps functionality will be limited."
    )


# Helper function to check if we should use simulation mode
def _is_api_key_placeholder(api_key: str) -> bool:
    """Check if the API key is a placeholder value."""
    if not api_key:
        return True
    placeholder_values = [
        "your_google_maps_api_key_here",
        "YOUR_API_KEY_HERE",
        "your_api_key_here",
        "INSERT_API_KEY_HERE",
        "REPLACE_WITH_YOUR_KEY",
    ]
    return api_key in placeholder_values or len(api_key) < 20


# Configure retry options for LLM calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Model configuration
# IMPORTANT: Always use gemini-2.5-flash-lite - DO NOT CHANGE
# This model works with google_search tool transparently via ADK
# Custom Python function tools work with this model when properly configured
MODEL_NAME = "gemini-2.5-flash-lite"

# Session state keys for pause/resume functionality
STATE_PAUSED = "consultation_paused"
STATE_PAUSE_REASON = "pause_reason"
STATE_PAUSE_TIMESTAMP = "pause_timestamp"
STATE_LAST_TOPIC = "last_discussed_topic"
STATE_PENDING_ACTIONS = "pending_actions"

# MCP Health Facility Cache (simulated local database)
LOCAL_HEALTH_FACILITIES = {
    "Bamako": [
        {
            "name": "Hospital Gabriel Touré",
            "address": "Rue 40, Bamako",
            "type": "general",
            "rating": 4.2,
            "emergency": True,
        },
        {
            "name": "Point G Hospital",
            "address": "Colline du Point G, Bamako",
            "type": "general",
            "rating": 4.0,
            "emergency": True,
        },
        {
            "name": "Centre de Santé Communautaire",
            "address": "Avenue Moussa Tavele",
            "type": "clinic",
            "rating": 3.8,
            "emergency": False,
        },
    ],
    "Accra": [
        {
            "name": "Ridge Hospital",
            "address": "Castle Road, Ridge, Accra",
            "type": "general",
            "rating": 4.3,
            "emergency": True,
        },
        {
            "name": "37 Military Hospital",
            "address": "Liberation Road, Accra",
            "type": "military",
            "rating": 4.5,
            "emergency": True,
        },
        {
            "name": "Korle Bu Teaching Hospital",
            "address": "Guggisberg Avenue, Accra",
            "type": "teaching",
            "rating": 4.1,
            "emergency": True,
        },
    ],
    "Lagos": [
        {
            "name": "Lagos University Teaching Hospital",
            "address": "Idi-Araba, Lagos",
            "type": "teaching",
            "rating": 4.0,
            "emergency": True,
        },
        {
            "name": "Lagos Island Maternity Hospital",
            "address": "Broad Street, Lagos Island",
            "type": "maternity",
            "rating": 3.9,
            "emergency": True,
        },
    ],
}

# --- APPLICATION CONSTANTS ---
APP_NAME = "pregnancy_companion"
DEFAULT_USER_ID = "patient_user"

logger.info("✅ Pregnancy Companion Agent initialized")

# ============================================================================
# DATABASE-BACKED MEMORY SERVICE
# ============================================================================


class DatabaseMemoryService(InMemoryMemoryService):
    """
    Persistent memory service using SQLite database.
    Extends InMemoryMemoryService and adds database persistence.

    Stores sessions in database for persistence across restarts.
    """

    def __init__(self, db_path: str = "pregnancy_agent_memory.db"):
        """Initialize database-backed memory service."""
        super().__init__()  # Initialize parent InMemoryMemoryService
        self.db_path = Path(db_path)
        self._session_cache = (
            {}
        )  # Cache sessions: {(app_name, user_id, session_id): Session}
        self._init_database()
        self._load_sessions_from_database()  # Load existing sessions on startup
        logger.info(
            f"✅ Database Memory Service initialized: {self.db_path.absolute()}"
        )

    def _init_database(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                session_data BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(app_name, user_id, session_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_sessions 
            ON sessions(app_name, user_id)
        """
        )

        conn.commit()
        conn.close()

    def _load_sessions_from_database(self):
        """Load existing sessions from database on startup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        count = 0
        try:
            cursor.execute(
                "SELECT app_name, user_id, session_id, session_data FROM sessions"
            )
            for row in cursor.fetchall():
                app_name, user_id, session_id, session_data = row
                try:
                    session = pickle.loads(session_data)
                    # Cache locally - will be added to parent's memory when first accessed
                    key = (app_name, user_id, session_id)
                    self._session_cache[key] = session
                    count += 1
                except Exception as e:
                    logger.error(f"Error loading session from database: {e}")

            if count > 0:
                logger.info(
                    f"📚 Loaded {count} sessions from database (will sync to memory on first use)"
                )
        except Exception as e:
            logger.error(f"Error reading from database: {e}")
        finally:
            conn.close()

    async def _restore_cached_sessions(self):
        """Restore cached sessions to parent's in-memory storage."""
        for key, session in self._session_cache.items():
            try:
                await super().add_session_to_memory(session)
            except Exception as e:
                logger.error(f"Error restoring session {key}: {e}")

    async def add_session_to_memory(self, session):
        """Add session to memory and persist to database."""
        # First, use parent's in-memory storage
        await super().add_session_to_memory(session)

        # Cache locally
        key = (session.app_name, session.user_id, session.id)
        self._session_cache[key] = session

        # Then persist to database
        self._persist_session(session)

    def _persist_session(self, session):
        """Persist session to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Pickle the entire session object
            session_data = pickle.dumps(session)

            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions 
                (app_name, user_id, session_id, session_data, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (session.app_name, session.user_id, session.id, session_data),
            )

            conn.commit()
            logger.debug(
                f"💾 Persisted session to database: {session.user_id}/{session.id}"
            )
        except Exception as e:
            logger.error(f"Error persisting session to database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def clear_user_memory(self, app_name: str, user_id: str):
        """Clear memory for a user from both in-memory and database."""
        # Clear from cache
        keys_to_delete = [
            k
            for k in self._session_cache.keys()
            if k[0] == app_name and k[1] == user_id
        ]
        for key in keys_to_delete:
            del self._session_cache[key]

        # Clear from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM sessions WHERE app_name = ? AND user_id = ?",
                (app_name, user_id),
            )
            conn.commit()
            logger.info(f"🗑️  Cleared sessions for user {user_id}")
        finally:
            conn.close()

    async def search_memory(self, app_name: str, user_id: str, query: str):
        """
        Search stored sessions for relevant memories.

        Implements keyword-based search across all user sessions stored in database.
        Extracts text from session events and matches against query keywords.

        Args:
            app_name: Application name
            user_id: User identifier
            query: Search query string

        Returns:
            SearchMemoryResponse with matching memories
        """
        from google.adk.memory.base_memory_service import SearchMemoryResponse
        from google.adk.memory.memory_entry import MemoryEntry
        from google.genai.types import Content, Part

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        matching_memories = []
        query_lower = query.lower()
        query_keywords = set(query_lower.split())

        try:
            # Retrieve all sessions for this user
            cursor.execute(
                "SELECT session_id, session_data FROM sessions WHERE app_name = ? AND user_id = ?",
                (app_name, user_id),
            )

            for row in cursor.fetchall():
                session_id, session_data = row
                try:
                    session = pickle.loads(session_data)

                    # Extract text from session events
                    for event in session.events:
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    text_lower = part.text.lower()

                                    # Check if any query keywords match
                                    if any(
                                        keyword in text_lower
                                        for keyword in query_keywords
                                    ):
                                        # Create a memory entry for this event
                                        memory_content = Content(
                                            role=event.content.role,
                                            parts=[Part(text=part.text)],
                                        )

                                        # Create proper ADK MemoryEntry
                                        memory = MemoryEntry(
                                            content=memory_content,
                                            author=event.content.role,
                                        )
                                        matching_memories.append(memory)
                                        break  # Only add one memory per event

                except Exception as e:
                    logger.error(f"Error processing session {session_id}: {e}")

            logger.info(
                f"🔍 Found {len(matching_memories)} memories matching query: '{query}'"
            )

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
        finally:
            conn.close()

        # Return SearchMemoryResponse
        return SearchMemoryResponse(memories=matching_memories)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM sessions")
            users = cursor.fetchone()[0]

            return {
                "total_sessions": total,
                "unique_users": users,
                "cached_sessions": len(self._session_cache),
                "database_path": str(self.db_path.absolute()),
                "database_size_kb": (
                    self.db_path.stat().st_size / 1024 if self.db_path.exists() else 0
                ),
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()


# ============================================================================
# TOOLS SECTION - ADK Function Tools
# ============================================================================


def get_local_health_facilities(
    city: str, facility_type: str = "all"
) -> Dict[str, Any]:
    """
    Get health facilities from local MCP-style database (offline-capable).
    This simulates an MCP (Model Context Protocol) server providing local data.

    Args:
        city: City name to search in
        facility_type: Type filter ("all", "emergency", "maternity", "clinic")

    Returns:
        dict: Dictionary containing:
            - status: "success" or "error"
            - facilities: List of local health facilities
            - source: "local_mcp" to indicate offline capability
            - count: Number of facilities found
    """
    try:
        # Search local database (MCP-style)
        city_key = None
        for key in LOCAL_HEALTH_FACILITIES.keys():
            if key.lower() in city.lower() or city.lower() in key.lower():
                city_key = key
                break

        if not city_key:
            return {
                "status": "error",
                "error_message": f"No local data available for {city}. Try nearby cities.",
                "available_cities": list(LOCAL_HEALTH_FACILITIES.keys()),
            }

        facilities = LOCAL_HEALTH_FACILITIES[city_key]

        # Filter by type if specified
        if facility_type != "all":
            if facility_type == "emergency":
                facilities = [f for f in facilities if f.get("emergency", False)]
            else:
                facilities = [f for f in facilities if f.get("type") == facility_type]

        logger.info(
            f"Retrieved {len(facilities)} local facilities for {city} (MCP source)"
        )

        return {
            "status": "success",
            "facilities": facilities,
            "source": "local_mcp",
            "count": len(facilities),
            "city": city_key,
            "offline_capable": True,
        }

    except Exception as e:
        logger.error(f"Error accessing local facility database: {e}")
        return {"status": "error", "error_message": f"Database error: {str(e)}"}


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
            - weeks_remaining: Weeks until due date
            - status: "success" or "error"
            - error_message: Error description if status is "error"
    """
    try:
        lmp = datetime.datetime.strptime(lmp_date, "%Y-%m-%d")
        edd = lmp + datetime.timedelta(days=280)
        gestational_weeks = int((datetime.datetime.now() - lmp).days / 7)
        weeks_remaining = max(0, 40 - gestational_weeks)

        logger.info(
            f"EDD calculated: {edd.strftime('%Y-%m-%d')} (LMP: {lmp_date}, {gestational_weeks} weeks)"
        )

        return {
            "status": "success",
            "edd": edd.strftime("%Y-%m-%d"),
            "gestational_weeks": gestational_weeks,
            "weeks_remaining": weeks_remaining,
        }
    except ValueError as e:
        logger.error(f"Invalid date format for LMP: {lmp_date}")
        return {
            "status": "error",
            "error_message": f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-05-01)",
        }
    except Exception as e:
        logger.error(f"Error calculating EDD: {e}")
        return {"status": "error", "error_message": f"Error calculating EDD: {str(e)}"}


def calculate_anc_schedule(lmp_date: str) -> Dict[str, Any]:
    """
    Calculates the complete ANC (Antenatal Care) visit schedule based on WHO guidelines.

    WHO recommends a minimum of 8 ANC contacts during pregnancy:
    - First visit: 8-12 weeks (we use 10 weeks as midpoint)
    - Second visit: 20 weeks
    - Third visit: 26 weeks
    - Fourth visit: 30 weeks
    - Fifth visit: 34 weeks
    - Sixth visit: 36 weeks
    - Seventh visit: 38 weeks
    - Eighth visit: 40 weeks (at EDD)

    Args:
        lmp_date: Last Menstrual Period date in YYYY-MM-DD format (e.g., "2025-03-01")

    Returns:
        dict: Dictionary containing:
            - status: "success" or "error"
            - anc_schedule: List of ANC visits with dates and status
            - next_visit: Next upcoming visit information (within 14 days)
            - overdue_visits: List of overdue visits (more than 7 days past)
            - completed_visits: Count of completed visits
            - error_message: Error description if status is "error"
    """
    try:
        lmp = datetime.datetime.strptime(lmp_date, "%Y-%m-%d")
        current_date = datetime.datetime.now()

        # WHO ANC visit schedule (in weeks from LMP)
        anc_weeks = [10, 20, 26, 30, 34, 36, 38, 40]

        schedule = []
        next_visit = None
        overdue_visits = []
        completed_count = 0

        for visit_num, week in enumerate(anc_weeks, start=1):
            visit_date = lmp + datetime.timedelta(weeks=week)
            days_until_visit = (visit_date - current_date).days

            # Determine visit status
            if days_until_visit < -7:  # More than 7 days past
                status = "overdue"
                overdue_visits.append(
                    {
                        "visit_number": visit_num,
                        "scheduled_date": visit_date.strftime("%Y-%m-%d"),
                        "week": week,
                        "days_overdue": abs(days_until_visit),
                    }
                )
            elif days_until_visit < 0:  # Within 7 days past
                status = "due_now"
            elif days_until_visit <= 14:  # Within next 14 days (2 weeks)
                status = "upcoming"
                if next_visit is None:
                    next_visit = {
                        "visit_number": visit_num,
                        "scheduled_date": visit_date.strftime("%Y-%m-%d"),
                        "week": week,
                        "days_until": days_until_visit,
                    }
            else:
                status = "scheduled"

            schedule.append(
                {
                    "visit_number": visit_num,
                    "week": week,
                    "scheduled_date": visit_date.strftime("%Y-%m-%d"),
                    "status": status,
                    "days_until": days_until_visit,
                }
            )

        # Calculate gestational age
        gestational_weeks = int((current_date - lmp).days / 7)

        logger.info(
            f"ANC schedule calculated: {len(schedule)} visits, {len(overdue_visits)} overdue"
        )

        return {
            "status": "success",
            "anc_schedule": schedule,
            "next_visit": next_visit,
            "overdue_visits": overdue_visits,
            "completed_visits": completed_count,
            "total_visits": len(schedule),
            "current_gestational_age": f"{gestational_weeks} weeks",
            "lmp_date": lmp_date,
        }

    except ValueError as e:
        logger.error(f"Invalid date format for LMP: {lmp_date}")
        return {
            "status": "error",
            "error_message": f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-03-01)",
        }
    except Exception as e:
        logger.error(f"Error calculating ANC schedule: {e}")
        return {
            "status": "error",
            "error_message": f"Error calculating ANC schedule: {str(e)}",
        }


def infer_country_from_location(location: str) -> Dict[str, Any]:
    """
    Infers the country from a location string using geocoding.
    Falls back to simulation mode if API key is not set.

    Args:
        location: Location string (city, region, address, etc.)

    Returns:
        dict: Dictionary containing:
            - status: "success" or "error"
            - country: Inferred country name
            - formatted_location: Full formatted address
            - error_message: Error description if status is "error"
    """
    if not location or not location.strip():
        return {"status": "error", "error_message": "Location cannot be empty"}

    # Simulation mode when API key is not set
    if _is_api_key_placeholder(GOOGLE_MAPS_API_KEY):
        location_lower = location.lower()
        simulated_mappings = {
            "lagos": ("Nigeria", "Lagos, Nigeria"),
            "bamako": ("Mali", "Bamako, Mali"),
            "accra": ("Ghana", "Accra, Ghana"),
            "abuja": ("Nigeria", "Abuja, Nigeria"),
            "kumasi": ("Ghana", "Kumasi, Ghana"),
            "sikasso": ("Mali", "Sikasso, Mali"),
            "port harcourt": ("Nigeria", "Port Harcourt, Nigeria"),
            "kano": ("Nigeria", "Kano, Nigeria"),
        }

        for city, (country, formatted) in simulated_mappings.items():
            if city in location_lower:
                logger.info(
                    f"[SIMULATION] Inferred country '{country}' from location '{location}'"
                )
                return {
                    "status": "success",
                    "country": country,
                    "formatted_location": formatted,
                    "simulation": True,
                }

        # Default for unknown locations
        logger.warning(f"[SIMULATION] Unknown location: {location}")
        return {
            "status": "error",
            "error_message": f"Could not determine country from location: {location}",
            "simulation": True,
        }

    try:
        # Use Google Maps Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": location, "key": GOOGLE_MAPS_API_KEY}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK" and data["results"]:
            result = data["results"][0]

            # Extract country from address components
            country = None
            for component in result.get("address_components", []):
                if "country" in component.get("types", []):
                    country = component.get("long_name")
                    break

            logger.info(f"Inferred country '{country}' from location '{location}'")

            return {
                "status": "success",
                "country": country,
                "formatted_location": result.get("formatted_address", location),
            }
        else:
            logger.warning(f"Could not geocode location: {location}")
            return {
                "status": "error",
                "error_message": f"Could not determine country from location: {location}",
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding API error: {e}")
        return {
            "status": "error",
            "error_message": f"Error contacting geocoding service: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Unexpected error in geocoding: {e}")
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def find_nearby_health_facilities(
    location: str, radius_meters: int = 5000
) -> Dict[str, Any]:
    """
    Finds nearby health facilities (hospitals, clinics, maternity centers) using Google Places API.
    Falls back to simulation mode if API key is not set.

    Args:
        location: Location string (city, address, coordinates)
        radius_meters: Search radius in meters (default: 5000 = 5km)

    Returns:
        dict: Dictionary containing:
            - status: "success" or "error"
            - facilities: List of nearby health facilities with details
            - count: Number of facilities found
            - error_message: Error description if status is "error"
    """
    # Simulation mode when API key is not set
    if _is_api_key_placeholder(GOOGLE_MAPS_API_KEY):
        location_lower = location.lower()

        # Simulated facilities for known cities
        simulated_facilities = {
            "lagos": [
                {
                    "name": "Lagos University Teaching Hospital",
                    "address": "Idi-Araba, Lagos",
                    "rating": 4.2,
                    "open_now": True,
                    "types": ["hospital", "emergency"],
                },
                {
                    "name": "Lagos Island Maternity Hospital",
                    "address": "Broad Street, Lagos Island",
                    "rating": 4.0,
                    "open_now": True,
                    "types": ["hospital", "maternity"],
                },
                {
                    "name": "Mainland Hospital Yaba",
                    "address": "Yaba, Lagos",
                    "rating": 3.8,
                    "open_now": True,
                    "types": ["hospital", "clinic"],
                },
            ],
            "bamako": [
                {
                    "name": "Hospital Gabriel Touré",
                    "address": "Commune III, Bamako",
                    "rating": 4.1,
                    "open_now": True,
                    "types": ["hospital", "emergency"],
                },
                {
                    "name": "Point G Hospital",
                    "address": "Point G, Bamako",
                    "rating": 4.3,
                    "open_now": True,
                    "types": ["hospital"],
                },
                {
                    "name": "Maternité Communautaire du Mali",
                    "address": "Commune IV, Bamako",
                    "rating": 3.9,
                    "open_now": True,
                    "types": ["hospital", "maternity"],
                },
            ],
            "accra": [
                {
                    "name": "Ridge Hospital",
                    "address": "Ridge, Accra",
                    "rating": 4.2,
                    "open_now": True,
                    "types": ["hospital"],
                },
                {
                    "name": "Korle Bu Teaching Hospital",
                    "address": "Korle Bu, Accra",
                    "rating": 4.4,
                    "open_now": True,
                    "types": ["hospital", "emergency"],
                },
                {
                    "name": "Princess Marie Louise Hospital",
                    "address": "Kinkole, Accra",
                    "rating": 4.0,
                    "open_now": True,
                    "types": ["hospital", "maternity"],
                },
            ],
        }

        for city, facilities_list in simulated_facilities.items():
            if city in location_lower:
                logger.info(
                    f"[SIMULATION] Found {len(facilities_list)} facilities near {location}"
                )
                return {
                    "status": "success",
                    "facilities": facilities_list,
                    "count": len(facilities_list),
                    "location": location,
                    "radius_meters": radius_meters,
                    "simulation": True,
                }

        # Default for unknown locations
        logger.warning(f"[SIMULATION] No facilities data for location: {location}")
        return {
            "status": "error",
            "error_message": f"No facilities found near {location}. Try: Lagos, Bamako, or Accra",
            "simulation": True,
        }

    try:
        # First, geocode the location to get coordinates
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geocode_params = {"address": location, "key": GOOGLE_MAPS_API_KEY}

        geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()

        if geocode_data["status"] != "OK" or not geocode_data["results"]:
            return {
                "status": "error",
                "error_message": f"Could not find location: {location}",
            }

        lat_lng = geocode_data["results"][0]["geometry"]["location"]
        location_str = f"{lat_lng['lat']},{lat_lng['lng']}"

        # Search for health facilities
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        places_params = {
            "location": location_str,
            "radius": radius_meters,
            "type": "hospital",  # Also matches clinics and health centers
            "key": GOOGLE_MAPS_API_KEY,
        }

        places_response = requests.get(places_url, params=places_params, timeout=10)
        places_response.raise_for_status()
        places_data = places_response.json()

        if places_data["status"] != "OK" and places_data["status"] != "ZERO_RESULTS":
            return {
                "status": "error",
                "error_message": f"Places API error: {places_data.get('status')}",
            }

        facilities = []
        for place in places_data.get("results", [])[:10]:  # Limit to top 10
            facility = {
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "rating": place.get("rating"),
                "open_now": place.get("opening_hours", {}).get("open_now"),
                "types": place.get("types", []),
            }
            facilities.append(facility)

        logger.info(f"Found {len(facilities)} health facilities near {location}")

        return {
            "status": "success",
            "facilities": facilities,
            "count": len(facilities),
            "search_location": location,
            "search_radius_km": radius_meters / 1000,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Places API error: {e}")
        return {
            "status": "error",
            "error_message": f"Error contacting Places API: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Unexpected error finding facilities: {e}")
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def assess_road_accessibility(location: str, destination: str = None) -> Dict[str, Any]:
    """
    Assesses road accessibility and travel information between locations.
    Useful for planning trips to health facilities near due date.
    Falls back to simulation mode if API key is not set.

    Args:
        location: Starting location (patient's location)
        destination: Destination (health facility). If None, finds nearest hospital

    Returns:
        dict: Dictionary containing:
            - status: "success" or "error"
            - distance: Distance in kilometers
            - duration: Travel time
            - route_available: Whether a route exists
            - travel_mode: Mode of transportation
            - error_message: Error description if status is "error"
    """
    # Simulation mode when API key is not set
    if _is_api_key_placeholder(GOOGLE_MAPS_API_KEY):
        location_lower = location.lower()

        simulated_routes = {
            "lagos": {
                "distance": "2.3 km",
                "duration": "15 mins",
                "start_address": location,
                "end_address": "Lagos University Teaching Hospital, Idi-Araba, Lagos",
                "traffic_note": "Moderate traffic during peak hours",
            },
            "bamako": {
                "distance": "1.8 km",
                "duration": "10 mins",
                "start_address": location,
                "end_address": "Hospital Gabriel Touré, Commune III, Bamako",
                "traffic_note": "Generally good road conditions",
            },
            "accra": {
                "distance": "1.5 km",
                "duration": "8 mins",
                "start_address": location,
                "end_address": "Ridge Hospital, Ridge, Accra",
                "traffic_note": "Excellent road access",
            },
        }

        for city, route_info in simulated_routes.items():
            if city in location_lower:
                logger.info(f"[SIMULATION] Assessed route from {location}")
                return {
                    "status": "success",
                    "route_available": True,
                    "travel_mode": "driving",
                    "simulation": True,
                    **route_info,
                }

        # Default for unknown locations
        logger.warning(f"[SIMULATION] No route data for location: {location}")
        return {
            "status": "success",
            "distance": "Unknown",
            "duration": "Unknown",
            "route_available": False,
            "travel_mode": "driving",
            "start_address": location,
            "end_address": "Nearest health facility",
            "simulation": True,
        }

    try:
        # If no destination, find nearest hospital first
        if not destination:
            facilities_result = find_nearby_health_facilities(
                location, radius_meters=10000
            )
            if (
                facilities_result["status"] == "success"
                and facilities_result["count"] > 0
            ):
                destination = facilities_result["facilities"][0]["address"]
            else:
                return {
                    "status": "error",
                    "error_message": "No health facilities found nearby for route planning",
                }

        # Use Google Maps Directions API
        directions_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": location,
            "destination": destination,
            "mode": "driving",
            "key": GOOGLE_MAPS_API_KEY,
        }

        response = requests.get(directions_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK" or not data.get("routes"):
            return {
                "status": "error",
                "error_message": f"No route found between locations. Status: {data.get('status')}",
            }

        route = data["routes"][0]
        leg = route["legs"][0]

        logger.info(f"Route assessed from {location} to {destination}")

        return {
            "status": "success",
            "distance": leg["distance"]["text"],
            "duration": leg["duration"]["text"],
            "route_available": True,
            "travel_mode": "driving",
            "start_address": leg["start_address"],
            "end_address": leg["end_address"],
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Directions API error: {e}")
        return {
            "status": "error",
            "error_message": f"Error contacting Directions API: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Unexpected error assessing accessibility: {e}")
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


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

# Create a specialized Nurse Agent for risk assessment with location and search tools
nurse_agent = LlmAgent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="nurse_agent",
    description="Senior Midwife specialist that assesses pregnancy risk levels, locates health facilities, searches emergency contacts, and provides medical information",
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

LOCATION-BASED ASSISTANCE:
- When a patient needs medical attention, use find_nearby_health_facilities tool
- Use the patient's location/country from their profile
- Prioritize facilities with good ratings and emergency capabilities
- Provide clear facility names, addresses, and contact information

EMERGENCY CONTACTS & HOTLINES:
- For HIGH RISK cases, ALWAYS use the `google_search` tool to find emergency contacts
- Call google_search with queries like:
  * "emergency pregnancy hotline [country]" 
  * "ambulance service [city] [country]"
  * "maternal health emergency contact [country]"
  * "24/7 pregnancy support hotline [country]"
- Look for: national health hotlines, ambulance services, maternity emergency numbers
- Include these contacts with phone numbers in your response to provide immediate help options

RESEARCH CAPABILITIES:
- Use the `google_search` tool to search for current medical guidelines when assessing complex cases
- Call google_search to look up condition-specific information for accurate assessments
- Use google_search to verify latest pregnancy care recommendations from WHO or local health authorities
- Search for local health services and resources available to the patient using google_search

RESPONSE FORMAT:
Always respond with a clear JSON structure:
{
  "risk_level": "Low|Moderate|High",
  "reasoning": "Step-by-step explanation of your assessment",
  "advice": "Clear, actionable advice for the patient",
  "nearest_facilities": "List of nearby health facilities if applicable"
}

Be professional, compassionate, and always prioritize patient safety.
""",
    tools=[
        FunctionTool(func=find_nearby_health_facilities),
        FunctionTool(func=get_local_health_facilities),
        GoogleSearchTool(
            bypass_multi_tools_limit=True
        ),  # Enable google_search with custom FunctionTools
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # Lower temperature for more consistent medical assessments
        safety_settings=[
            types.SafetySetting(category=cat, threshold=HarmBlockThreshold.BLOCK_NONE)
            for cat in SAFETY_SETTINGS.keys()
        ],
    ),
)

logger.info("✅ Nurse Agent created for risk assessment")

# Wrap nurse agent in App for proper tool handling
from google.adk.apps.app import (
    App as NurseApp,
    ResumabilityConfig as NurseResumabilityConfig,
)

nurse_app = NurseApp(
    name="nurse_coordinator",
    root_agent=nurse_agent,
    resumability_config=NurseResumabilityConfig(is_resumable=True),
)

logger.info("✅ Nurse App created")


# ============================================================================
# MCP PREGNANCY RECORD TOOLSET
# ============================================================================

# Create MCP toolset to connect to pregnancy record server
try:
    from mcp.client.stdio import StdioConnectionParams

    pregnancy_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python3", args=["pregnancy_mcp_server.py"]
            )
        )
    )
    logger.info("✅ Pregnancy MCP Toolset created")
except Exception as e:
    logger.error(f"Failed to create MCP toolset: {e}")
    pregnancy_mcp = None


# ============================================================================
# OPENAPI FACILITIES TOOLSET
# ============================================================================

# Create OpenAPI toolset for health facilities search
try:
    from pathlib import Path

    facilities_openapi_spec = Path(__file__).parent / "facilities_api.yaml"

    facilities_api = OpenAPIToolset(
        openapi_spec_path=str(facilities_openapi_spec),
        server_url="http://localhost:8080",
    )
    logger.info("✅ Facilities OpenAPI Toolset created")
except Exception as e:
    logger.error(f"Failed to create OpenAPI toolset: {e}")
    facilities_api = None


# ============================================================================
# MAIN PREGNANCY COMPANION AGENT
# ============================================================================

# Build tools list conditionally based on MCP and OpenAPI availability
# Wrap custom Python functions with FunctionTool for proper handling by gemini-2.5-flash-lite
# Use GoogleSearchTool with bypass_multi_tools_limit=True to enable alongside FunctionTools
agent_tools = [
    FunctionTool(func=calculate_edd),
    FunctionTool(func=calculate_anc_schedule),
    FunctionTool(func=infer_country_from_location),
    FunctionTool(func=assess_road_accessibility),
    FunctionTool(
        func=get_local_health_facilities
    ),  # MCP-style offline facility lookup (fallback)
    GoogleSearchTool(
        bypass_multi_tools_limit=True
    ),  # Enable google_search with custom FunctionTools
]

# Add MCP toolset if available
if pregnancy_mcp is not None:
    agent_tools.append(pregnancy_mcp)
    logger.info("✅ MCP toolset added to agent tools")
else:
    logger.warning("⚠️  MCP toolset not available, pregnancy records will not persist")

# Add OpenAPI facilities toolset if available
if facilities_api is not None:
    agent_tools.append(facilities_api)
    logger.info("✅ OpenAPI facilities toolset added to agent tools")
else:
    logger.warning("⚠️  OpenAPI toolset not available, using fallback facility lookup")

# Add nurse agent back now that we've identified google_search as the issue
agent_tools.append(AgentTool(agent=nurse_agent))

# Create the main Pregnancy Companion Agent with enhanced location and search capabilities
root_agent = LlmAgent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="pregnancy_companion",
    description="Pregnancy care companion with location awareness, nutrition guidance, health facility information, and emergency contact search",
    instruction="""
You are the 'Pregnancy Companion', a specialized medical AI providing support for pregnant women in West Africa.

YOUR ROLE:
You provide caring, evidence-based pregnancy support while prioritizing patient safety.
You have access to patient history through the session state and can perform calculations, risk assessments,
location-based assistance, and nutrition research.

OPERATIONAL PROTOCOL:

1. **Patient Identification & Profile**:
   - Check if you know the patient using get_pregnancy_by_phone tool (phone number is unique identifier)
   - If patient not found, collect: Name, Age, Phone, LMP, Country, Location
   - If location/country is missing, ask politely: "Where are you located so I can provide local information?"
   - If country is not provided but location is, use infer_country_from_location tool
   - Store/update patient information using upsert_pregnancy_record tool
   - Use simple language - avoid medical jargon, acronyms, and complex terms

2. **Calculate EDD (Due Date)**:
   - When the patient provides their LMP date, use the `calculate_edd` tool
   - The tool expects date format: YYYY-MM-DD (e.g., "2025-05-01")
   - Share the results in a friendly, understandable way
   - Note the weeks_remaining for travel planning purposes

3. **Nutrition Information**:
   - When patients ask about nutrition, use the `google_search` tool to get current, evidence-based advice
   - Call google_search with queries like:
     * "pregnancy nutrition guidelines WHO"
     * "foods to eat during pregnancy [trimester]"
     * "[country] traditional pregnancy foods"
     * "iron rich foods for pregnancy"
   - Recommend culturally appropriate foods available in the patient's country/location
   - Topics: pregnancy-safe foods, nutrients by trimester, foods to avoid, traditional pregnancy diets
   - Tailor advice to local context and traditional diets
   - Examples: iron-rich foods (beans, leafy greens), protein sources, hydration

4. **Health Facility Search**:
   - Use OpenAPI facilities tool to find nearby hospitals, clinics, and maternity centers
   - Provide facility details: name, address, distance, rating, services
   - Filter by type (hospital, maternity, emergency) based on patient needs
   - Include contact information and emergency availability

5. **Road Accessibility Assessment**:
   - As due date approaches (weeks_remaining < 4), proactively assess road accessibility
   - Use assess_road_accessibility tool with patient's location
   - Provide travel time and distance to nearest hospital
   - Advise on planning transportation in advance
   - Consider local conditions (rainy season, road quality)

6. **Risk Assessment - CRITICAL PROTOCOL**:
   - If the patient mentions ANY of these symptoms, you MUST call the `nurse_agent` tool:
     * Bleeding (any amount)
     * Dizziness, spots in vision, or fainting
     * Severe headaches
     * Fever
     * Severe pain
     * Reduced fetal movement
     * Severe swelling
   
   - When using `nurse_agent`, provide:
     * Patient summary (age, gestational week, location, relevant history)
     * Current symptoms described by the patient
   
   - After receiving the nurse's assessment:
     * Communicate the risk level clearly but compassionately
     * If HIGH RISK: Be firm but calm - urgent medical care needed. The nurse will provide emergency contacts.
     * If MODERATE RISK: Recommend scheduling appointment soon
     * If LOW RISK: Provide reassurance and general advice
   
   - For HIGH RISK cases, also use the `google_search` tool yourself to find:
     * Call google_search("emergency ambulance [country]")
     * Call google_search("national health emergency hotline [country]")
     * Call google_search("24/7 maternal health support [country]")
     * Call google_search("pregnancy emergency hotline [location]")
     * Provide phone numbers and contact information to the patient

7. **Communication Style**:
   - Use simple, caring language
   - Avoid medical jargon, acronyms, and abbreviations
   - Be culturally sensitive and respectful
   - Provide clear, actionable guidance
   - Never be alarmist, but be honest about risks

8. **Safety First**:
   - Always prioritize patient safety
   - When in doubt, recommend consulting healthcare provider
   - Provide emergency contact information for high-risk situations

REMEMBER: You are a support companion, not a replacement for medical care.
""",
    tools=agent_tools,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,  # Balanced for friendly yet consistent responses
        max_output_tokens=1024,
        safety_settings=[
            types.SafetySetting(category=cat, threshold=HarmBlockThreshold.BLOCK_NONE)
            for cat in SAFETY_SETTINGS.keys()
        ],
    ),
)

logger.info("✅ Pregnancy Companion Agent created")


# ============================================================================
# PAUSE/RESUME FUNCTIONALITY - Long-running Operations Support
# ============================================================================


async def pause_consultation(
    session_id: str, user_id: str, reason: str, last_topic: str = ""
) -> Dict[str, Any]:
    """
    Pause an ongoing consultation for later resumption.
    Useful for long consultations that span multiple interactions.

    Args:
        session_id: Session identifier
        user_id: User identifier
        reason: Reason for pausing (e.g., "patient_busy", "awaiting_test_results")
        last_topic: Last discussed topic for context

    Returns:
        dict: Status of pause operation
    """
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        if session:
            # Update session state with pause information
            session.state[STATE_PAUSED] = True
            session.state[STATE_PAUSE_REASON] = reason
            session.state[STATE_PAUSE_TIMESTAMP] = datetime.datetime.now().isoformat()
            session.state[STATE_LAST_TOPIC] = last_topic

            logger.info(f"Consultation paused: {session_id} - Reason: {reason}")

            return {
                "status": "success",
                "message": f"Consultation paused. Reason: {reason}",
                "session_id": session_id,
                "can_resume": True,
            }
        else:
            return {"status": "error", "error_message": "Session not found"}

    except Exception as e:
        logger.error(f"Error pausing consultation: {e}")
        return {"status": "error", "error_message": str(e)}


async def resume_consultation(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Resume a paused consultation.

    Args:
        session_id: Session identifier
        user_id: User identifier

    Returns:
        dict: Status and context for resumption
    """
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        if session and session.state.get(STATE_PAUSED, False):
            pause_reason = session.state.get(STATE_PAUSE_REASON, "unknown")
            pause_time = session.state.get(STATE_PAUSE_TIMESTAMP, "")
            last_topic = session.state.get(STATE_LAST_TOPIC, "general consultation")

            # Clear pause state
            session.state[STATE_PAUSED] = False

            logger.info(f"Consultation resumed: {session_id}")

            return {
                "status": "success",
                "message": "Consultation resumed",
                "session_id": session_id,
                "was_paused_reason": pause_reason,
                "pause_duration": pause_time,
                "last_topic": last_topic,
                "resume_context": f"Welcome back! We were discussing: {last_topic}",
            }
        else:
            return {
                "status": "error",
                "error_message": "Session not paused or not found",
            }

    except Exception as e:
        logger.error(f"Error resuming consultation: {e}")
        return {"status": "error", "error_message": str(e)}


async def resume_session_for_reminder(
    user_id: str,
    reminder_message: str,
    session_id: Optional[str] = None,
    create_if_missing: bool = True,
) -> Dict[str, Any]:
    """
    Resume or create a session to deliver a system-initiated reminder.

    This function is designed for the LoopAgent reminder system to:
    1. Find the user's most recent session OR create a new one
    2. Preserve conversation context if session exists
    3. Deliver the reminder message through the agent
    4. Handle cases where session doesn't exist

    Args:
        user_id: User identifier (typically phone number)
        reminder_message: The reminder message to deliver
        session_id: Optional specific session to resume (if None, finds most recent)
        create_if_missing: If True, creates new session if none exists

    Returns:
        dict: Status and agent response
    """
    try:
        # Find session
        target_session_id = session_id

        if not target_session_id:
            # Try to find user's most recent session
            # For now, create a reminder-specific session
            target_session_id = (
                f"reminder_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
            )
            logger.info(f"Creating reminder session: {target_session_id}")

        # Check if session exists
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=target_session_id
        )

        session_existed = session is not None

        # Create session if needed
        if not session and create_if_missing:
            await session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=target_session_id
            )
            logger.info(f"Created new reminder session: {target_session_id}")
            session = await session_service.get_session(
                app_name=APP_NAME, user_id=user_id, session_id=target_session_id
            )

        if not session:
            return {
                "status": "error",
                "error_message": "Could not create or find session",
                "user_id": user_id,
            }

        # Mark session as system-initiated
        session.state["system_initiated"] = True
        session.state["last_reminder_time"] = datetime.datetime.now().isoformat()

        # Deliver reminder through agent
        system_prompt = f"[SYSTEM REMINDER - Do not ask for confirmation, just deliver the message warmly]\n\n{reminder_message}"

        response = await run_agent_interaction(
            user_input=system_prompt, user_id=user_id, session_id=target_session_id
        )

        logger.info(f"Reminder delivered to {user_id} via session {target_session_id}")

        return {
            "status": "success",
            "session_id": target_session_id,
            "session_existed": session_existed,
            "reminder_delivered": True,
            "agent_response": response,
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error resuming session for reminder: {e}")
        return {"status": "error", "error_message": str(e), "user_id": user_id}


async def get_or_create_user_session(
    user_id: str, session_prefix: str = "session"
) -> Optional[str]:
    """
    Get user's most recent session ID or create a new one.

    Args:
        user_id: User identifier
        session_prefix: Prefix for session ID generation

    Returns:
        Session ID string or None if error
    """
    try:
        # For now, we create a new session each time
        # In production, you might query the session service for recent sessions
        session_id = f"{session_prefix}_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        logger.info(f"Created session: {session_id} for user: {user_id}")
        return session_id

    except Exception as e:
        logger.error(f"Error getting/creating session: {e}")
        return None


# ============================================================================
# SERVICES INITIALIZATION - Session and Memory Management
# ============================================================================

# Initialize ADK services
session_service = InMemorySessionService()
memory_service = DatabaseMemoryService(db_path="pregnancy_agent_memory.db")

# Import App for proper tool handling with gemini-2.5-flash-lite
from google.adk.apps.app import App, ResumabilityConfig

# Wrap the root agent in an App with resumability support
# This is required for proper function calling support with gemini-2.5-flash-lite
pregnancy_app = App(
    name=APP_NAME,
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

logger.info("✅ Pregnancy Companion App created with resumability")

# Create the Runner with the App - this orchestrates agent execution
runner = Runner(
    app=pregnancy_app,  # Pass the app instead of the agent directly
    session_service=session_service,
    memory_service=memory_service,
)

logger.info("✅ Runner initialized with PERSISTENT DATABASE memory service")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def run_agent_interaction(
    user_input: str, user_id: str = DEFAULT_USER_ID, session_id: Optional[str] = None
):
    """
    Run a single agent interaction with proper ADK patterns.
    Now includes OpenTelemetry tracing and pause/resume support.

    Args:
        user_input: The user's message
        user_id: User identifier for session management
        session_id: Optional session ID (creates new session if None)

    Returns:
        str: The agent's final response
    """
    # Start tracing span if available
    if TRACING_ENABLED and tracer:
        span = tracer.start_span("agent_interaction")
        span.set_attribute("user_id", user_id)
        span.set_attribute("session_id", session_id or "new")
        span.set_attribute("input_length", len(user_input))
    else:
        span = None

    try:
        # Create session if it doesn't exist or if session_id is provided but doesn't exist
        if session_id is None:
            session_id = (
                f"session_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

        # Check if session exists
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        # Create session if it doesn't exist
        if not session:
            await session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
            logger.info(f"Created new session: {session_id}")
            if span:
                span.add_event("session_created")

            # Get the newly created session
            session = await session_service.get_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )

        # Check if session is paused and handle resumption

        if session and session.state.get(STATE_PAUSED, False):
            resume_info = await resume_consultation(session_id, user_id)
            if resume_info["status"] == "success":
                logger.info(f"Resuming paused consultation: {session_id}")
                if span:
                    span.add_event("consultation_resumed")
                # Prepend resume context to user input
                user_input = (
                    f"[SYSTEM: {resume_info['resume_context']}]\n\nUser: {user_input}"
                )

        # Create user message
        user_message = types.Content(role="user", parts=[types.Part(text=user_input)])

        # Run the agent
        logger.info(f"User: {user_input}")
        if span:
            span.add_event("agent_execution_started")

        final_response = ""
        tool_calls = 0

        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=user_message
        ):
            # Log intermediate events for observability
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.debug(f"[{event.author}] {part.text[:100]}...")
                    # Track tool usage
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls += 1
                        if span:
                            span.add_event(f"tool_call_{part.function_call.name}")

            # Capture final response
            if event.is_final_response() and event.content and event.content.parts:
                final_response = "".join(
                    part.text or "" for part in event.content.parts
                )
                logger.info(f"Agent: {final_response}")
                if span:
                    span.set_attribute("response_length", len(final_response))
                    span.set_attribute("tool_calls", tool_calls)
                    span.add_event("agent_execution_completed")

        # Add session to memory for future recall
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        await memory_service.add_session_to_memory(session)

        if span:
            span.end()

        return final_response

    except Exception as e:
        logger.error(f"Error during agent interaction: {e}", exc_info=True)
        if span:
            span.set_attribute("error", True)
            span.set_attribute("error_message", str(e))
            span.end()
        return f"I apologize, but I encountered an error. Please try again or contact support if the issue persists."


def run_agent_interaction_sync(
    user_input: str, user_id: str = DEFAULT_USER_ID, session_id: Optional[str] = None
) -> str:
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

    return loop.run_until_complete(
        run_agent_interaction(user_input, user_id, session_id)
    )


# ============================================================================
# EVALUATION FUNCTION - LLM-as-a-Judge Pattern
# ============================================================================


async def evaluate_interaction(
    user_input: str, agent_response: str, expected_behavior: str
) -> Dict[str, Any]:
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
        ),
    )

    # Create temporary session for evaluation
    eval_session_id = f"eval_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    await session_service.create_session(
        app_name=APP_NAME, user_id="evaluator", session_id=eval_session_id
    )

    eval_runner = Runner(
        agent=eval_agent, app_name=APP_NAME, session_service=session_service
    )

    eval_message = types.Content(
        role="user", parts=[types.Part(text="Evaluate this interaction")]
    )

    eval_result = ""
    async for event in eval_runner.run_async(
        user_id="evaluator", session_id=eval_session_id, new_message=eval_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            eval_result = "".join(part.text or "" for part in event.content.parts)

    logger.info(f"📊 Evaluation result:\n{eval_result}")

    try:
        # Try to parse JSON response
        clean_result = eval_result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_result)
    except:
        return {
            "score": 0,
            "reasoning": eval_result,
            "error": "Could not parse evaluation JSON",
        }


# ============================================================================
# DEMO SCRIPT - Demonstrates all agent features
# ============================================================================


async def run_demo():
    """
    Run a complete demo showing all agent capabilities.
    This demonstrates: memory, tools, agent-as-a-tool, location features, nutrition search, and evaluation.
    """
    print("\n" + "=" * 70)
    print("PREGNANCY COMPANION AGENT - ENHANCED DEMO")
    print("Google ADK Compliant Implementation with Location & Search")
    print("=" * 70 + "\n")

    # Use a consistent session for the demo
    demo_session_id = "demo_amina_session_enhanced"
    demo_user_id = "amina_demo"

    # Create session
    await session_service.create_session(
        app_name=APP_NAME, user_id=demo_user_id, session_id=demo_session_id
    )

    print("👤 Patient: Amina (17 years old)")
    print("📍 Demonstrating NEW location-aware features")
    print("=" * 70 + "\n")

    # Turn 1: Introduction with Location
    print("--- TURN 1: PATIENT INTRODUCTION WITH LOCATION ---\n")
    response1 = await run_agent_interaction(
        "My name is Amina. I am 17. My LMP was May 1st 2025. I live in Bamako, Mali. I had a hemorrhage in my last birth.",
        user_id=demo_user_id,
        session_id=demo_session_id,
    )
    print(f"🤖 COMPANION: {response1}\n")

    # Turn 2: Nutrition Advice (Uses Google Search)
    print("\n--- TURN 2: NUTRITION GUIDANCE (Google Search Tool) ---\n")
    response2 = await run_agent_interaction(
        "What foods should I eat for my pregnancy? I want to know what's good for me and my baby.",
        user_id=demo_user_id,
        session_id=demo_session_id,
    )
    print(f"🤖 COMPANION: {response2}\n")

    # Turn 3: EDD Calculation with Road Accessibility
    print("\n--- TURN 3: DUE DATE & TRAVEL PLANNING ---\n")
    response3 = await run_agent_interaction(
        "When is my baby due? How far is the nearest hospital from my location?",
        user_id=demo_user_id,
        session_id=demo_session_id,
    )
    print(f"🤖 COMPANION: {response3}\n")

    # Turn 4: Symptom Check (Should trigger Nurse Agent with Location)
    print("\n--- TURN 4: DANGER SIGNS WITH HEALTH FACILITY SEARCH ---\n")
    response4 = await run_agent_interaction(
        "I am feeling dizzy and seeing spots. I need help urgently. Where can I go?",
        user_id=demo_user_id,
        session_id=demo_session_id,
    )
    print(f"🤖 COMPANION: {response4}\n")

    # Evaluate Turn 4 (Location-aware Risk Assessment)
    print("\n--- EVALUATION: LOCATION-AWARE RISK ASSESSMENT ---\n")
    evaluation = await evaluate_interaction(
        user_input="I am feeling dizzy and seeing spots. I need help urgently. Where can I go?",
        agent_response=response4,
        expected_behavior="Agent should recognize danger signs, consult nurse agent with location info, provide nearby health facilities, and communicate urgency clearly.",
    )

    print(f"📊 Evaluation Score: {evaluation.get('score', 'N/A')}/10")
    print(f"📋 Reasoning: {evaluation.get('reasoning', 'N/A')}\n")

    print("=" * 70)
    print("ENHANCED DEMO COMPLETE")
    print("=" * 70)
    print("\n✅ All features demonstrated:")
    print("  ✓ Session and memory management (ADK SessionService)")
    print("  ✓ Patient context retention with location/country")
    print("  ✓ Country inference from location (Custom tool)")
    print("  ✓ EDD calculation tool (ADK function tool)")
    print("  ✓ Google Search for nutrition guidance (ADK built-in tool)")
    print("  ✓ Health facility location search (Google Places API)")
    print("  ✓ Road accessibility assessment (Google Directions API)")
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
