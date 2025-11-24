"""
Pytest configuration and fixtures for Pregnancy Companion Agent tests.

This module provides shared fixtures and setup for all test scenarios.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service
from google.adk.sessions import InMemorySessionService


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def agent():
    """Provide the root agent for testing."""
    return root_agent


@pytest.fixture
async def session_service_fixture():
    """Provide the session service for testing."""
    return session_service


@pytest.fixture
async def test_session(session_service_fixture):
    """Create a fresh test session."""
    session_id = f"test_session_{id(asyncio.current_task())}"
    user_id = f"test_user_{id(asyncio.current_task())}"
    session = await session_service_fixture.get_or_create_session(session_id, user_id)
    return session


@pytest.fixture
def test_config():
    """Load test configuration."""
    import json
    config_path = Path(__file__).parent / "test_config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "high_risk: mark test as high-risk scenario requiring urgent care"
    )
    config.addinivalue_line(
        "markers", "data_collection: mark test as data collection scenario"
    )
    config.addinivalue_line(
        "markers", "low_risk: mark test as low-risk/routine care scenario"
    )
    config.addinivalue_line(
        "markers", "error_handling: mark test as error handling scenario"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        if "teen_hemorrhage" in item.nodeid:
            item.add_marker(pytest.mark.high_risk)
        elif "missing_lmp" in item.nodeid:
            item.add_marker(pytest.mark.data_collection)
        elif "low_risk" in item.nodeid:
            item.add_marker(pytest.mark.low_risk)
        elif "invalid_date" in item.nodeid:
            item.add_marker(pytest.mark.error_handling)
