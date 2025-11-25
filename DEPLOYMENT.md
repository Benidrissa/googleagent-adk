# Deployment Guide - Pregnancy Companion Agent

## Quick Deployment Options

### Option 1: Docker Compose (Recommended for Development & Testing)

The fastest way to deploy the complete stack locally or on a server.

#### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- Ports available: 80, 8000, 8080, 5432, 6379

#### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd googleagent-adk

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

#### Services Included

| Service | Description | Port | URL |
|---------|-------------|------|-----|
| **web-client** | React UI | 80 | http://localhost |
| **agent** | FastAPI server | 8000 | http://localhost:8000 |
| **traefik** | Reverse proxy | 80, 8080 | http://localhost:8080 |
| **postgres** | Database | 5432 | Internal |
| **redis** | Cache | 6379 | Internal |
| **mcp_server** | MCP tools | - | Internal |

#### Configuration

**Environment Variables (.env)**
```bash
# Required
GOOGLE_API_KEY=AIzaSy...
GOOGLE_MAPS_API_KEY=AIzaSy...

# Optional
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=INFO
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/pregnancy_db
REDIS_URL=redis://redis:6379/0
```

**Docker Compose Override (docker-compose.override.yml)**
```yaml
version: '3.8'
services:
  agent:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8001:8000"  # Expose additional port
```

#### Management Commands

```bash
# View logs
docker-compose logs -f agent
docker-compose logs -f web-client

# Restart services
docker-compose restart agent

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Update images
docker-compose pull
docker-compose up -d --build

# Scale services
docker-compose up -d --scale agent=3
```

#### Health Checks

```bash
# Check all services
docker-compose ps

# Test API endpoint
curl http://localhost:8000/health

# Test web client
curl http://localhost

# Check Traefik dashboard
open http://localhost:8080
```

#### Troubleshooting

**Issue**: Port already in use
```bash
# Find what's using the port
sudo lsof -i :80
sudo lsof -i :6379

# Stop conflicting service
docker stop <container-name>
```

**Issue**: Services not starting
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose up -d --build --force-recreate
```

**Issue**: Out of memory
```bash
# Check Docker resources
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 4GB+
```

**Issue**: Database connection failed
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d agent
```

#### Production Deployment with Docker

For production deployment on a VPS/server:

```bash
# 1. Install Docker on server (Ubuntu example)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone and deploy
git clone <repository-url>
cd googleagent-adk
cp .env.example .env
nano .env  # Add your API keys

# 4. Start services
docker-compose up -d

# 5. Enable auto-restart
docker update --restart=always $(docker-compose ps -q)

# 6. Set up firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### SSL/HTTPS Setup with Let's Encrypt

Add to `docker-compose.yml`:

```yaml
services:
  traefik:
    command:
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    volumes:
      - ./letsencrypt:/letsencrypt
    labels:
      - "traefik.http.routers.web-secure.tls.certresolver=letsencrypt"
```

#### Monitoring & Logs

```bash
# View real-time logs
docker-compose logs -f --tail=100

# Export logs
docker-compose logs > deployment-logs-$(date +%Y%m%d).txt

# Monitor resource usage
docker stats

# Check service health
watch -n 5 'docker-compose ps'
```

#### Backup & Restore

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres pregnancy_db > backup-$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U postgres pregnancy_db < backup-20251125.sql

# Backup all data volumes
docker run --rm -v googleagent-adk_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/data-backup-$(date +%Y%m%d).tar.gz /data
```

---

### Option 2: Google Cloud Run (Cloud Deployment)

Cloud Run provides serverless deployment with automatic scaling.

#### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Project with billing enabled

#### Steps

1. **Create Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY pregnancy_companion_agent.py .
COPY .env .env

# Expose port
EXPOSE 8080

# Run the agent server
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. **Create FastAPI wrapper** (app.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pregnancy_companion_agent import run_agent_interaction_sync
import uuid

app = FastAPI(title="Pregnancy Companion Agent API")

class ChatRequest(BaseModel):
    message: str
    user_id: str = None
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        user_id = request.user_id or str(uuid.uuid4())
        session_id = request.session_id
        
        response = run_agent_interaction_sync(
            request.message,
            user_id=user_id,
            session_id=session_id
        )
        
        return ChatResponse(
            response=response,
            session_id=session_id or f"session_{user_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

3. **Deploy to Cloud Run**

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy pregnancy-companion \\
  --source . \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --set-env-vars GOOGLE_API_KEY=your_key,GOOGLE_MAPS_API_KEY=your_key \\
  --memory 1Gi \\
  --timeout 300

# Get URL
gcloud run services describe pregnancy-companion --region us-central1 --format='value(status.url)'
```

4. **Test deployment**

```bash
curl -X POST https://your-service-url/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hi, I need pregnancy advice", "user_id": "test_user"}'
```

**Cost**: Free tier includes 2 million requests/month, then $0.40 per million requests

---

### Option 2: Vertex AI Agent Engine (Enterprise)

Agent Engine provides managed infrastructure specifically for AI agents.

#### Steps

1. **Enable APIs**

```bash
gcloud services enable aiplatform.googleapis.com
```

2. **Create deployment script** (deploy_to_agent_engine.py)

```python
from google.cloud import aiplatform
from pregnancy_companion_agent import root_agent, APP_NAME

# Initialize Vertex AI
aiplatform.init(
    project="YOUR_PROJECT_ID",
    location="us-central1"
)

# Deploy agent
deployed_agent = aiplatform.Agent.create(
    display_name="pregnancy-companion-production",
    description="AI-powered maternal health support for West Africa",
    agent_source=root_agent,
    app_name=APP_NAME
)

print(f"Agent deployed: {deployed_agent.resource_name}")
print(f"Endpoint: {deployed_agent.endpoint}")
```

3. **Deploy**

```bash
python deploy_to_agent_engine.py
```

**Cost**: Pay-per-token pricing, varies by usage

---

### Option 3: Local Server with ngrok (Development/Demo)

For quick demos and testing.

#### Steps

1. **Install ngrok**

```bash
# macOS
brew install ngrok

# Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
```

2. **Run local server**

```bash
# In terminal 1: Start server
uvicorn app:app --host 0.0.0.0 --port 8000

# In terminal 2: Expose with ngrok
ngrok http 8000
```

3. **Share URL**

ngrok provides a public URL like: `https://abc123.ngrok.io`

**Cost**: Free for testing, $8/month for custom domains

---

### Option 4: Heroku (Simple Deployment)

Quick deployment for small-scale use.

#### Steps

1. **Create Procfile**

```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

2. **Create runtime.txt**

```
python-3.10.0
```

3. **Deploy**

```bash
heroku login
heroku create pregnancy-companion-agent
heroku config:set GOOGLE_API_KEY=your_key
heroku config:set GOOGLE_MAPS_API_KEY=your_key
git push heroku main
```

**Cost**: Free tier available, $7/month for hobby tier

---

## Environment Configuration

### Required Environment Variables

```bash
# .env file for deployment
GOOGLE_API_KEY=AIzaSy...
GOOGLE_MAPS_API_KEY=AIzaSy...
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=INFO
```

### Cloud Run Secret Manager (Recommended)

```bash
# Store secrets in Secret Manager
echo -n "your_api_key" | gcloud secrets create google-api-key --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding google-api-key \\
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \\
  --role=roles/secretmanager.secretAccessor

# Deploy with secrets
gcloud run deploy pregnancy-companion \\
  --source . \\
  --set-secrets GOOGLE_API_KEY=google-api-key:latest
```

---

## Monitoring & Observability

### Enable Cloud Logging

```python
# Already included in code with OpenTelemetry support
# Logs automatically sent to Cloud Logging when deployed to GCP
```

### View logs

```bash
# Cloud Run logs
gcloud run logs tail pregnancy-companion --region us-central1

# Or in Cloud Console
https://console.cloud.google.com/run
```

### Set up alerts

```bash
# Create alert for errors
gcloud alpha monitoring policies create \\
  --notification-channels=CHANNEL_ID \\
  --display-name="Agent Errors" \\
  --condition-display-name="High error rate" \\
  --condition-threshold-value=10 \\
  --condition-threshold-duration=60s
```

---

## Scaling Configuration

### Auto-scaling (Cloud Run)

```bash
gcloud run deploy pregnancy-companion \\
  --min-instances 0 \\
  --max-instances 100 \\
  --concurrency 80 \\
  --cpu 2 \\
  --memory 2Gi
```

### Load testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between
import json

class AgentUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def chat(self):
        self.client.post("/chat", json={
            "message": "What should I eat during pregnancy?",
            "user_id": "load_test"
        })

EOF

# Run load test
locust -f locustfile.py --host https://your-service-url
```

---

## Security Best Practices

### 1. API Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(request: ChatRequest, token: str = Security(security)):
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of code
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    # ... code
```

### 3. Input Validation

```python
from pydantic import Field, validator

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v
```

---

## Cost Optimization

### 1. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_facility_data(location: str):
    return get_local_health_facilities(location)
```

### 2. Request batching

```python
# Process multiple requests in batch
@app.post("/batch_chat")
async def batch_chat(requests: List[ChatRequest]):
    responses = await asyncio.gather(*[
        process_chat(req) for req in requests
    ])
    return responses
```

### 3. Model selection

```python
# Use Flash for routine queries, Pro for complex cases
def select_model(complexity: str):
    return "gemini-2.0-flash-exp" if complexity == "low" else "gemini-2.0-pro"
```

---

## Deployment Checklist

Before going to production:

- [ ] Environment variables configured
- [ ] Secrets stored securely (Secret Manager)
- [ ] API keys restricted (IP/domain whitelisting)
- [ ] Logging enabled
- [ ] Monitoring alerts configured
- [ ] Rate limiting implemented
- [ ] Input validation added
- [ ] Load testing completed
- [ ] Backup strategy in place
- [ ] Documentation updated
- [ ] Health check endpoint working
- [ ] Error handling tested
- [ ] CORS configured (if web frontend)
- [ ] HTTPS enforced
- [ ] Cost alerts set up

---

## Troubleshooting

### Common Issues

**Issue**: "API key not valid"
```bash
# Verify secrets
gcloud secrets versions access latest --secret=google-api-key
```

**Issue**: "Out of memory"
```bash
# Increase memory
gcloud run deploy pregnancy-companion --memory 2Gi
```

**Issue**: "Cold start timeout"
```bash
# Set minimum instances
gcloud run deploy pregnancy-companion --min-instances 1
```

**Issue**: "Request timeout"
```bash
# Increase timeout
gcloud run deploy pregnancy-companion --timeout 300
```

---

## Demo Deployment (30-Day Trial)

For capstone submission, deploy a temporary demo:

```bash
# Quick Cloud Run deployment
gcloud run deploy pregnancy-companion-demo \\
  --source . \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY \\
  --timeout 60

# Get URL for submission
gcloud run services describe pregnancy-companion-demo \\
  --region us-central1 \\
  --format='value(status.url)'
```

Add this URL to your Kaggle writeup with:
- Demo endpoint documentation
- Example requests
- Note: "Demo deployment active through Dec 31, 2025"

---

## Production Recommendations

For real-world deployment:

1. **Use Vertex AI Agent Engine** for enterprise scale
2. **Implement authentication** (OAuth2, API keys)
3. **Add regional deployment** (multi-region for West Africa)
4. **Set up CDN** for static assets
5. **Enable auto-scaling** with appropriate limits
6. **Monitor costs** with budget alerts
7. **Regular backups** of session data
8. **HIPAA compliance** if handling real patient data

---

**Deployment complete? Add to your capstone submission for +5 bonus points! 🚀**
