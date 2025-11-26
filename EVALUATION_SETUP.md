# ADK Evaluation Framework Setup

## Status: Partial Implementation

### ✅ Completed

1. **Evaluation Configuration** (`tests/evaluation_config.json`)
   - Tool trajectory threshold: 90%
   - Response match threshold: 75%
   - Rubric-based tool use quality: 80%

2. **Test Scenarios Designed** (8 comprehensive cases)
   - Patient registration
   - ANC schedule calculation
   - High-risk emergency handling
   - Nutrition guidance
   - Low-risk reassurance
   - Health facility search
   - Moderate risk monitoring
   - Error handling

3. **Agent Module Structure**
   - Created `agent_eval/` package with `agent` attribute export
   - Required for ADK eval command compatibility

### ⚠️ Pending Issues

**ADK Eval Format Compatibility**:
The eval set JSON format requires specific structure that differs from documentation examples. Current blockers:

1. **EvalSet Schema Validation**:
   - `description` field not allowed in eval_cases
   - `data` field structure needs specific format
   - Pydantic validation errors prevent execution

2. **Format Investigation Needed**:
   - Need to examine ADK source code for exact schema
   - Alternative: Use Google Cloud Vertex AI Agent Builder for evaluation
   - Alternative: Build custom evaluation script using pytest

### 📋 Evaluation Approach Options

#### Option 1: Fix ADK Eval Format (Recommended)
```bash
# Investigate exact schema
python3 -c "from google.adk.evaluation import EvalSet; import inspect; print(inspect.getsource(EvalSet))"

# Update tests/pregnancy_agent_integration.evalset.json accordingly
```

#### Option 2: Custom Pytest Evaluation
```python
# Create tests/test_agent_evaluation.py
# Use agent directly with assertions
# More control, easier debugging
```

#### Option 3: Manual Testing Script
```bash
# Use existing test_observability.py pattern
# Extend with all 8 test scenarios
# Generate markdown report
```

### 🚀 Next Steps

1. **Immediate**: Document that evaluation framework is designed but format needs adjustment
2. **Short-term**: Choose evaluation approach (ADK vs pytest vs manual)
3. **Long-term**: Integrate with CI/CD for automated quality checks

### 📊 Current Evaluation Capability

Even without ADK eval running, the agent has:
- ✅ LoggingPlugin for observability
- ✅ Comprehensive test suite (tests/ directory)
- ✅ Manual test scripts (test_observability.py)
- ✅ Integration tests (test_live_integration.py)
- ✅ 33 working tests across all functionality

### 🔧 Evaluation Config Ready For

The created config files can be adapted for:
- Vertex AI Agent Builder eval
- Custom pytest evaluation harness
- CI/CD quality gates
- Manual regression testing

## Files Created

- `tests/evaluation_config.json` - Evaluation criteria
- `tests/pregnancy_agent_integration.evalset.json` - Test scenarios (needs format fix)
- `run_evaluation.py` - Setup validator script
- `agent_eval/__init__.py` - ADK-compatible agent module
- This file - Documentation of evaluation setup status
