"""
Pregnancy Companion Agent Package
Google ADK Compliant Implementation
"""

from .pregnancy_companion_agent import (
    root_agent,
    runner,
    run_agent_interaction_sync,
    run_agent_interaction,
    evaluate_interaction,
    run_demo
)

__version__ = "1.0.0"
__all__ = [
    "root_agent",
    "runner", 
    "run_agent_interaction_sync",
    "run_agent_interaction",
    "evaluate_interaction",
    "run_demo"
]
