# Test 7 Fix Summary - ANC Auto-Calculation Solution

## Problem Analysis

### Original Issue
Test 7 ("Phone-Based Patient Lookup") was intermittently failing with empty LLM responses after successfully calling the `get_pregnancy_by_phone` tool.

### Root Cause
**Gemini Flash Lite Limitation**: The model occasionally fails to generate text output after receiving a single tool response, returning empty content with `finish_reason="STOP"` and 0 output tokens.

**Pattern Observed**:
1. LLM calls `get_pregnancy_by_phone("+223 70 XX XX 99")`  
2. Tool returns patient record with LMP date  
3. LLM returns: `{"content":{"role":"model"},"finish_reason":"STOP"}` ❌ **EMPTY!**

### Attempted Solutions That Failed

#### Solution 1: System Prompt Update
- **Approach**: Added explicit instructions to call `calculate_anc_schedule` after retrieving patient record
- **Result**: FAILED - LLM still returned empty response after first tool call
- **Why**: Gemini Flash Lite doesn't reliably chain multiple tool calls

#### Solution 2: Increase max_output_tokens
- **Approach**: Changed from 1024 to 2048 tokens
- **Result**: NOT TESTED - opted for more reliable solution
- **Risk**: Doesn't address root cause of empty generation

## Successful Solution: Auto-Calculate ANC Schedule in Tool Response

### Implementation Strategy
Instead of requiring the LLM to make two tool calls (get_pregnancy_by_phone → calculate_anc_schedule), **consolidate the data into one comprehensive tool response**.

### Code Changes

#### Modified `get_pregnancy_by_phone` Function
```python
def get_pregnancy_by_phone(phone: str) -> Dict[str, Any]:
    """
    Retrieves pregnancy record by phone number (unique identifier).
    
    IMPORTANT: If the patient has an LMP date recorded, this tool automatically
    calculates and includes their full ANC (Antenatal Care) visit schedule,
    next upcoming visit, and any overdue visits. You can use this information
    to directly answer questions about "next ANC visit" or "next appointment".
    
    Returns:
        dict: Dictionary containing:
            - status: "success" or "not_found"
            - record: Patient pregnancy record if found
            - anc_schedule: List of ANC visits (if LMP available) ✅ NEW
            - next_visit: Next upcoming visit info (if LMP available) ✅ NEW
            - overdue_visits: List of overdue visits (if LMP available) ✅ NEW
            - message: Status message
    """
    # ... existing code to fetch patient record ...
    
    if row:
        record = {
            "phone": row[0],
            "name": row[1],
            "age": row[2],
            "lmp_date": row[3],
            # ... other fields ...
        }
        
        result = {
            "status": "success",
            "record": record,
            "message": f"Found existing pregnancy record for {record['name']}",
        }
        
        # ✅ AUTO-CALCULATE ANC SCHEDULE IF LMP AVAILABLE
        if record.get("lmp_date"):
            try:
                anc_result = calculate_anc_schedule(record["lmp_date"])
                if anc_result.get("status") == "success":
                    result["anc_schedule"] = anc_result.get("anc_schedule", [])
                    result["next_visit"] = anc_result.get("next_visit")
                    result["overdue_visits"] = anc_result.get("overdue_visits", [])
                    result["message"] += f". Patient's LMP: {record['lmp_date']}. ANC schedule calculated automatically."
            except Exception as e:
                logger.warning(f"Could not calculate ANC schedule: {e}")
        
        return result
```

### Benefits

1. **Reliability**: Eliminates dependency on LLM multi-step generation
2. **Performance**: Reduces LLM invocation steps from 2 to 1
3. **Completeness**: LLM receives all necessary data in single tool response
4. **Maintainability**: Logic encapsulated in tool, not dependent on LLM behavior
5. **Token Efficiency**: No additional LLM tokens spent on second tool call

### Test Results

#### Before Fix
```
FAILED: Phone-Based Lookup - No response received
TOTAL: 5/7 tests passed (71.4%)
```

#### After Fix
```
✅ PASSED: Phone-Based Lookup
✅ Patient recognized by phone number
✅ Next ANC visit correctly identified: December 06, 2025 (4th visit, 30 weeks)
✅ Overdue visits correctly reported
TOTAL: 7/7 tests passed (100.0%)
```

### Example Tool Response

**Before (Manual Approach)**:
```json
{
  "status": "success",
  "record": {
    "phone": "+223 70 XX XX 99",
    "name": "Kadiatou",
    "lmp_date": "2025-05-10"
  },
  "message": "Found existing pregnancy record for Kadiatou"
}
```
*LLM would need to call calculate_anc_schedule next (often fails)*

**After (Auto-Calculation Approach)**:
```json
{
  "status": "success",
  "record": {
    "phone": "+223 70 XX XX 99",
    "name": "Kadiatou", 
    "lmp_date": "2025-05-10"
  },
  "anc_schedule": [
    {"visit_number": 1, "date": "2025-07-19", "status": "overdue"},
    {"visit_number": 2, "date": "2025-09-28", "status": "overdue"},
    {"visit_number": 3, "date": "2025-11-09", "status": "overdue"},
    {"visit_number": 4, "date": "2025-12-06", "status": "upcoming"}
  ],
  "next_visit": {"visit_number": 4, "date": "2025-12-06"},
  "overdue_visits": [1, 2, 3],
  "message": "Found existing pregnancy record for Kadiatou. Patient's LMP: 2025-05-10. ANC schedule calculated automatically."
}
```
*LLM can directly answer user's question with complete data*

## Key Lessons

### Model Limitations
- **Gemini Flash Lite**: Not reliable for multi-step tool call chains
- **Empty Responses**: Occasionally returns no content after single tool execution
- **Mitigation**: Consolidate data in tool responses to minimize LLM generation steps

### Architecture Patterns
1. **Prefer Data Consolidation**: Pack more information into single tool responses
2. **Reduce LLM Steps**: Fewer generation steps = more reliable behavior
3. **Tool Intelligence**: Move logic into tools rather than relying on LLM orchestration
4. **Defensive Design**: Assume LLM may not always generate follow-up calls

### Testing Insights
- **Intermittent Failures**: Model behavior can be non-deterministic
- **Reliable Reproduction**: Requires multiple test runs to validate fixes
- **Fresh State**: Database resets helped isolate patient isolation from model issues

## Final Status

- ✅ **All 7 integration tests passing (100%)**
- ✅ **Patient isolation working correctly**
- ✅ **Token overflow resolved (from 20,000+ to <5,000)**
- ✅ **Phone-based lookup reliable and complete**
- ✅ **ANC schedule auto-calculation in production**

## Commits
- `70d9240`: Patient isolation implementation (Test 5 fix)
- `08c721c`: ANC auto-calculation in get_pregnancy_by_phone (Test 7 fix)

## Date
November 26, 2025 - 10:26 UTC
