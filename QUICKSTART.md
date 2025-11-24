# Quick Start Guide - Pregnancy Companion Agent

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install google-adk python-dotenv
```

### Step 2: Set Your API Key
```bash
# Option A: Environment variable
export GOOGLE_API_KEY="your_api_key_here"

# Option B: Create .env file
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```

Get your API key: https://aistudio.google.com/app/apikey

### Step 3: Run the Demo
```bash
python pregnancy_companion_agent.py
```

That's it! You should see the demo running with all features.

## 📋 What You'll See

The demo demonstrates:

1. **Patient Introduction**
   - Agent remembers patient name, age, LMP, and history
   - Context is stored across conversation turns

2. **Risk Assessment**
   - Patient reports danger signs (dizziness, spots in vision)
   - Main agent calls Nurse Agent for specialized assessment
   - Risk level is communicated clearly

3. **EDD Calculation**
   - Agent calculates due date from LMP
   - Shows gestational age in weeks

4. **Evaluation**
   - LLM-as-a-Judge scores the interaction
   - Checks if safety protocols were followed

## 🎯 Try Your Own Interactions

### Basic Usage (Sync)
```python
from pregnancy_companion_agent import run_agent_interaction_sync

# Single interaction
response = run_agent_interaction_sync(
    "Hi, my name is Maria. My LMP was March 1, 2025.",
    user_id="maria_001"
)
print(response)

# Follow-up (same user_id for context)
response = run_agent_interaction_sync(
    "I have a severe headache and blurry vision.",
    user_id="maria_001"
)
print(response)
```

### Advanced Usage (Async)
```python
import asyncio
from pregnancy_companion_agent import run_agent_interaction

async def chat():
    # Session-based conversation
    session_id = "maria_session_001"
    
    response1 = await run_agent_interaction(
        "Hello, I'm 8 weeks pregnant.",
        user_id="maria",
        session_id=session_id
    )
    print(response1)
    
    response2 = await run_agent_interaction(
        "When is my baby due if my LMP was March 1, 2025?",
        user_id="maria",
        session_id=session_id
    )
    print(response2)

asyncio.run(chat())
```

## 🌐 Using ADK Web Interface

Run the agent with ADK's built-in web UI:

```bash
# From parent directory of this project
adk web --port 8000
```

Then open: http://localhost:8000

## 🔧 Configuration

### Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

### Different Model
```python
# Edit in pregnancy_companion_agent.py
MODEL_NAME = "gemini-2.0-flash-exp"  # or any other model
```

### Custom Session/Memory Services
```python
# For persistent memory
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="your-gcp-project",
    location="us-central1",
    agent_engine_id="your-agent-id"
)
```

## 📚 Key Features to Try

### 1. Memory Across Turns
```python
# First turn
run_agent_interaction_sync("My name is Sarah", user_id="sarah")

# Later turn - agent remembers
run_agent_interaction_sync("What's my name?", user_id="sarah")
```

### 2. EDD Calculation
```python
run_agent_interaction_sync(
    "My last period was January 1, 2025. When is my due date?",
    user_id="user_001"
)
```

### 3. Risk Assessment
```python
run_agent_interaction_sync(
    "I'm having severe bleeding and dizziness",
    user_id="user_001"
)
# Agent will call nurse agent automatically
```

### 4. Evaluation
```python
from pregnancy_companion_agent import evaluate_interaction

evaluation = await evaluate_interaction(
    user_input="I feel dizzy",
    agent_response="<agent response>",
    expected_behavior="Should assess risk"
)
print(f"Score: {evaluation['score']}/10")
```

## 🐛 Troubleshooting

### "Module 'google.adk' not found"
```bash
pip install --upgrade google-adk
```

### "API key not set"
Make sure you've set `GOOGLE_API_KEY` environment variable or created `.env` file.

### "No errors but nothing happens"
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Rate Limits
If you hit rate limits, wait a moment or use a different model tier.

## 📖 Next Steps

1. **Read the README.md** for comprehensive documentation
2. **Check MIGRATION_REPORT.md** to see what changed from original
3. **Explore the code** - it's well-commented
4. **Customize instructions** in the agent definitions
5. **Add new tools** following the pattern
6. **Deploy** using ADK deployment guides

## 🔗 Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Get API Key](https://aistudio.google.com/app/apikey)
- [ADK GitHub](https://github.com/google/adk-python)
- [Example Projects](https://google.github.io/adk-docs/tutorials/)

## 💡 Tips

- Use **consistent user_id** for conversation continuity
- Use **session_id** for explicit session management
- Enable **DEBUG logging** when developing
- Test with **different symptom scenarios** to see risk assessment
- Try **async version** for better performance in production
- Check **MIGRATION_REPORT.md** for feature comparison

## ✅ You're Ready!

If you can run the demo successfully, you have a fully working ADK-compliant pregnancy companion agent with:
- ✅ Memory management
- ✅ Tool calling
- ✅ Multi-agent architecture
- ✅ Safety protocols
- ✅ Evaluation system
- ✅ Professional logging

Happy coding! 🎉
