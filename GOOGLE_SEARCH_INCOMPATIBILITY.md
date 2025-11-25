# Google Search with Custom FunctionTools - SOLVED ✅

## Solution

**Use `bypass_multi_tools_limit=True`** parameter when initializing GoogleSearchTool to enable it alongside custom FunctionTools.

```python
from google.adk.tools.google_search_tool import GoogleSearchTool

agent_tools = [
    FunctionTool(func=my_custom_function),
    GoogleSearchTool(bypass_multi_tools_limit=True),  # ✅ This enables compatibility!
]
```

## Previous Issue (Now Resolved)

**Previous Error**: `400 INVALID_ARGUMENT: Tool use with function calling is unsupported`

This occurred when using the singleton `google_search` object alongside FunctionTools without the bypass parameter.

## Testing Results

### ✅ WORKS
- gemini-2.5-flash-lite + FunctionTool(s) only (no google_search)
- gemini-2.5-flash-lite + google_search only (no FunctionTool)
- App + ResumabilityConfig + Runner pattern

### ❌ FAILS
- gemini-2.5-flash-lite + FunctionTool + google_search (mixed)

## Test Evidence

```python
# Test 1: ONE FunctionTool, no google_search → ✅ WORKS
agent_tools = [FunctionTool(func=calculate_edd)]
# Result: "Your estimated due date is February 5th, 2026..."

# Test 2: MULTIPLE FunctionTools, no google_search → ✅ WORKS  
agent_tools = [
    FunctionTool(func=calculate_edd),
    FunctionTool(func=calculate_anc_schedule),
    FunctionTool(func=infer_country_from_location),
    FunctionTool(func=assess_road_accessibility),
    FunctionTool(func=get_local_health_facilities),
]
# Result: Successfully processes patient info with location awareness

# Test 3: FunctionTools + google_search → ❌ FAILS
agent_tools = [
    FunctionTool(func=calculate_edd),
    google_search,  # Adding this breaks everything
]
# Result: "400 INVALID_ARGUMENT: Tool use with function calling is unsupported"
```

## Root Cause Analysis

The issue appears to be a limitation in gemini-2.5-flash-lite where:
1. It can handle custom functions (FunctionTool) correctly when wrapped in App pattern
2. It can handle built-in google_search tool independently  
3. But it **cannot handle both simultaneously**

This suggests google_search uses a different function calling mechanism that conflicts with FunctionTool's approach.

## Workarounds

### Option 1: Remove google_search (Current Implementation)
- **Pro**: All custom functions work perfectly
- **Con**: No web search capability for nutrition/medical info

### Option 2: Custom Web Search Function
Create a FunctionTool-wrapped custom search using an API:

```python
import requests

def search_web(query: str, num_results: int = 3) -> dict:
    """Search the web for information (DuckDuckGo or similar API)"""
    try:
        # Use DuckDuckGo HTML API or similar
        url = f"https://html.duckduckgo.com/html/?q={query}"
        response = requests.get(url, headers={"User-Agent": "PregnancyCompanionAgent/1.0"})
        # Parse and return results
        return {"status": "success", "results": [...]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Add as FunctionTool
agent_tools.append(FunctionTool(func=search_web))
```

### Option 3: Use Different Model for Search Tasks
- Keep gemini-2.5-flash-lite for main agent with custom functions
- Create separate agent with google_search using compatible model (gemini-2.0-flash-exp)
- Use AgentTool to delegate search queries

### Option 4: Manual Search Integration
- Prompt user to search externally when needed
- Provide specific search terms/queries for them to look up

## Recommendation

**Implement Option 2 (Custom Web Search)** for these reasons:
1. Maintains all custom function calling capabilities
2. Restores web search functionality 
3. Avoids model switching complexity
4. Uses free/open search APIs (DuckDuckGo)
5. Can be wrapped as FunctionTool like other custom functions

## Implementation Priority

**HIGH** - Web search is important for:
- Nutrition information queries
- Local health facility contact info
- Emergency services in specific regions
- Up-to-date medical guidelines

## Files Affected

- `pregnancy_companion_agent.py`: Line 1258 (google_search commented out)
- `test_custom_functions_flashlite.py`: Working reference without google_search

## Related Documentation

- `GOOGLE_SEARCH_IMPLEMENTATION.md`: Earlier investigation of google_search behavior
- `test_custom_functions_flashlite.py`: Validated Kaggle pattern implementation

## Status

**Date**: 2025-11-25
**Status**: IDENTIFIED - Workaround in place (google_search disabled)
**Next Step**: Implement custom web search as FunctionTool
