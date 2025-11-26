#!/usr/bin/env python3
"""
Pregnancy Companion Agent - Evaluation Runner

This script runs comprehensive evaluations using the ADK evaluation framework.
It assesses tool usage, response quality, and agent behavior against defined criteria.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "=" * 80)
print("PREGNANCY COMPANION AGENT - EVALUATION SUITE")
print("=" * 80 + "\n")

# Display evaluation configuration
print("📋 EVALUATION CONFIGURATION:")
print("-" * 80)

config_path = Path("tests/evaluation_config.json")
if config_path.exists():
    with open(config_path, "r") as f:
        config = json.load(f)

    print("\n✅ Evaluation Criteria Loaded:")
    for criterion, value in config["criteria"].items():
        if criterion == "rubric_based_tool_use_quality_v1":
            print(f"\n📊 {criterion}:")
            print(f"   Rubric: {value['rubric'][:100]}...")
        else:
            print(f"  • {criterion}: {value}")
else:
    print("❌ Evaluation configuration not found!")
    sys.exit(1)

print("\n" + "-" * 80)

# Display test cases
print("\n🧪 EVALUATION TEST CASES:")
print("-" * 80)

evalset_path = Path("tests/pregnancy_agent_integration.evalset.json")
if evalset_path.exists():
    with open(evalset_path, "r") as f:
        evalset = json.load(f)

    print(f"\n📦 Eval Set ID: {evalset['eval_set_id']}")
    print(f"📝 Description: {evalset['description']}")
    print(f"\n✅ {len(evalset['eval_cases'])} Test Cases Loaded:\n")

    for i, case in enumerate(evalset["eval_cases"], 1):
        print(f"{i}. {case['eval_id']}")
        print(f"   Description: {case['description']}")
        user_msg = case["conversation"][0]["user_content"]["parts"][0]["text"]
        print(
            f'   User Input: "{user_msg[:80]}..."'
            if len(user_msg) > 80
            else f'   User Input: "{user_msg}"'
        )
        tool_count = len(case["conversation"][0]["intermediate_data"]["tool_uses"])
        print(f"   Expected Tools: {tool_count}")
        print()
else:
    print("❌ Evaluation test cases not found!")
    sys.exit(1)

print("-" * 80)

print("\n🎯 EVALUATION WILL ASSESS:")
print("  1. Tool Trajectory - Correct tool selection and usage")
print("  2. Response Quality - Text similarity to expected responses")
print("  3. Rubric Adherence - Following agent behavior guidelines")
print()

print("📊 SCORING THRESHOLDS:")
print(
    f"  • Tool Trajectory: {config['criteria']['tool_trajectory_avg_score'] * 100}% accuracy required"
)
print(
    f"  • Response Match: {config['criteria']['response_match_score'] * 100}% similarity required"
)
print()

print("=" * 80)
print("\n🚀 TO RUN EVALUATION, EXECUTE THIS COMMAND:\n")
print("adk eval pregnancy_companion_agent \\")
print("    tests/pregnancy_agent_integration.evalset.json \\")
print("    --config_file_path=tests/evaluation_config.json \\")
print("    --print_detailed_results")
print()
print("=" * 80)

print("\n📈 INTERPRETING RESULTS:")
print("-" * 80)
print(
    """
EXAMPLE ANALYSIS:

Test Case: new_patient_registration
  ✅ tool_trajectory_avg_score: 1.0/0.9
  ❌ response_match_score: 0.65/0.75

📊 What this tells us:
  • TOOL USAGE: Perfect - Agent used correct tools in correct order
  • RESPONSE QUALITY: Needs improvement - Response text differs from expected
  • ROOT CAUSE: Communication style, not technical capability

🎯 ACTIONABLE INSIGHTS:
  1. Technical capability works (tool usage perfect)
  2. Response wording needs adjustment (failed similarity threshold)
  3. Fix: Update system prompt for more consistent language
  4. Or: Lower response_match_score threshold if variation is acceptable

KEY METRICS:
  • tool_trajectory_avg_score = 1.0: Perfect tool usage
  • tool_trajectory_avg_score = 0.5: Some tools wrong or missing
  • tool_trajectory_avg_score = 0.0: Completely wrong tool usage
  
  • response_match_score = 1.0: Exact text match
  • response_match_score = 0.8: Very similar, minor wording differences
  • response_match_score = 0.5: Partially similar, significant differences
  • response_match_score = 0.0: Completely different response
"""
)

print("\n" + "=" * 80)
print("EVALUATION SETUP COMPLETE ✅")
print("=" * 80 + "\n")

print("💡 TIP: Run with --print_detailed_results to see full comparison")
print("💡 TIP: Adjust thresholds in evaluation_config.json as needed")
print()
