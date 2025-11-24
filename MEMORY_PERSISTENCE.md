# Memory Persistence in Google ADK

## Understanding ADK Memory Services

### 📝 Key Concepts

**Session (Short-term)**
- Tracks history and state for ONE conversation
- Lives only during that specific chat
- Managed by `SessionService`

**Memory (Long-term)**
- Searchable archive across MULTIPLE conversations
- Can recall information from past sessions
- Managed by `MemoryService`

---

## Memory Service Options

### 1. ⚠️ InMemoryMemoryService (Current - NOT Persistent)

```python
from google.adk.memory import InMemoryMemoryService
memory_service = InMemoryMemoryService()
```

**Characteristics:**
- ❌ **NOT persistent** - lost when process stops
- ✅ Best for prototyping and testing
- ✅ No setup required
- ⚠️ Basic keyword matching only

**When to use:**
- Local development
- Quick prototypes
- Testing features

---

### 2. ✅ VertexAiMemoryBankService (Recommended for Production)

```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="YOUR_GCP_PROJECT_ID",
    location="us-central1",
    agent_engine_id="YOUR_AGENT_ENGINE_ID"
)
```

**Characteristics:**
- ✅ **Fully persistent** - managed by Google Cloud
- ✅ Advanced semantic search
- ✅ LLM-powered memory extraction
- ✅ Production-ready
- ⚠️ Requires Google Cloud setup

**Prerequisites:**
1. Google Cloud Project with Vertex AI API enabled
2. Create an Agent Engine in Vertex AI
3. Set environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export GOOGLE_CLOUD_LOCATION="us-central1"
   ```
4. Authenticate:
   ```bash
   gcloud auth application-default login
   ```

---

## Current Implementation

Our pregnancy companion agent currently uses `InMemoryMemoryService`:

**What this means:**
- ✅ Memory works WITHIN a single session (same session_id)
- ✅ Agent remembers conversation history during the chat
- ❌ Memory is LOST when you:
  - Exit the program
  - Restart interactive_demo.py
  - Change session_id

**To maintain memory across restarts:**
Use the same `session_id` each time:
```python
session_id = "persistent_interactive_session"  # Fixed, not timestamped
```

---

## How Memory Works in Practice

### Workflow:

1. **User interacts** with agent via a Session
2. **Ingestion**: Call `memory_service.add_session_to_memory(session)`
3. **Later query**: User asks something requiring past context
4. **Agent uses memory tool**: Calls `load_memory` or `preload_memory` tool
5. **Search execution**: `memory_service.search_memory(query)`
6. **Results returned**: Agent gets relevant past information
7. **Agent uses results**: Formulates answer with retrieved context

### Tools for Memory Retrieval:

```python
from google.adk.tools import load_memory  # Retrieve when needed
from google.adk.tools import preload_memory  # Always retrieve at turn start
```

---

## Testing Memory

### Within Same Session (Works Now):

```bash
python interactive_demo.py
```

```
You: Hi, I'm Amina from Lagos. My LMP was January 1, 2025.
Agent: [Calculates EDD, stores in session]

You: What is my due date?
Agent: [Remembers from session state] ✅

You: What should I eat?
Agent: [Remembers location=Lagos] ✅
```

### Across Restarts (Requires Vertex AI):

Currently **NOT working** because `InMemoryMemoryService` is non-persistent.

To make it work:
1. Set up Vertex AI Memory Bank (see prerequisites above)
2. Replace memory service in pregnancy_companion_agent.py
3. Restart will maintain memory ✅

---

## SQLite Alternative (Custom Implementation)

The code includes a custom `SQLiteMemoryService` class as an alternative to Vertex AI,
but it's currently disabled because it doesn't inherit from the correct base class.

**Pros:**
- Local persistence without cloud dependency
- No cost

**Cons:**
- Custom implementation not officially supported
- Requires maintaining compatibility with ADK interfaces
- No semantic search (only keyword matching)

---

## Recommendation

**For Development/Testing:**
- Keep using `InMemoryMemoryService`
- Use fixed `session_id` in interactive mode
- Memory persists within single program execution

**For Production:**
- Switch to `VertexAiMemoryBankService`
- Follow setup guide: https://google.github.io/adk-docs/sessions/memory/
- Get true persistent memory across restarts

---

## References

- [ADK Memory Documentation](https://google.github.io/adk-docs/sessions/memory/)
- [Agent Engine Setup](https://google.github.io/adk-docs/deploy/agent-engine/)
- [Sessions & State](https://google.github.io/adk-docs/sessions/)

