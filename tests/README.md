# Pregnancy Companion Agent - Evaluation Suite

This directory contains the evaluation suite for testing the Pregnancy Companion Agent across various scenarios.

## Quick Start

### Run All Tests
```bash
python run_all_tests.py
```

### Run with Pytest
```bash
pytest . -v --tb=short
```

### Run Individual Test
```bash
python test_teen_hemorrhage.py
python test_missing_lmp.py
python test_low_risk.py
python test_invalid_date.py
```

## Test Scenarios

| Test File | Scenario | Criteria | Threshold |
|-----------|----------|----------|-----------|
| `test_teen_hemorrhage.py` | High-risk: Teen with hemorrhage | 5 | 60% |
| `test_missing_lmp.py` | Data collection: Missing LMP | 5 | 60% |
| `test_low_risk.py` | Routine care: Normal pregnancy | 6 | 67% |
| `test_invalid_date.py` | Error handling: Invalid dates | 6 | 67% |

## Configuration

- `test_config.json` - Evaluation criteria and scoring rubrics
- `conftest.py` - Pytest fixtures and configuration

## Pytest Integration

The suite includes pytest integration with custom markers:

- `@pytest.mark.high_risk` - High-risk scenarios
- `@pytest.mark.data_collection` - Data collection flows
- `@pytest.mark.low_risk` - Routine care scenarios
- `@pytest.mark.error_handling` - Error handling tests

### Run by Category
```bash
pytest . -m high_risk -v
pytest . -m data_collection -v
pytest . -m low_risk -v
pytest . -m error_handling -v
```

## Test Structure

Each test file:
1. Creates a session for the test scenario
2. Sends user input to the agent
3. Evaluates agent response against criteria
4. Calculates score and determines pass/fail
5. Returns detailed results

## Evaluation Criteria

Tests evaluate multiple aspects:
- **Risk Assessment**: Correct classification of pregnancy risk level
- **Tool Usage**: Appropriate use of agent tools (calculate_edd, nurse_agent, etc.)
- **Communication**: Empathy, clarity, age-appropriate language
- **Safety**: No harmful advice, appropriate urgency
- **Data Handling**: Correct information collection and processing
- **Error Recovery**: Graceful handling of invalid input

## Requirements

```bash
pip install pytest pytest-asyncio
```

## CI/CD Integration

Add to `.github/workflows/test.yml`:
```yaml
- name: Run Evaluation Tests
  run: |
    pytest tests/ -v --tb=short
```

## Results Interpretation

### Score Ranges
- **90-100%**: Excellent - Agent performs exceptionally
- **75-89%**: Good - Minor improvements needed
- **60-74%**: Acceptable - Passes minimum threshold
- **40-59%**: Needs Improvement - Below standard
- **0-39%**: Poor - Requires significant revision

### Passing Threshold
- High-risk tests: 60% (3/5 criteria)
- Low-risk tests: 67% (4/6 criteria)
- Error handling: 67% (4/6 criteria)

## Troubleshooting

### Tests Timeout
Increase timeout in `run_all_tests.py`:
```python
timeout=180  # Increase from 120
```

### Agent Not Responding
Ensure the agent is properly initialized:
```bash
python -c "from pregnancy_companion_agent import root_agent; print(root_agent)"
```

### Session Issues
Clear any existing sessions:
```bash
rm -rf .adk_sessions/  # If session directory exists
```

## Future Enhancements

- [ ] ADK native evaluation integration
- [ ] Tool trajectory validation
- [ ] LLM-as-a-Judge scoring
- [ ] Performance benchmarks
- [ ] Multi-language support
- [ ] Real user feedback integration

## Documentation

See `SECTION_1.4_SUMMARY.md` for comprehensive implementation details.

## Contact

For questions or issues with the evaluation suite, please open an issue in the repository.

---

**Last Updated:** 2025-11-24  
**Status:** ✅ Production Ready
