#!/usr/bin/env python3
"""
MCP Server for Pregnancy Records
Provides tools for managing pregnancy data storage and retrieval.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pregnancy-mcp-server")

# Simple in-memory database (will be replaced with SQLite in production)
pregnancy_records: Dict[str, Dict[str, Any]] = {
    "+1234567890": {
        "phone": "+1234567890",
        "name": "Sarah Johnson",
        "age": 25,
        "lmp_date": "2025-10-19",
        "edd": "2026-07-26",
        "location": "Lagos",
        "country": "Nigeria",
        "status": "active",
        "created_at": "2025-11-01T10:00:00Z",
        "updated_at": "2025-11-24T10:00:00Z"
    },
    "+2345678901": {
        "phone": "+2345678901",
        "name": "Amina Diallo",
        "age": 28,
        "lmp_date": "2025-06-09",
        "edd": "2026-03-16",
        "location": "Dakar",
        "country": "Senegal",
        "risk_level": "low",
        "status": "active",
        "created_at": "2025-06-15T10:00:00Z",
        "updated_at": "2025-11-24T10:00:00Z"
    }
}

# Load schema
SCHEMA_PATH = Path(__file__).parent / "pregnancy_schema.json"
with open(SCHEMA_PATH, 'r') as f:
    SCHEMA = json.load(f)

# Initialize MCP server
app = Server("pregnancy-record-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for pregnancy record management."""
    return [
        Tool(
            name="get_pregnancy_by_phone",
            description="Retrieve a pregnancy record by phone number",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number (e.g., +2347012345678)"
                    }
                },
                "required": ["phone"]
            }
        ),
        Tool(
            name="upsert_pregnancy_record",
            description="Create or update a pregnancy record",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number (unique identifier)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Patient's full name"
                    },
                    "lmp_date": {
                        "type": "string",
                        "description": "Last Menstrual Period date (YYYY-MM-DD format)"
                    },
                    "age": {
                        "type": "integer",
                        "description": "Patient's age in years"
                    },
                    "location": {
                        "type": "string",
                        "description": "Patient's location (city/town)"
                    },
                    "country": {
                        "type": "string",
                        "description": "Patient's country"
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "moderate", "high", "unknown"],
                        "description": "Assessed risk level"
                    },
                    "additional_data": {
                        "type": "object",
                        "description": "Additional data (medical_history, emergency_contact, etc.)"
                    }
                },
                "required": ["phone", "name", "lmp_date"]
            }
        ),
        Tool(
            name="list_active_pregnancies",
            description="List all active pregnancy records",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "completed", "inactive", "archived", "all"],
                        "description": "Filter by status (default: active)",
                        "default": "active"
                    }
                }
            }
        ),
        Tool(
            name="update_anc_visit",
            description="Mark an ANC visit as completed",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number"
                    },
                    "visit_number": {
                        "type": "integer",
                        "description": "Visit number (1-8)",
                        "minimum": 1,
                        "maximum": 8
                    },
                    "completed_date": {
                        "type": "string",
                        "description": "Date visit was completed (YYYY-MM-DD)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Visit notes"
                    }
                },
                "required": ["phone", "visit_number", "completed_date"]
            }
        ),
        Tool(
            name="delete_pregnancy_record",
            description="Delete a pregnancy record (use with caution)",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm deletion"
                    }
                },
                "required": ["phone", "confirm"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls for pregnancy record operations."""
    
    if name == "get_pregnancy_by_phone":
        return await get_pregnancy_by_phone(arguments)
    elif name == "upsert_pregnancy_record":
        return await upsert_pregnancy_record(arguments)
    elif name == "list_active_pregnancies":
        return await list_active_pregnancies(arguments)
    elif name == "update_anc_visit":
        return await update_anc_visit(arguments)
    elif name == "delete_pregnancy_record":
        return await delete_pregnancy_record(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def get_pregnancy_by_phone(arguments: Dict[str, Any]) -> List[TextContent]:
    """Retrieve pregnancy record by phone number."""
    phone = arguments["phone"]
    
    logger.info(f"Getting pregnancy record for phone: {phone}")
    
    if phone in pregnancy_records:
        record = pregnancy_records[phone]
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "record": record
            }, indent=2)
        )]
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "not_found",
                "message": f"No pregnancy record found for phone: {phone}"
            }, indent=2)
        )]

async def upsert_pregnancy_record(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create or update a pregnancy record."""
    phone = arguments["phone"]
    name = arguments["name"]
    lmp_date = arguments["lmp_date"]
    
    logger.info(f"Upserting pregnancy record for: {name} ({phone})")
    
    # Check if record exists
    is_update = phone in pregnancy_records
    
    # Create/update record
    if is_update:
        record = pregnancy_records[phone]
        record["name"] = name
        record["lmp_date"] = lmp_date
        record["updated_at"] = datetime.utcnow().isoformat() + "Z"
    else:
        record = {
            "phone": phone,
            "name": name,
            "lmp_date": lmp_date,
            "status": "active",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
    
    # Add optional fields
    if "age" in arguments:
        record["age"] = arguments["age"]
    if "location" in arguments:
        record["location"] = arguments["location"]
    if "country" in arguments:
        record["country"] = arguments["country"]
    if "risk_level" in arguments:
        record["risk_level"] = arguments["risk_level"]
    if "additional_data" in arguments:
        record.update(arguments["additional_data"])
    
    pregnancy_records[phone] = record
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "operation": "updated" if is_update else "created",
            "record": record
        }, indent=2)
    )]

async def list_active_pregnancies(arguments: Dict[str, Any]) -> List[TextContent]:
    """List pregnancy records filtered by status."""
    status_filter = arguments.get("status", "active")
    
    logger.info(f"Listing pregnancies with status: {status_filter}")
    
    if status_filter == "all":
        filtered_records = list(pregnancy_records.values())
    else:
        filtered_records = [
            record for record in pregnancy_records.values()
            if record.get("status") == status_filter
        ]
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "count": len(filtered_records),
            "records": filtered_records
        }, indent=2)
    )]

async def update_anc_visit(arguments: Dict[str, Any]) -> List[TextContent]:
    """Mark an ANC visit as completed."""
    phone = arguments["phone"]
    visit_number = arguments["visit_number"]
    completed_date = arguments["completed_date"]
    notes = arguments.get("notes", "")
    
    logger.info(f"Updating ANC visit {visit_number} for {phone}")
    
    if phone not in pregnancy_records:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"No pregnancy record found for phone: {phone}"
            }, indent=2)
        )]
    
    record = pregnancy_records[phone]
    
    # Initialize anc_schedule if not exists
    if "anc_schedule" not in record:
        record["anc_schedule"] = []
    
    # Update the specific visit
    visit_found = False
    for visit in record["anc_schedule"]:
        if visit["visit_number"] == visit_number:
            visit["status"] = "completed"
            visit["completed_date"] = completed_date
            if notes:
                visit["notes"] = notes
            visit_found = True
            break
    
    # If visit not found in schedule, add it
    if not visit_found:
        record["anc_schedule"].append({
            "visit_number": visit_number,
            "status": "completed",
            "completed_date": completed_date,
            "notes": notes
        })
    
    record["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "message": f"ANC visit {visit_number} marked as completed",
            "record": record
        }, indent=2)
    )]

async def delete_pregnancy_record(arguments: Dict[str, Any]) -> List[TextContent]:
    """Delete a pregnancy record."""
    phone = arguments["phone"]
    confirm = arguments.get("confirm", False)
    
    if not confirm:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": "Deletion requires explicit confirmation (confirm=true)"
            }, indent=2)
        )]
    
    logger.warning(f"Deleting pregnancy record for phone: {phone}")
    
    if phone in pregnancy_records:
        deleted_record = pregnancy_records.pop(phone)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Record deleted for {deleted_record.get('name', 'Unknown')}",
                "deleted_record": deleted_record
            }, indent=2)
        )]
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "not_found",
                "message": f"No record found for phone: {phone}"
            }, indent=2)
        )]

async def main():
    """Run the MCP server."""
    logger.info("Starting Pregnancy Record MCP Server...")
    logger.info(f"Loaded {len(pregnancy_records)} sample records")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pregnancy-record-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
