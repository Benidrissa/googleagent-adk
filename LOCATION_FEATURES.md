# Location-Aware Features Documentation

## Overview

The Pregnancy Companion Agent now includes comprehensive location-aware features using **real Google ADK tools** (Google Search) and **Google Maps API integration** (Places, Geocoding, Directions).

## New Features (v2.0)

### 1. User Profile with Country & Location

**Feature**: Patients can provide their location and country, which is stored in their session profile.

**Implementation**:
- Session state now tracks `country` and `location` fields
- Agent asks for location during initial consultation
- Location data is used for all location-based services

**Example**:
```
User: "I live in Bamako, Mali"
Agent: [Stores location="Bamako, Mali", country="Mali" in session]
```

### 2. Country Inference from Location

**Feature**: If only location is provided, the system automatically infers the country using geocoding.

**Tool**: `infer_country_from_location(location: str)`

**API Used**: Google Maps Geocoding API

**How it works**:
1. Takes location string (city, address, region, etc.)
2. Calls Google Geocoding API
3. Extracts country from address components
4. Returns formatted location and country name

**Example**:
```python
result = infer_country_from_location("Bamako")
# Returns: {"country": "Mali", "formatted_location": "Bamako, Mali"}
```

### 3. Google Search Tool Integration

**Feature**: Real Google Search capability for finding pregnancy-related information, especially nutrition guidance.

**Tool**: `google_search` (ADK built-in tool from `google.adk.tools`)

**Used by**:
- **Companion Agent**: Searches for nutrition information, pregnancy-safe foods, cultural dietary practices
- **Nurse Agent**: Searches for medical guidelines, condition-specific information

**Configuration**: Uses `bypass_multi_tools_limit=True` to combine with custom function tools

**Example Use Cases**:
- "What foods should I eat during pregnancy in Mali?"
  - Searches: "pregnancy nutrition Mali", "iron-rich foods West Africa"
- "What foods should I avoid?"
  - Searches: "foods to avoid during pregnancy", "pregnancy dietary restrictions"

### 4. Health Facility Location Search

**Feature**: Finds nearby hospitals, clinics, and maternity centers using Google Places API.

**Tool**: `find_nearby_health_facilities(location: str, radius_meters: int = 5000)`

**API Used**: 
- Google Maps Geocoding API (to get coordinates)
- Google Places API Nearby Search (to find facilities)

**Returns**:
- List of nearby health facilities (up to 10)
- Facility name, address, rating, open status
- Facility types (hospital, clinic, health center)
- Search radius and location

**Example**:
```python
result = find_nearby_health_facilities("Bamako, Mali", radius_meters=5000)
# Returns facilities within 5km of Bamako
```

**Used by Nurse Agent**:
- When patient reports danger signs
- When urgent care is needed
- Automatic facility search with patient's location

### 5. Road Accessibility Assessment

**Feature**: Assesses travel time and distance to health facilities, critical for planning near due date.

**Tool**: `assess_road_accessibility(location: str, destination: str = None)`

**API Used**: Google Maps Directions API

**How it works**:
1. If no destination provided, finds nearest hospital first
2. Calculates driving route between locations
3. Returns distance, duration, and route availability

**Returns**:
- Distance (e.g., "3.5 km")
- Duration (e.g., "12 mins")
- Start and end addresses
- Route availability status

**Proactive Use**:
- Companion agent checks accessibility when due date approaches (< 4 weeks remaining)
- Advises on transportation planning
- Considers local conditions (rainy season, road quality)

**Example**:
```python
result = assess_road_accessibility("Bamako city center", "Hospital Gabriel Touré")
# Returns: {"distance": "5.2 km", "duration": "15 mins", "route_available": True}
```

### 6. Nutrition Guidance via Google Search

**Feature**: Companion agent uses Google Search to provide culturally-appropriate, evidence-based nutrition advice.

**Implementation**:
- Agent automatically searches for pregnancy nutrition information
- Tailors searches to patient's country/location
- Focuses on locally available foods
- Provides trimester-specific guidance

**Search Examples**:
- "pregnancy nutrition [Country]"
- "iron-rich foods pregnancy [Location]"
- "traditional pregnancy diet [Culture]"
- "foods to avoid pregnancy"
- "pregnancy vitamins recommendations"

**Result**:
- Evidence-based nutrition advice
- Culturally appropriate food suggestions
- Foods to avoid
- Supplement recommendations

### 7. Health Facility Finder for Nurse Agent

**Feature**: Nurse agent can locate nearby health facilities when assessing high-risk situations.

**Workflow**:
1. Patient reports danger signs
2. Nurse agent assesses risk level
3. If HIGH or MODERATE risk:
   - Calls `find_nearby_health_facilities` with patient's location
   - Provides facility names, addresses, and ratings
   - Advises immediate care with specific location information

**Example Response**:
```
"You need immediate medical attention. Here are the nearest facilities:

1. Hospital Gabriel Touré
   - Address: Rue 40, Bamako
   - Rating: 4.2/5
   - Status: Open now

2. Centre de Santé Communautaire
   - Address: Avenue Moussa Tavele, Bamako
   - Rating: 3.8/5
```

## API Configuration

### Required API Keys

1. **GOOGLE_API_KEY**: For Gemini models and Google Search
   - Get from: https://aistudio.google.com/app/apikey

2. **GOOGLE_MAPS_API_KEY**: For location services
   - Get from: https://console.cloud.google.com/google/maps-apis
   - Can be same as GOOGLE_API_KEY if Maps APIs are enabled

### Required Google Maps APIs

Enable these in Google Cloud Console:

1. **Geocoding API**: For country inference
2. **Places API**: For health facility search
3. **Directions API**: For route planning

### Environment Setup

```bash
# .env file
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_maps_api_key  # or same as above
```

## Architecture

### Tool Distribution

**Companion Agent Tools**:
- `calculate_edd` - EDD calculation
- `infer_country_from_location` - Country inference
- `assess_road_accessibility` - Route planning
- `google_search` - Nutrition and pregnancy information
- `nurse_agent` - Risk assessment (Agent-as-a-Tool)

**Nurse Agent Tools**:
- `google_search` - Medical guidelines and research
- `find_nearby_health_facilities` - Health facility location

### ADK Compliance

✅ **Google Search**: Built-in ADK tool from `google.adk.tools`
- Uses `bypass_multi_tools_limit=True` for compatibility with custom tools

✅ **Custom Location Tools**: Proper ADK function tool patterns
- Type hints for all parameters
- Comprehensive docstrings
- Dict return values with status indicators
- Error handling and logging

✅ **Agent Configuration**: 
- Safety settings for medical content (BLOCK_NONE)
- Appropriate temperature settings (0.7 for companion, 0.2 for nurse)
- Tool integration following ADK patterns

## Usage Examples

### Example 1: New Patient with Location

```python
# Patient provides location
response = await run_agent_interaction(
    "Hi, I'm Amina from Bamako, Mali. I'm pregnant.",
    user_id="amina_001",
    session_id="session_001"
)
# Agent stores location and country in session
```

### Example 2: Nutrition Advice

```python
# Agent uses Google Search for nutrition guidance
response = await run_agent_interaction(
    "What should I eat during pregnancy?",
    user_id="amina_001",
    session_id="session_001"
)
# Agent searches for country-specific nutrition information
# Returns culturally-appropriate food recommendations
```

### Example 3: Emergency Situation

```python
# Patient reports danger signs
response = await run_agent_interaction(
    "I have severe headache and vision problems. Where can I go?",
    user_id="amina_001",
    session_id="session_001"
)
# 1. Companion agent calls nurse_agent for risk assessment
# 2. Nurse agent evaluates as HIGH RISK
# 3. Nurse agent calls find_nearby_health_facilities
# 4. Returns urgent care advice with nearby hospital locations
```

### Example 4: Pre-Delivery Planning

```python
# Patient approaching due date
response = await run_agent_interaction(
    "I'm 36 weeks pregnant. How far is the hospital?",
    user_id="amina_001",
    session_id="session_001"
)
# Agent uses assess_road_accessibility
# Provides travel time and distance
# Advises on transportation planning
```

## Testing

### Manual Testing Checklist

- [ ] Country inference from various location formats
- [ ] Google Search returns relevant nutrition information
- [ ] Health facility search finds real facilities
- [ ] Road accessibility provides accurate routes
- [ ] Nurse agent uses location in risk assessments
- [ ] Location data persists across conversation turns

### Test with Demo Script

```bash
python pregnancy_companion_agent.py
```

The enhanced demo tests all location features:
1. Location capture and storage
2. Google Search for nutrition
3. EDD calculation with road accessibility
4. Emergency response with facility search

## Limitations and Considerations

1. **API Rate Limits**: Google Maps APIs have usage limits
   - Monitor usage in Google Cloud Console
   - Consider caching frequent locations

2. **API Costs**: Google Maps APIs are paid services
   - Free tier: $200/month credit
   - Monitor costs for production use

3. **Data Accuracy**: Map data varies by region
   - West Africa coverage may be limited in rural areas
   - Verify critical facilities manually

4. **Network Dependency**: All location features require internet
   - Implement appropriate error handling
   - Provide fallback guidance when APIs unavailable

5. **Privacy**: Location data is sensitive
   - Stored in session memory only (not persistent)
   - Consider GDPR/privacy regulations for production

## Future Enhancements

- [ ] Cache frequently searched locations
- [ ] Add public transportation directions
- [ ] Integrate real-time traffic data
- [ ] Add emergency services (ambulance) contact info
- [ ] Support for multiple languages in search
- [ ] Offline mode with pre-cached facility data

## Support

For issues with location features:
1. Check API key configuration in `.env`
2. Verify APIs are enabled in Google Cloud Console
3. Check logs for API error messages
4. Review API usage quotas

## Changelog

**v2.0** (Current)
- Added country and location to user profile
- Implemented country inference from location
- Integrated Google Search (ADK built-in tool)
- Added health facility search (Google Places API)
- Added road accessibility assessment (Google Directions API)
- Enhanced agent instructions for location awareness
- Updated demo script with location features

**v1.0**
- Initial ADK-compliant implementation
- EDD calculation
- Risk assessment with nurse agent
- Session and memory management
