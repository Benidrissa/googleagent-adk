# Pregnancy Companion Agent

A comprehensive pregnancy care agent built with Google Agent Development Kit (ADK) with location-aware features for West Africa.

## Features

✅ **ADK Compliant Architecture**
- Built using Google ADK best practices
- Uses `LlmAgent`, `Runner`, and proper session management
- Follows ADK patterns for tools, agents, and observability

✅ **Core Capabilities**
- **Patient Memory**: Contextual conversation history and patient data retention
- **EDD Calculator**: Tool for calculating Estimated Due Date from LMP
- **Risk Assessment**: Nurse agent consultation using Agent-as-a-Tool pattern
- **Safety-First**: Medical safety guidelines with appropriate safety settings
- **Evaluation**: LLM-as-a-Judge for assessing agent performance

✅ **Location-Aware Features (NEW v2.0)**
- **Country & Location Profile**: Captures and stores patient location data
- **Country Inference**: Automatically infers country from location using Google Geocoding API
- **Google Search Integration**: Real ADK built-in tool for nutrition guidance and medical information
- **Health Facility Locator**: Finds nearby hospitals and clinics using Google Places API
- **Road Accessibility**: Assesses travel time and distance to health facilities using Google Directions API
- **Nutrition Guidance**: Uses Google Search to provide culturally-appropriate pregnancy nutrition advice
- **Pre-Delivery Planning**: Proactive route planning for expectant mothers nearing due date

✅ **Technical Features**
- Session and memory management (InMemorySessionService, InMemoryMemoryService)
- Real Google Search tool from `google.adk.tools` (not simulated)
- Custom Google Maps integration (Geocoding, Places, Directions APIs)
- Comprehensive logging using Python's standard logging module
- Proper error handling and fallbacks
- Async/await support for modern Python applications

## Installation

### Prerequisites
- Python 3.10 or higher
- Google ADK (`pip install google-adk>=1.19.0`)
- Google Cloud account (for Maps API - free tier available)

### Quick Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API keys:
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys:
# - GOOGLE_API_KEY: Get from https://aistudio.google.com/app/apikey
# - GOOGLE_MAPS_API_KEY: Get from https://console.cloud.google.com/
```

3. Enable Google Maps APIs (for location features):
   - Go to https://console.cloud.google.com/
   - Enable: Geocoding API, Places API, Directions API
   - See [SETUP_LOCATION.md](SETUP_LOCATION.md) for detailed instructions

### Alternative: Environment Variables

```bash
export GOOGLE_API_KEY="your_api_key_here"
export GOOGLE_MAPS_API_KEY="your_maps_api_key_here"  # Can be same as above
```

### Documentation

- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Location Features**: See [LOCATION_FEATURES.md](LOCATION_FEATURES.md) 
- **Location Setup**: See [SETUP_LOCATION.md](SETUP_LOCATION.md)

## Usage

### Running the Demo

The simplest way to see all features in action:

```bash
python pregnancy_companion_agent.py
```

This runs a complete demo showing:
- Patient introduction with history
- Risk assessment with danger signs
- EDD calculation
- Evaluation of agent performance

### Using ADK CLI

You can also run the agent using ADK's web interface:

```bash
# From the parent directory containing this folder
adk web --port 8000
```

Then open http://localhost:8000 in your browser.

### Programmatic Usage

```python
import asyncio
from pregnancy_companion_agent import run_agent_interaction

# Run a single interaction
async def main():
    response = await run_agent_interaction(
        "My name is Sarah. My LMP was January 15, 2025.",
        user_id="sarah_001"
    )
    print(response)

asyncio.run(main())
```

### Synchronous Usage

```python
from pregnancy_companion_agent import run_agent_interaction_sync

response = run_agent_interaction_sync(
    "When is my baby due?",
    user_id="sarah_001"
)
print(response)
```

## Architecture

### Components

1. **Main Agent** (`root_agent`): 
   - LlmAgent configured for pregnancy care
   - Uses Gemini 2.0 Flash model
   - Equipped with tools and instructions

2. **Tools**:
   - `calculate_edd`: Function tool for EDD calculation
   - `nurse_agent` (via AgentTool): Specialized risk assessment agent

3. **Services**:
   - `InMemorySessionService`: Manages conversation sessions
   - `InMemoryMemoryService`: Stores long-term knowledge
   - `Runner`: Orchestrates agent execution

### Agent-as-a-Tool Pattern

The Nurse Agent is used as a tool by the main agent:

```python
nurse_agent = LlmAgent(...)  # Specialized risk assessment agent

root_agent = LlmAgent(
    tools=[
        calculate_edd,
        AgentTool(agent=nurse_agent)  # Nurse as a tool
    ]
)
```

When the main agent detects symptoms, it calls the nurse agent for specialized risk assessment.

## Safety

The agent uses appropriate safety settings for medical applications:

- Safety filters set to `BLOCK_NONE` to allow discussion of medical symptoms
- Risk assessment protocols for pregnancy danger signs
- Clear communication about when to seek urgent medical care
- Agent is a support companion, not a replacement for medical care

⚠️ **Important**: This is a demonstration agent. For production medical applications:
- Review and adjust safety settings
- Implement proper medical review processes
- Add appropriate disclaimers
- Ensure compliance with healthcare regulations

## Evaluation

The agent includes LLM-as-a-Judge evaluation:

```python
evaluation = await evaluate_interaction(
    user_input="I am feeling dizzy",
    agent_response=agent_response,
    expected_behavior="Should recognize danger signs and consult nurse"
)
```

Evaluation criteria:
- Medical intent identification
- Specialist consultation when needed
- Medical safety of advice
- Communication clarity
- Avoidance of jargon

## Logging and Observability

The agent uses Python's standard logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

Log levels:
- `INFO`: Agent lifecycle, tool calls, major events
- `DEBUG`: Detailed prompts, LLM requests/responses
- `WARNING`: Potential issues
- `ERROR`: Failures and exceptions

## Extending the Agent

### Adding New Tools

```python
def new_tool(param: str) -> Dict[str, Any]:
    """Tool description for the LLM."""
    # Implementation
    return {"status": "success", "result": "..."}

# Add to root_agent tools
root_agent = LlmAgent(
    tools=[calculate_edd, AgentTool(agent=nurse_agent), new_tool]
)
```

### Customizing Instructions

Edit the `instruction` parameter in `root_agent` to change behavior:

```python
root_agent = LlmAgent(
    instruction="""
    Your custom instructions here...
    """
)
```

### Using Different Memory Services

Replace `InMemoryMemoryService` with `VertexAiMemoryBankService` for persistent, semantic memory:

```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="your-gcp-project",
    location="us-central1",
    agent_engine_id="your-agent-engine-id"
)
```

## ADK Compliance Checklist

✅ Uses `LlmAgent` for agent definition  
✅ Uses `Runner` for agent execution  
✅ Uses `InMemorySessionService` for session management  
✅ Uses `InMemoryMemoryService` for memory  
✅ Function tools follow ADK patterns (proper signatures, docstrings, return types)  
✅ Agent-as-a-Tool pattern for multi-agent architecture  
✅ Proper logging using Python's logging module  
✅ Safety settings configured appropriately  
✅ Event-based async execution  
✅ Evaluation using ADK agents  

## Contributing

When contributing to this agent:

1. Follow ADK best practices
2. Maintain comprehensive docstrings
3. Test all features thoroughly
4. Update this README with changes
5. Ensure backward compatibility

## License

This is a demonstration project for educational purposes.

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python Reference](https://google.github.io/adk-docs/api-reference/python/)
- [Get Your API Key](https://aistudio.google.com/app/apikey)

## Support

For issues or questions:
1. Check the ADK documentation
2. Review the code comments
3. Enable DEBUG logging for troubleshooting
4. Consult the ADK community resources
