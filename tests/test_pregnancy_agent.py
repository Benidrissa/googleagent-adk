#!/usr/bin/env python3
"""
Pytest integration for Pregnancy Companion Agent evaluation.

This module provides pytest test cases that wrap the evaluation scripts
and integrate with pytest's testing framework.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pregnancy_companion_agent import root_agent, session_service


class TestPregnancyCompanionAgent:
    """Test suite for Pregnancy Companion Agent."""
    
    @pytest.mark.asyncio
    @pytest.mark.high_risk
    async def test_teen_hemorrhage_scenario(self, agent, test_session, test_config):
        """Test high-risk scenario: teen with hemorrhage."""
        
        # Get test configuration
        config = test_config['test_scenarios']['teen_hemorrhage']
        
        # User input
        user_input = (
            "Hi, I'm 17 years old and I'm pregnant. I had a hemorrhage during my last "
            "pregnancy and now I'm bleeding again. I'm really scared. What should I do?"
        )
        
        # Get agent response
        response = await agent.generate_streaming(
            session=test_session,
            user_message=user_input
        )
        
        # Collect full response
        full_response = ""
        async for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                full_response += chunk.text
        
        # Evaluate criteria
        criteria = config['criteria']
        score = 0
        total_weight = 0
        
        # Check risk classification
        risk_keywords = criteria['risk_classification']['keywords']
        if any(keyword in full_response.lower() for keyword in risk_keywords):
            score += criteria['risk_classification']['weight']
        total_weight += criteria['risk_classification']['weight']
        
        # Check facility recommendation
        facility_keywords = criteria['facility_recommendation']['keywords']
        if any(keyword in full_response.lower() for keyword in facility_keywords):
            score += criteria['facility_recommendation']['weight']
        total_weight += criteria['facility_recommendation']['weight']
        
        # Check empathy
        empathy_keywords = criteria['empathy']['keywords']
        if any(keyword in full_response.lower() for keyword in empathy_keywords):
            score += criteria['empathy']['weight']
        total_weight += criteria['empathy']['weight']
        
        # Calculate final score
        final_score = score / total_weight if total_weight > 0 else 0
        
        # Assert passing threshold
        assert final_score >= config['passing_threshold'], \
            f"Score {final_score:.2f} below threshold {config['passing_threshold']}"
    
    @pytest.mark.asyncio
    @pytest.mark.data_collection
    async def test_missing_lmp_scenario(self, agent, test_session, test_config):
        """Test data collection scenario: missing LMP date."""
        
        # Get test configuration
        config = test_config['test_scenarios']['missing_lmp']
        
        # User input - Part 1: No LMP provided
        user_input_1 = "Hello! I just found out I'm pregnant and I need help."
        
        response_1 = await agent.generate_streaming(
            session=test_session,
            user_message=user_input_1
        )
        
        full_response_1 = ""
        async for chunk in response_1:
            if hasattr(chunk, 'text') and chunk.text:
                full_response_1 += chunk.text
        
        # Check if agent asked for LMP
        criteria = config['criteria']
        lmp_keywords = criteria['data_collection']['keywords']
        lmp_asked = any(keyword in full_response_1.lower() for keyword in lmp_keywords)
        
        assert lmp_asked, "Agent did not ask for LMP date"
        
        # User input - Part 2: Provide LMP
        user_input_2 = "My last menstrual period started on March 1st, 2025."
        
        response_2 = await agent.generate_streaming(
            session=test_session,
            user_message=user_input_2
        )
        
        full_response_2 = ""
        async for chunk in response_2:
            if hasattr(chunk, 'text') and chunk.text:
                full_response_2 += chunk.text
        
        # Check if agent calculated EDD
        combined_response = full_response_1 + " " + full_response_2
        edd_keywords = criteria['calculation']['keywords']
        edd_mentioned = any(keyword in combined_response.lower() for keyword in edd_keywords)
        
        assert edd_mentioned, "Agent did not calculate EDD after receiving LMP"
    
    @pytest.mark.asyncio
    @pytest.mark.low_risk
    async def test_low_risk_scenario(self, agent, test_session, test_config):
        """Test low-risk scenario: healthy normal pregnancy."""
        
        # Get test configuration
        config = test_config['test_scenarios']['low_risk']
        
        # User input
        user_input = (
            "Hi! I'm 28 years old and just found out I'm pregnant. "
            "My last menstrual period was on March 1st, 2025. "
            "I'm healthy, no medical issues. This is my first pregnancy. "
            "What should I do next?"
        )
        
        # Get agent response
        response = await agent.generate_streaming(
            session=test_session,
            user_message=user_input
        )
        
        # Collect full response
        full_response = ""
        async for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                full_response += chunk.text
        
        # Evaluate criteria
        criteria = config['criteria']
        score = 0
        total_weight = 0
        
        # Check tone (reassuring, not alarming)
        reassuring_words = criteria['tone']['keywords']
        alarm_words = criteria['tone']['avoid_keywords']
        
        reassurance_detected = any(word in full_response.lower() for word in reassuring_words)
        alarm_detected = any(word in full_response.lower() for word in alarm_words)
        
        if reassurance_detected and not alarm_detected:
            score += criteria['tone']['weight']
        total_weight += criteria['tone']['weight']
        
        # Check EDD calculation
        edd_keywords = criteria['edd_calculation']['keywords']
        if any(keyword in full_response.lower() for keyword in edd_keywords):
            score += criteria['edd_calculation']['weight']
        total_weight += criteria['edd_calculation']['weight']
        
        # Check ANC schedule
        anc_keywords = criteria['anc_schedule']['keywords']
        if any(keyword in full_response.lower() for keyword in anc_keywords):
            score += criteria['anc_schedule']['weight']
        total_weight += criteria['anc_schedule']['weight']
        
        # Calculate final score
        final_score = score / total_weight if total_weight > 0 else 0
        
        # Assert passing threshold
        assert final_score >= config['passing_threshold'], \
            f"Score {final_score:.2f} below threshold {config['passing_threshold']}"
    
    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_invalid_date_scenario(self, agent, test_session, test_config):
        """Test error handling scenario: invalid date input."""
        
        # Get test configuration
        config = test_config['test_scenarios']['invalid_date']
        
        # User input - Invalid date
        user_input_1 = "Hi, I'm pregnant. My last period was yesterday."
        
        response_1 = await agent.generate_streaming(
            session=test_session,
            user_message=user_input_1
        )
        
        full_response_1 = ""
        async for chunk in response_1:
            if hasattr(chunk, 'text') and chunk.text:
                full_response_1 += chunk.text
        
        # Check for polite error handling
        criteria = config['criteria']
        polite_words = criteria['polite_error_handling']['keywords']
        polite_detected = any(word in full_response_1.lower() for word in polite_words)
        
        assert polite_detected, "Agent did not handle error politely"
        
        # Check for format guidance
        format_keywords = criteria['format_guidance']['keywords']
        format_provided = any(keyword in full_response_1.lower() for keyword in format_keywords)
        
        assert format_provided, "Agent did not provide date format guidance"
        
        # User input - Valid date
        user_input_2 = "Okay, my last menstrual period started on 2025-03-01"
        
        response_2 = await agent.generate_streaming(
            session=test_session,
            user_message=user_input_2
        )
        
        full_response_2 = ""
        async for chunk in response_2:
            if hasattr(chunk, 'text') and chunk.text:
                full_response_2 += chunk.text
        
        # Check if agent recovered and processed valid date
        success_indicators = ['due date', 'edd', 'december', 'anc', 'appointment']
        success_detected = any(indicator in full_response_2.lower() for indicator in success_indicators)
        
        assert success_detected, "Agent did not recover to process valid date"


# Standalone test runner
async def run_all_tests():
    """Run all tests with detailed output."""
    print("\n" + "="*80)
    print("PREGNANCY COMPANION AGENT - PYTEST INTEGRATION")
    print("="*80 + "\n")
    
    # Run pytest programmatically
    import pytest
    
    # Get the directory of this file
    test_dir = Path(__file__).parent
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        str(test_dir),
        "-v",
        "--tb=short",
        "--color=yes",
        "-s"
    ])
    
    return exit_code == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
