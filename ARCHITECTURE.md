# Pregnancy Companion Agent - Architecture Documentation

**Version:** 1.0  
**Last Updated:** 2025-11-24  
**Status:** Phase 1 Complete, Phase 2 In Progress

---

## Table of Contents

1. [Overview](#overview)
2. [Current Architecture](#current-architecture)
3. [Target Architecture](#target-architecture)
4. [Migration Path](#migration-path)
5. [Technical Decisions](#technical-decisions)
6. [Scalability Considerations](#scalability-considerations)

---

## Overview

The Pregnancy Companion Agent is a comprehensive maternal health assistant built on Google's Agent Development Kit (ADK). It provides personalized pregnancy care guidance, risk assessment, and facility recommendations for expectant mothers in Africa.

### Core Capabilities

- **Conversation Management**: Multi-turn dialogues with context retention
- **Risk Assessment**: High/moderate/low risk classification
- **EDD Calculation**: Evidence-based due date estimation
- **ANC Scheduling**: WHO-compliant antenatal care schedules
- **Facility Search**: Location-based health facility recommendations
- **Nurse Consultation**: Agent-as-a-Tool for expert medical advice
- **Data Persistence**: Pregnancy records via MCP server

---

## Current Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                    (CLI / Future: WhatsApp)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RUNNER (Orchestrator)                       │
│  - Session Management                                            │
│  - Memory Service Coordination                                   │
│  - Agent Lifecycle Management                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ROOT AGENT (LlmAgent)                        │
│  Model: gemini-2.5-flash-lite                                    │
│  Instruction: 8-section comprehensive pregnancy care guidance    │
│  Temperature: 0.3 (balanced creativity/consistency)              │
└────────────────┬───────────────────────────┬────────────────────┘
                 │                           │
                 ▼                           ▼
┌────────────────────────────┐  ┌───────────────────────────────┐
│      TOOLS & SERVICES      │  │      NURSE AGENT (Sub-Agent)  │
│                            │  │  - Risk assessment            │
│ - calculate_edd            │  │  - Medical consultation       │
│ - calculate_anc_schedule   │  │  - Evidence-based guidance    │
│ - infer_country            │  │  - Tool: literature_search    │
│ - assess_road_access       │  └───────────────────────────────┘
│ - get_local_facilities     │
│ - pregnancy_mcp (McpToolset)│
│ - facility_api (OpenAPITool)│
│ - google_search            │
└────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY & PERSISTENCE                          │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │ InMemorySessionService│  │ DatabaseMemoryService (SQLite)   ││
│  │ - Session lifecycle   │  │ - Conversation history           ││
│  │ - User-session mapping│  │ - Entity extraction              ││
│  │ - Ephemeral storage   │  │ - Semantic search                ││
│  └──────────────────────┘  └──────────────────────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ MCP Server (Model Context Protocol)                          ││
│  │ - pregnancy_mcp_server.py                                    ││
│  │ - Pregnancy records (SQLite: pregnancy_records.db)           ││
│  │ - Tools: get_pregnancy_by_phone, upsert_pregnancy_record     ││
│  │ - Schema: phone, name, age, LMP, EDD, risk, location, etc.   ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │ Facilities REST API  │  │ Google Maps API (future)         ││
│  │ - FastAPI server     │  │ - Geocoding                      ││
│  │ - Mock facilities    │  │ - Distance matrix                ││
│  │ - Geographic search  │  │ - Places API                     ││
│  └──────────────────────┘  └──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Session Management (InMemorySessionService)

**Location:** `google.adk.sessions.InMemorySessionService`

**Purpose:** Manages user sessions and conversation state during runtime.

**Current Implementation:**
```python
session_service = InMemorySessionService()
```

**Characteristics:**
- ✅ **Pros:**
  - Fast in-memory access
  - Simple implementation
  - No external dependencies
  - Works well for single-process applications
  
- ❌ **Cons:**
  - Sessions lost on restart
  - No persistence across deployments
  - Not suitable for multi-instance deployment
  - No session sharing between processes

**Data Stored:**
- Session ID → User ID mapping
- Session state (active/paused/completed)
- Current conversation turn
- Temporary flags (e.g., `consultation_paused`)

**Usage Pattern:**
```python
# Create session
session = await session_service.get_or_create_session(
    session_id="session_123",
    user_id="user_456"
)

# Get existing session
session = await session_service.get_session(
    app_name=APP_NAME,
    user_id=user_id,
    session_id=session_id
)
```

#### 2. Memory Service (DatabaseMemoryService)

**Location:** `pregnancy_companion_agent.py` (lines 135-320)

**Purpose:** Stores conversation history and extracted entities with SQLite persistence.

**Current Implementation:**
```python
class DatabaseMemoryService(InMemoryMemoryService):
    """
    Custom memory service with SQLite persistence.
    Extends InMemoryMemoryService and adds database persistence.
    """
    def __init__(self, db_path: str = "pregnancy_agent_memory.db"):
        super().__init__()  # Initialize parent InMemoryMemoryService
        self.db_path = db_path
        self._init_db()
```

**Database Schema:**
```sql
-- Conversation history table
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'model'
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Entities table (key-value pairs)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    timestamp REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, entity_key)
)

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_history(session_id)
CREATE INDEX IF NOT EXISTS idx_user_id ON conversation_history(user_id)
CREATE INDEX IF NOT EXISTS idx_entities_session ON entities(session_id)
```

**Characteristics:**
- ✅ **Pros:**
  - Persistent storage (survives restarts)
  - SQLite is lightweight and embedded
  - No external database setup needed
  - Fast queries with indexes
  - Entity extraction and storage
  
- ❌ **Cons:**
  - Limited to single-file database
  - No built-in replication
  - Write contention in high-concurrency scenarios
  - Limited to single-machine deployment

**Methods Implemented:**
- `add_message()`: Store user/model messages
- `add_entities()`: Store extracted entities (LMP, age, location, etc.)
- `get_messages()`: Retrieve conversation history
- `get_entities()`: Retrieve stored entities
- `search_memories()`: Semantic search (placeholder)

#### 3. MCP Server (Model Context Protocol)

**Location:** `pregnancy_mcp_server.py`

**Purpose:** External tool for managing pregnancy records with structured data persistence.

**Current Implementation:**
```python
# MCP Server with 5 tools
app = Server("pregnancy-record-server")

@app.list_tools()
async def list_tools():
    return [
        get_pregnancy_by_phone,
        upsert_pregnancy_record,
        list_all_pregnancies,
        delete_pregnancy_record,
        search_pregnancies_by_criteria
    ]
```

**Database:** `pregnancy_records.db` (SQLite)

**Schema:**
```json
{
  "phone": "string (unique, primary key)",
  "name": "string",
  "age": "integer",
  "lmp_date": "date (YYYY-MM-DD)",
  "edd": "date (YYYY-MM-DD)",
  "location": "string",
  "country": "string",
  "risk_level": "string (low/moderate/high)",
  "anc_schedule": "JSON array of dates",
  "medical_history": "JSON object",
  "last_updated": "timestamp"
}
```

**Integration:**
```python
pregnancy_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',
            args=['pregnancy_mcp_server.py']
        )
    )
)
```

**Characteristics:**
- ✅ **Pros:**
  - Structured pregnancy data storage
  - Phone number as unique identifier
  - Tools automatically exposed to agent
  - Separate process/database from main agent
  
- ❌ **Cons:**
  - Requires MCP server process running
  - Additional process management overhead
  - Stdio communication (single-machine only)

#### 4. Agent Structure

**Root Agent (LlmAgent):**
```python
root_agent = LlmAgent(
    model=MODEL_NAME,  # gemini-2.5-flash-lite
    system_instruction=COMPREHENSIVE_INSTRUCTION,
    tools=[
        calculate_edd,
        calculate_anc_schedule,
        infer_country_from_location,
        assess_road_accessibility,
        get_local_health_facilities,
        pregnancy_mcp,  # MCP toolset
        facility_api,   # OpenAPI toolset
        google_search,
        AgentTool(agent=nurse_agent)  # Sub-agent
    ],
    generation_config={
        'temperature': 0.3,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 8192
    }
)
```

**Nurse Agent (Sub-Agent):**
```python
nurse_agent = LlmAgent(
    model=MODEL_NAME,
    system_instruction=NURSE_INSTRUCTION,
    tools=[literature_search, google_search],
    generation_config={
        'temperature': 0.2,  # More deterministic
        'top_p': 0.9,
        'top_k': 40,
        'max_output_tokens': 4096
    }
)
```

**Tool Inventory:**
1. **calculate_edd**: Naegele's rule implementation
2. **calculate_anc_schedule**: WHO 8-visit schedule
3. **infer_country_from_location**: Country detection from location string
4. **assess_road_accessibility**: Infrastructure analysis
5. **get_local_health_facilities**: Mock offline facility data
6. **pregnancy_mcp**: MCP toolset (5 pregnancy record tools)
7. **facility_api**: OpenAPI toolset (REST API for facilities)
8. **google_search**: Web search capability
9. **literature_search**: Medical literature search (nurse agent)
10. **nurse_agent**: Expert consultation via Agent-as-a-Tool

#### 5. LoopAgent for Reminders

**Location:** `anc_reminder_scheduler.py`

**Purpose:** Proactive ANC appointment reminders via scheduled checks.

**Current Implementation:**
```python
# Check Schedule Agent
check_schedule_agent = LlmAgent(
    model=MODEL_NAME,
    system_instruction=CHECK_SCHEDULE_INSTRUCTION,
    tools=[pregnancy_mcp]  # Access to pregnancy records
)

# Send Reminder Agent
send_reminder_agent = LlmAgent(
    model=MODEL_NAME,
    system_instruction=SEND_REMINDER_INSTRUCTION,
    tools=[]  # No external tools needed
)

# LoopAgent Structure
anc_reminder_loop = LoopAgent(
    name="ANCReminderLoop",
    sub_agents=[
        check_schedule_agent,
        send_reminder_agent
    ],
    max_iterations=100
)
```

**Scheduling:**
```python
scheduler = ANCReminderScheduler(
    mcp_toolset=pregnancy_mcp,
    loop_agent=anc_reminder_loop,
    session_service=session_service
)

# Daily check at 9:00 AM
scheduler.schedule_daily_check(hour=9, minute=0)
```

**Characteristics:**
- ✅ **Pros:**
  - Proactive engagement
  - Automated reminder delivery
  - Configurable schedule
  
- ⚠️ **Limitations:**
  - Requires long-running process
  - No distributed scheduling
  - Single-machine deployment only

### Memory Flow

```
User Input
    │
    ▼
Runner.generate_streaming()
    │
    ├─→ Session Service: Get/Create Session
    │   └─→ InMemory: session_id ↔ user_id
    │
    ├─→ Memory Service: Get Context
    │   ├─→ SQLite: Retrieve conversation_history
    │   └─→ SQLite: Retrieve entities
    │
    ├─→ Agent: Process Input
    │   ├─→ LLM: Generate response with tools
    │   ├─→ Tool Calls (calculate_edd, pregnancy_mcp, etc.)
    │   └─→ Sub-Agent: nurse_agent if needed
    │
    └─→ Memory Service: Store Output
        ├─→ SQLite: Insert conversation_history
        └─→ SQLite: Update/Insert entities
```

### Data Persistence Layers

1. **Session Data** (InMemorySessionService)
   - Lifetime: Process lifecycle
   - Persistence: None (volatile)
   - Use case: Active session tracking

2. **Conversation History** (DatabaseMemoryService)
   - Lifetime: Permanent
   - Persistence: SQLite (`pregnancy_agent_memory.db`)
   - Use case: Context for current and future conversations

3. **Pregnancy Records** (MCP Server)
   - Lifetime: Permanent
   - Persistence: SQLite (`pregnancy_records.db`)
   - Use case: Structured patient data

4. **Facilities Data** (REST API)
   - Lifetime: Permanent (in production)
   - Persistence: Currently mock data in memory
   - Use case: Health facility search

### Configuration

**Environment Variables:**
```bash
GOOGLE_API_KEY=<gemini-api-key>
GOOGLE_MAPS_API_KEY=<optional-maps-key>
```

**Model Configuration:**
```python
MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "pregnancy_companion_agent"
DEFAULT_USER_ID = "default_user"
```

**Safety Settings:**
```python
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}
```

### Observability

**Logging:**
- Standard Python logging module
- Level: INFO (configurable)
- Format: Timestamp + Level + Module + Message
- Output: Console (can be extended to file/cloud)

**Tracing (Optional):**
- OpenTelemetry integration
- Span tracking for agent interactions
- Attributes: user_id, session_id, input_length
- Export: Console (can be extended to Jaeger/Zipkin)

**Metrics (Future):**
- Response time
- Tool usage frequency
- Error rates
- User engagement

---

## Current Limitations

### 1. Session Persistence
- **Issue:** Sessions lost on restart
- **Impact:** Users must restart conversations
- **Severity:** Medium

### 2. Scalability
- **Issue:** Single-process architecture
- **Impact:** Limited to vertical scaling
- **Severity:** High (for production)

### 3. Context Window
- **Issue:** Conversation history grows unbounded
- **Impact:** Token limit exceeded for long conversations
- **Severity:** High

### 4. Deployment
- **Issue:** No containerization or cloud deployment
- **Impact:** Manual deployment process
- **Severity:** Medium

### 5. Monitoring
- **Issue:** Limited observability beyond logs
- **Impact:** Difficult to diagnose production issues
- **Severity:** Medium

### 6. Data Backup
- **Issue:** SQLite files have no automated backup
- **Impact:** Risk of data loss
- **Severity:** High (for production)

---

## Technical Decisions

### Why InMemorySessionService?
- **Reason:** Simple, fast, and sufficient for MVP
- **Trade-off:** No persistence vs. complexity
- **Future:** Will migrate to persistent session service

### Why SQLite for Memory?
- **Reason:** Embedded, no setup, good performance
- **Trade-off:** Limited concurrency vs. ease of use
- **Future:** Consider PostgreSQL for production

### Why MCP Server?
- **Reason:** ADK best practice for external tools
- **Trade-off:** Additional process vs. clean separation
- **Future:** May consolidate or use cloud-based MCP

### Why Gemini 2.5 Flash Lite?
- **Reason:** Fast, cost-effective, good quality
- **Trade-off:** Less capable than Pro but faster
- **Future:** May upgrade to Pro for complex cases

---

## Performance Characteristics

### Response Time (Typical)
- Simple query: 2-4 seconds
- With tool call: 4-8 seconds
- With nurse consultation: 8-15 seconds
- With multiple tools: 10-20 seconds

### Token Usage (Average per interaction)
- Input: 500-1500 tokens
- Output: 300-800 tokens
- Total: 800-2300 tokens per interaction

### Database Performance
- Memory DB write: <10ms
- Memory DB read: <5ms
- MCP server call: 50-200ms
- REST API call: 100-300ms

### Concurrency
- Current: Single process, sequential
- Maximum: ~10 concurrent users (theoretical)
- Bottleneck: LLM API rate limits

---

## Security Considerations

### Current Security Measures
1. **API Key Management:** Environment variables
2. **Input Sanitization:** SQLite parameterized queries
3. **PII Handling:** Stored in local SQLite (not encrypted)
4. **Safety Settings:** Gemini safety filters enabled

### Security Gaps (To Address)
1. **Encryption:** SQLite databases not encrypted at rest
2. **Authentication:** No user authentication system
3. **Authorization:** No role-based access control
4. **Audit Logs:** Limited audit trail
5. **HTTPS:** REST API uses HTTP (local only)

---

## Dependencies

### Core Dependencies
```
google-genai>=0.8.0
google-adk>=0.1.0
mcp>=0.1.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0
requests>=2.31.0
APScheduler>=3.10.4
```

### Optional Dependencies
```
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## File Structure

```
pregnancy_companion_agent/
├── pregnancy_companion_agent.py    # Main agent (1790 lines)
├── pregnancy_mcp_server.py         # MCP server (392 lines)
├── anc_reminder_scheduler.py       # LoopAgent scheduler (397 lines)
├── facilities_rest_server.py       # REST API mock (346 lines)
├── facilities_api.yaml             # OpenAPI spec (347 lines)
├── pregnancy_schema.json           # Data schema (46 lines)
├── pregnancy_agent_memory.db       # Conversation history (SQLite)
├── pregnancy_records.db            # Pregnancy records (SQLite)
├── tests/                          # Evaluation suite (1472 lines)
│   ├── test_teen_hemorrhage.py
│   ├── test_missing_lmp.py
│   ├── test_low_risk.py
│   ├── test_invalid_date.py
│   ├── test_config.json
│   ├── test_pregnancy_agent.py
│   ├── conftest.py
│   ├── run_all_tests.py
│   └── README.md
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (gitignored)
├── README.md                       # Project documentation
├── MVP_CHECKLIST.md                # Implementation checklist
└── ARCHITECTURE.md                 # This file
```

---

## Next Steps

See [Target Architecture](#target-architecture) section for planned improvements and [Migration Path](#migration-path) for implementation strategy.

---

## Target Architecture

### Overview

The target architecture addresses current limitations and prepares the system for production deployment with scalability, reliability, and maintainability improvements.

### Key Improvements

1. **Persistent Session Service**: Redis-backed session management
2. **Context Compaction**: Automatic conversation summarization
3. **Horizontal Scalability**: Multi-instance deployment support
4. **Cloud-Native**: Containerized with cloud storage
5. **Enhanced Monitoring**: Comprehensive observability stack
6. **Data Backup**: Automated backup and disaster recovery

### Target Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          LOAD BALANCER                                │
│                      (Future: Google Cloud LB)                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   AGENT INSTANCE 1       │  │   AGENT INSTANCE 2       │
│   (Docker Container)      │  │   (Docker Container)      │
│                           │  │                           │
│   - FastAPI Server        │  │   - FastAPI Server        │
│   - Runner                │  │   - Runner                │
│   - Root Agent            │  │   - Root Agent            │
│   - Nurse Agent           │  │   - Nurse Agent           │
└───────────┬───────────────┘  └───────────┬───────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Redis           │  │ PostgreSQL   │  │ Cloud Storage    │
│ (Sessions)      │  │ (Memory)     │  │ (Backups)        │
│                 │  │              │  │                  │
│ - Session state │  │ - Conv hist  │  │ - DB backups     │
│ - User context  │  │ - Entities   │  │ - Audit logs     │
│ - Rate limits   │  │ - Summaries  │  │ - Analytics      │
└─────────────────┘  └──────────────┘  └──────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ MCP Server      │  │ Facilities   │  │ Monitoring       │
│ (Separate Pod)  │  │ REST API     │  │ Stack            │
│                 │  │              │  │                  │
│ - Pregnancy DB  │  │ - Real data  │  │ - Prometheus     │
│ - gRPC API      │  │ - Caching    │  │ - Grafana        │
└─────────────────┘  └──────────────┘  │ - OpenTelemetry  │
                                       │ - Error tracking │
                                       └──────────────────┘
```

### Target Components

#### 1. Persistent Session Service (Redis)

**Replacement for:** InMemorySessionService

**Technology:** Redis (or Google Cloud Memorystore)

**Implementation:**
```python
from google.adk.sessions import RedisSessionService

session_service = RedisSessionService(
    redis_url="redis://redis-service:6379",
    ttl=86400  # 24 hours
)
```

**Benefits:**
- ✅ Sessions persist across restarts
- ✅ Shared across multiple instances
- ✅ Fast in-memory performance
- ✅ Built-in TTL for automatic cleanup
- ✅ Horizontal scalability

**Data Structure:**
```
Session Key: "session:{app_name}:{user_id}:{session_id}"
Value: {
    "user_id": "string",
    "session_id": "string",
    "state": "active|paused|completed",
    "created_at": timestamp,
    "last_activity": timestamp,
    "metadata": {...}
}
TTL: 24 hours (configurable)
```

#### 2. PostgreSQL Memory Service

**Replacement for:** DatabaseMemoryService (SQLite)

**Technology:** PostgreSQL (or Google Cloud SQL)

**Implementation:**
```python
from google.adk.memory import PostgreSQLMemoryService

memory_service = PostgreSQLMemoryService(
    connection_string="postgresql://user:pass@postgres:5432/pregnancy_db"
)
```

**Schema:**
```sql
-- Conversation history with partitioning
CREATE TABLE conversation_history (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    summary TEXT,  -- NEW: Compacted summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Partition by month for better performance
CREATE TABLE conversation_history_2025_11 PARTITION OF conversation_history
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Entities table
CREATE TABLE entities (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    entity_key VARCHAR(255) NOT NULL,
    entity_value JSONB NOT NULL,  -- JSONB for flexible storage
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_session_entity UNIQUE (session_id, entity_key)
);

-- Summaries table (NEW for context compaction)
CREATE TABLE conversation_summaries (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    start_turn INT NOT NULL,
    end_turn INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_conv_session ON conversation_history(session_id);
CREATE INDEX idx_conv_user ON conversation_history(user_id);
CREATE INDEX idx_conv_timestamp ON conversation_history(timestamp);
CREATE INDEX idx_entities_session ON entities(session_id);
CREATE INDEX idx_summaries_session ON conversation_summaries(session_id);
```

**Benefits:**
- ✅ Production-grade reliability
- ✅ ACID transactions
- ✅ Better concurrency handling
- ✅ Built-in replication
- ✅ Advanced query capabilities
- ✅ Cloud-managed options available

#### 3. Context Compaction System

**Purpose:** Prevent token overflow in long conversations

**Implementation Strategy:**

```python
class ContextCompactionService:
    """
    Automatically summarizes old conversation turns to maintain
    context while staying within token limits.
    """
    
    def __init__(
        self,
        memory_service: MemoryService,
        summarization_threshold: int = 20,  # Summarize after 20 turns
        max_tokens: int = 6000  # Reserve tokens for prompt + response
    ):
        self.memory_service = memory_service
        self.threshold = summarization_threshold
        self.max_tokens = max_tokens
    
    async def compact_if_needed(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Check if compaction is needed and perform it.
        Returns True if compaction was performed.
        """
        # Get conversation length
        messages = await self.memory_service.get_messages(
            session_id=session_id,
            user_id=user_id
        )
        
        turn_count = len(messages) // 2  # User + model = 1 turn
        
        if turn_count >= self.threshold:
            # Summarize old turns (keep last 10 turns)
            await self._summarize_old_turns(
                session_id=session_id,
                user_id=user_id,
                keep_last_n=10
            )
            return True
        
        return False
    
    async def _summarize_old_turns(
        self,
        session_id: str,
        user_id: str,
        keep_last_n: int
    ):
        """
        Summarize old conversation turns into a compact summary.
        """
        messages = await self.memory_service.get_messages(
            session_id=session_id,
            user_id=user_id
        )
        
        # Split into old (to summarize) and recent (to keep)
        split_point = len(messages) - (keep_last_n * 2)
        old_messages = messages[:split_point]
        
        if not old_messages:
            return
        
        # Generate summary using LLM
        summary_prompt = f"""
        Summarize the following conversation, extracting key information:
        - Patient details (name, age, phone, location)
        - Pregnancy details (LMP, EDD, gestational age)
        - Risk factors and medical history
        - Previous advice given
        - Follow-up items
        
        Conversation:
        {self._format_messages(old_messages)}
        
        Provide a concise summary in 200-300 words.
        """
        
        # Call summarization model (could be same or different)
        summary = await self._call_summarization_model(summary_prompt)
        
        # Store summary in database
        await self.memory_service.store_summary(
            session_id=session_id,
            user_id=user_id,
            summary=summary,
            start_turn=0,
            end_turn=split_point // 2
        )
        
        # Delete old messages from memory (keep in DB for audit)
        await self.memory_service.archive_messages(
            session_id=session_id,
            message_ids=[msg.id for msg in old_messages]
        )
```

**Usage in Runner:**
```python
# Before generating response
await context_compaction_service.compact_if_needed(
    session_id=session.id,
    user_id=session.user_id
)

# Retrieve context with summary
context = await memory_service.get_context_with_summary(
    session_id=session.id,
    user_id=session.user_id
)
# Returns: {
#   "summary": "Previous conversation summary...",
#   "recent_messages": [last 10 turns],
#   "entities": {...}
# }
```

**Benefits:**
- ✅ Prevents token overflow
- ✅ Maintains long-term context
- ✅ Reduces API costs
- ✅ Improves response time

#### 4. FastAPI Server Wrapper

**Purpose:** RESTful API for external integrations (WhatsApp, web, mobile)

**Implementation:**
```python
# api_server.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Pregnancy Companion API")

class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat interaction with the agent.
    """
    try:
        # Run agent interaction
        result = await run_agent_interaction(
            user_input=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return ChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            timestamp=datetime.datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/callback/loop")
async def loop_callback(background_tasks: BackgroundTasks):
    """
    Callback endpoint for LoopAgent reminders.
    Triggered by scheduler to send proactive reminders.
    """
    background_tasks.add_task(run_reminder_loop)
    return {"status": "scheduled"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Benefits:**
- ✅ RESTful API for integrations
- ✅ Async request handling
- ✅ OpenAPI documentation
- ✅ Easy deployment

#### 5. Containerization (Docker)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY pregnancy_companion_agent.py .
COPY pregnancy_mcp_server.py .
COPY anc_reminder_scheduler.py .
COPY facilities_api.yaml .
COPY pregnancy_schema.json .
COPY api_server.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_API_KEY=""

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://postgres:password@postgres:5432/pregnancy_db
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
  
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=pregnancy_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
  
  mcp_server:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/pregnancy_records
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

**Benefits:**
- ✅ Reproducible deployments
- ✅ Environment isolation
- ✅ Easy scaling (docker-compose scale)
- ✅ Platform independence

#### 6. Observability Stack

**Components:**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **OpenTelemetry**: Distributed tracing
- **Loki**: Log aggregation
- **Sentry**: Error tracking

**Metrics to Track:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'agent_requests_total',
    'Total agent requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'agent_request_duration_seconds',
    'Agent request duration',
    ['endpoint']
)

# Agent metrics
tool_calls = Counter(
    'agent_tool_calls_total',
    'Total tool calls',
    ['tool_name', 'success']
)

token_usage = Counter(
    'agent_tokens_total',
    'Total tokens used',
    ['type']  # 'input' or 'output'
)

# Business metrics
active_sessions = Gauge(
    'agent_active_sessions',
    'Number of active sessions'
)

high_risk_cases = Counter(
    'pregnancy_high_risk_cases_total',
    'Total high-risk cases identified'
)
```

**Dashboard Panels:**
1. Request rate and latency
2. Error rate and types
3. Tool usage distribution
4. Token consumption
5. Active users/sessions
6. High-risk case alerts
7. Database query performance
8. Cache hit rates

#### 7. Cloud Deployment (Google Cloud)

**Services Used:**
- **Cloud Run**: Containerized agent instances
- **Cloud SQL**: PostgreSQL database
- **Memorystore**: Redis for sessions
- **Cloud Storage**: Backups and static files
- **Cloud Logging**: Centralized logs
- **Cloud Monitoring**: Metrics and alerts
- **Secret Manager**: API keys and credentials

**Architecture:**
```
Internet
    │
    ▼
Cloud Load Balancer
    │
    ├─→ Cloud Run (Agent Instance 1)
    ├─→ Cloud Run (Agent Instance 2)
    └─→ Cloud Run (Agent Instance N)
         │
         ├─→ Memorystore (Redis)
         ├─→ Cloud SQL (PostgreSQL)
         ├─→ Cloud Storage (Backups)
         └─→ Secret Manager (Credentials)
```

**Benefits:**
- ✅ Auto-scaling
- ✅ Pay-per-use
- ✅ High availability
- ✅ Managed services
- ✅ Built-in monitoring

### Migration Timeline

**Phase 2a: Foundation (Week 2)**
- Document current architecture ✅ (this file)
- Document target architecture ✅ (this section)
- Create migration plan (MIGRATION.md)

**Phase 2b: Deployment (Week 2)**
- Create FastAPI server wrapper
- Implement /chat endpoint
- Implement /callback/loop endpoint
- Create Dockerfile

**Phase 2c: Context Compaction (Week 2)**
- Implement conversation summarization
- Store summaries in database
- Clear old dialogue history
- Test with long conversations

**Phase 3: Production Readiness (Week 3)**
- Set up PostgreSQL migration
- Implement Redis session service
- Deploy to Cloud Run
- Set up monitoring stack
- Implement backup strategy
- Load testing and optimization

---

**Document Version:** 1.0  
**Last Review:** 2025-11-24  
**Next Review:** 2025-12-01
