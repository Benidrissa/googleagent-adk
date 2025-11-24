# Quick Setup Guide - Location Features

## Prerequisites

1. **Python 3.9+**
2. **Google Cloud Account** (free tier available)
3. **API Keys**:
   - Google AI Studio API key (for Gemini)
   - Google Maps API key (for location services)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

New dependency added: `requests>=2.31.0` for Maps API calls.

## Step 2: Get Google AI Studio API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

## Step 3: Get Google Maps API Key

### Enable Required APIs

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Navigate to "APIs & Services" > "Library"
4. Enable these APIs:
   - ✅ **Geocoding API** (for country inference)
   - ✅ **Places API** (for health facility search)
   - ✅ **Directions API** (for route planning)

### Create API Key

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the key
4. (Optional) Click "Restrict Key" to limit to Maps APIs only

### API Key Restrictions (Recommended)

For security, restrict your Maps API key:

**Application Restrictions**: None (or IP addresses if known)

**API Restrictions**: 
- Geocoding API
- Places API
- Directions API

## Step 4: Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Google AI Studio API Key (for Gemini and Google Search)
GOOGLE_API_KEY=AIzaSy...your_key_here

# Google Maps API Key (for location services)
# Can be the same as GOOGLE_API_KEY if Maps APIs are enabled
GOOGLE_MAPS_API_KEY=AIzaSy...your_maps_key_here
```

**Note**: You can use the same key for both if you've enabled all APIs on one key.

## Step 5: Test the Installation

### Test 1: Basic Tool Test

```python
from pregnancy_companion_agent import infer_country_from_location

result = infer_country_from_location("Bamako")
print(result)
# Expected: {"status": "success", "country": "Mali", ...}
```

### Test 2: Run Location Features Test Suite

```bash
python test_location_features.py
```

This will test:
- ✅ Country inference
- ✅ Health facility search
- ✅ Road accessibility
- ✅ Agent integration

### Test 3: Run Enhanced Demo

```bash
python pregnancy_companion_agent.py
```

This demonstrates all features in action.

## Step 6: Verify Features

### 6.1 Country Inference

```python
from pregnancy_companion_agent import infer_country_from_location

# Test with just city name
result = infer_country_from_location("Lagos")
print(f"Country: {result['country']}")  # Should show "Nigeria"
```

### 6.2 Health Facility Search

```python
from pregnancy_companion_agent import find_nearby_health_facilities

# Find hospitals within 5km of Accra
result = find_nearby_health_facilities("Accra, Ghana", radius_meters=5000)
print(f"Found {result['count']} facilities")
for facility in result['facilities'][:3]:
    print(f"- {facility['name']}: {facility['address']}")
```

### 6.3 Road Accessibility

```python
from pregnancy_companion_agent import assess_road_accessibility

# Check route to nearest hospital
result = assess_road_accessibility("Bamako city center")
print(f"Distance: {result['distance']}, Duration: {result['duration']}")
```

### 6.4 Full Agent Test

```python
import asyncio
from pregnancy_companion_agent import run_agent_interaction

async def test():
    # Patient provides location
    response = await run_agent_interaction(
        "I'm Amina from Bamako, Mali. What foods should I eat?"
    )
    print(response)

asyncio.run(test())
```

## Troubleshooting

### Issue: "API key not valid" error

**Solution**:
1. Verify API key is correctly copied to `.env`
2. For Maps features, ensure APIs are enabled in Cloud Console
3. Wait 1-2 minutes after enabling APIs (propagation time)

### Issue: "This API project is not authorized to use this API"

**Solution**:
1. Go to Google Cloud Console
2. Navigate to "APIs & Services" > "Library"
3. Search for and enable: Geocoding API, Places API, Directions API

### Issue: "Quota exceeded" error

**Solution**:
1. Check usage in Cloud Console > "APIs & Services" > "Dashboard"
2. Free tier includes $200/month credit
3. Monitor usage or set up billing alerts

### Issue: "ZERO_RESULTS" from Places API

**Possible causes**:
1. Location is too rural (limited map data)
2. Search radius is too small (increase radius_meters)
3. Location string is ambiguous (be more specific)

**Solution**: Try with larger radius or more specific location.

### Issue: Google Search not working

**Check**:
1. Ensure you're using `google-adk>=1.19.0`
2. Verify `google_search` is imported from `google.adk.tools`
3. Check if `bypass_multi_tools_limit=True` is set in config

## API Costs (Free Tier)

Google Cloud free tier (as of 2024):

**Geocoding API**: $5 per 1,000 requests
- Free: $200 credit = 40,000 requests/month

**Places API**: $17 per 1,000 requests
- Free: $200 credit = ~11,500 requests/month

**Directions API**: $5 per 1,000 requests
- Free: $200 credit = 40,000 requests/month

**Google Search (ADK)**: Included with Gemini API usage

**Monitoring**: Set up billing alerts in Cloud Console to avoid charges.

## Production Checklist

Before deploying to production:

- [ ] Restrict API keys to specific APIs
- [ ] Set up billing alerts in Cloud Console
- [ ] Implement caching for frequently searched locations
- [ ] Add rate limiting for API calls
- [ ] Monitor API usage in Cloud Console
- [ ] Test with real user locations in target regions
- [ ] Verify health facility data accuracy
- [ ] Review privacy compliance (GDPR, etc.)
- [ ] Set up error monitoring and logging
- [ ] Create fallback responses when APIs unavailable

## Next Steps

1. **Customize Location Logic**: Modify `find_nearby_health_facilities` radius or filters
2. **Add Caching**: Cache geocoding results to reduce API calls
3. **Enhance Instructions**: Tune agent instructions for your specific use case
4. **Add Languages**: Integrate translation for multi-language support
5. **Extend Features**: Add pharmacies, labs, or other facility types

## Support Resources

- **Google Maps Platform**: https://developers.google.com/maps
- **Google ADK Documentation**: https://google.github.io/adk-docs/
- **API Console**: https://console.cloud.google.com/
- **Pricing Calculator**: https://cloud.google.com/products/calculator

## Need Help?

Check these resources:
1. `LOCATION_FEATURES.md` - Detailed feature documentation
2. `test_location_features.py` - Example usage and tests
3. Google Maps Platform documentation
4. Google Cloud Console error logs

Happy coding! 🚀
