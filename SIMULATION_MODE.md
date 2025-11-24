# 🎭 Simulation Mode

The Pregnancy Companion Agent includes a **simulation mode** that allows you to test all features without requiring Google API keys. This is perfect for development, testing, and demos.

## What Works Without API Keys

### ✅ Fully Functional (No API Required)

1. **EDD Calculator**
   - Calculate Expected Delivery Date from LMP
   - Determine gestational age and weeks remaining
   - No external dependencies

2. **MCP Local Database**
   - Offline health facility lookup
   - 8 facilities across 3 cities (Lagos, Bamako, Accra)
   - Emergency and maternity center information

### ✅ Simulation Mode (Placeholder API Key)

When `GOOGLE_MAPS_API_KEY` is not set or is a placeholder value:

1. **Country Inference**
   - Supports: Lagos, Bamako, Accra, Abuja, Kumasi, Sikasso, Port Harcourt, Kano
   - Returns country name and formatted location
   - Marked with `"simulation": true` flag

2. **Nearby Health Facilities**
   - Simulated facilities for Lagos, Bamako, Accra
   - Includes ratings, addresses, facility types
   - 3 facilities per city with realistic data

3. **Road Accessibility**
   - Estimated distances and travel times
   - Traffic condition notes
   - Route information for major cities

## What Requires API Keys

### ❌ Requires GOOGLE_API_KEY

- LLM conversation (Gemini 2.0 Flash)
- Natural language understanding
- Multi-turn dialogue
- Contextual responses
- Google Search integration

### ❌ Requires GOOGLE_MAPS_API_KEY (Real Data)

- Actual geocoding for unknown locations
- Real-time Google Places data
- Live traffic conditions
- Directions API for accurate routes

## Testing Simulation Mode

```bash
# Set placeholder or no API key
export GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"

# Run simulation test
python -c "
from pregnancy_companion_agent import (
    infer_country_from_location,
    find_nearby_health_facilities,
    assess_road_accessibility
)

# Country inference
result = infer_country_from_location('Lagos')
print(f'Country: {result[\"country\"]}')
print(f'Simulation: {result.get(\"simulation\", False)}')

# Nearby facilities
facilities = find_nearby_health_facilities('Bamako')
print(f'Found: {facilities[\"count\"]} facilities')
print(f'Simulation: {facilities.get(\"simulation\", False)}')

# Road accessibility
route = assess_road_accessibility('Accra')
print(f'Distance: {route[\"distance\"]}')
print(f'Simulation: {route.get(\"simulation\", False)}')
"
```

## Supported Cities

### Full Simulation Support
- **Lagos, Nigeria** - 3 facilities, route data
- **Bamako, Mali** - 3 facilities, route data
- **Accra, Ghana** - 3 facilities, route data

### Country Inference Only
- Abuja, Nigeria
- Kumasi, Ghana
- Sikasso, Mali
- Port Harcourt, Nigeria
- Kano, Nigeria

## Placeholder Detection

The simulation mode activates when `GOOGLE_MAPS_API_KEY` is:
- Not set (empty/None)
- `"YOUR_API_KEY_HERE"`
- `"your_google_maps_api_key_here"`
- `"your_api_key_here"`
- `"INSERT_API_KEY_HERE"`
- `"REPLACE_WITH_YOUR_KEY"`
- Less than 20 characters

## Response Format

All simulated responses include a `"simulation": true` flag:

```json
{
  "status": "success",
  "country": "Nigeria",
  "formatted_location": "Lagos, Nigeria",
  "simulation": true
}
```

## Use Cases

1. **Development**: Test agent logic without API costs
2. **Demos**: Show functionality without sharing API keys
3. **CI/CD**: Run tests in environments without credentials
4. **Offline Mode**: Work in areas with limited internet
5. **Training**: Learn the agent capabilities without setup

## Enabling Full Mode

To use real API data instead of simulation:

```bash
# Google AI API Key (required for LLM)
export GOOGLE_API_KEY="AIza..."

# Google Maps API Key (optional, enables real location data)
export GOOGLE_MAPS_API_KEY="AIza..."

# Run interactive demo
python interactive_demo.py
```

Get API keys:
- **GOOGLE_API_KEY**: https://aistudio.google.com/app/apikey
- **GOOGLE_MAPS_API_KEY**: https://console.cloud.google.com/google/maps-apis

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Request                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  API Key Check        │
         │  _is_api_key_placeholder() │
         └───────────┬───────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │Simulation│          │Real API  │
    │  Mode    │          │  Call    │
    └──────────┘          └──────────┘
          │                     │
          └──────────┬──────────┘
                     │
                     ▼
            ┌────────────────┐
            │   Response     │
            │ (with flag)    │
            └────────────────┘
```

## Best Practices

1. **Check Simulation Flag**: Always check for `simulation` flag in responses
2. **Log Mode**: Log whether running in simulation or real mode
3. **User Notification**: Inform users when in simulation mode
4. **Graceful Degradation**: Fall back to simulation on API errors
5. **Test Both Modes**: Verify functionality in both simulation and real modes

---

**Note**: Simulation data is based on real West African health facilities but should not be used for actual medical decisions. Always use real API keys for production deployments.
