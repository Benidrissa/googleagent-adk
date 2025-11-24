# Web Client Debugging Guide

## Issue: Network Error in Browser

### Problem
The web client was showing "Network Error" when trying to communicate with the API.

### Root Cause
The React app was configured to use `http://localhost:8000` as the API URL, which caused CORS and network routing issues when accessed through the browser at `http://localhost`.

### Solution
Changed the API URL from `http://localhost:8000` to `/api` to use the nginx reverse proxy configured in the web-client container.

## Architecture

```
Browser (http://localhost)
    ↓
Traefik (port 80)
    ↓
web-client container (nginx)
    ├── / → serves React static files
    └── /api/* → proxies to agent:8000/*
```

## Testing the Fix

### 1. Test Health Endpoint
```bash
# Through browser/web-client
curl http://localhost/api/health

# Expected output:
{
    "status": "healthy",
    "timestamp": "2025-11-24T22:27:07",
    "version": "1.0.0"
}
```

### 2. Test Chat Endpoint
```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello"
  }'

# Expected output:
{
    "session_id": "session_test_user_...",
    "response": "Hello! I am your pregnancy companion...",
    "timestamp": "2025-11-24T22:27:07"
}
```

### 3. Access Web Client
Open browser to: http://localhost

The web client should now:
- ✅ Load without errors
- ✅ "Check Health" button works
- ✅ Send messages successfully
- ✅ Display agent responses

## Common Issues

### Issue: 404 Not Found on /api/*
**Cause:** Nginx proxy configuration not correct
**Fix:** Check `web-client/nginx.conf`:
```nginx
location /api/ {
    proxy_pass http://agent:8000/;
    ...
}
```

### Issue: CORS Error
**Cause:** API server not allowing requests from origin
**Fix:** Check CORS middleware in `api_server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Connection Refused
**Cause:** Agent container not running
**Fix:**
```bash
docker-compose ps
docker-compose logs agent
docker-compose restart agent
```

### Issue: Changes Not Reflected
**Cause:** Browser cache or old Docker image
**Fix:**
```bash
# Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

# Rebuild web-client
docker-compose up -d --build web-client
```

## Debugging Commands

```bash
# Check if web-client can reach agent
docker-compose exec web-client wget -O- -q http://agent:8000/health

# Check nginx logs
docker-compose logs web-client

# Check agent logs
docker-compose logs agent

# Test from within web-client container
docker-compose exec web-client sh
wget -O- http://agent:8000/health

# Check Traefik routing
curl http://localhost:8080/api/http/routers
```

## Environment Variables

The web client uses build-time environment variables:

```dockerfile
# In docker-compose.yml
environment:
  - VITE_API_URL=http://localhost:8000  # NOT USED (build-time only)
```

**Important:** Vite environment variables are replaced at **build time**, not runtime. Therefore, we hardcode the API URL to `/api` in the source code to use the nginx proxy.

## Verification Checklist

- [x] Web client container running
- [x] Agent container running and healthy
- [x] Traefik routing configured
- [x] Nginx proxy forwarding /api/* to agent:8000
- [x] Browser can access http://localhost
- [x] Health check button works
- [x] Chat messages send successfully
- [x] No CORS errors in browser console
- [x] No network errors in browser console

## Related Files

- `web-client/src/App.tsx` - React app with API URL configuration
- `web-client/nginx.conf` - Nginx reverse proxy configuration
- `web-client/Dockerfile` - Multi-stage build configuration
- `docker-compose.yml` - Service orchestration and networking
- `api_server.py` - FastAPI server with CORS middleware

---

**Fixed:** 2025-11-24
**Status:** ✅ Working
