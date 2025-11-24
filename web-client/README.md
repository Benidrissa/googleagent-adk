# Pregnancy Companion Agent - Web Client

A React TypeScript web client for testing the Pregnancy Companion Agent API.

## Features

- 💬 Chat interface for testing conversations
- 📊 Real-time session management
- 🔄 Automatic message history
- 🏥 Health check endpoint testing
- 🎨 Modern, responsive UI
- 🐳 Docker containerized

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Docker Deployment

### Build and run with Docker Compose

```bash
# From project root
docker-compose up web-client
```

The web client will be available at `http://localhost:3000`

### Build standalone

```bash
cd web-client
docker build -t pregnancy-web-client .
docker run -p 3000:3000 pregnancy-web-client
```

## Architecture

- **Frontend**: React 18 + TypeScript + Vite
- **HTTP Client**: Axios
- **Server**: Nginx (production)
- **Styling**: CSS3 with animations

## API Integration

The client communicates with the Pregnancy Companion Agent API:

- `GET /health` - Check API health status
- `POST /chat` - Send messages and receive responses

### Request Format

```json
{
  "user_id": "test_user_123",
  "session_id": "optional_session_id",
  "message": "Hi, I just found out I'm pregnant"
}
```

### Response Format

```json
{
  "session_id": "session_abc123",
  "response": "Congratulations! Let me help you...",
  "timestamp": "2025-11-24T12:00:00Z"
}
```

## Features

### Chat Interface
- Send and receive messages
- View conversation history
- Auto-scroll to latest messages
- Typing indicators

### Session Management
- Automatic session creation
- Session ID display
- User ID tracking
- Clear chat functionality

### Health Monitoring
- API health check
- Connection status
- Error handling and display

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure the API server has proper CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Refused

Check that:
1. API server is running on port 8000
2. Network connectivity between containers
3. Environment variables are set correctly

## License

Part of the Pregnancy Companion Agent project for Google ADK Competition.
