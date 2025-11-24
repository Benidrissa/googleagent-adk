# Testing Long-Term Memory in Interactive Mode

## How to Test Memory:

### 1. **Basic Information Recall**
Start a session and provide your details:
```
You: Hi, I'm Amina from Lagos. My LMP was January 1st, 2025.
```

Then in a later message, ask without repeating info:
```
You: What is my due date again?
```
✅ Agent should remember your LMP and respond with the EDD.

---

### 2. **Location Memory**
First interaction:
```
You: I live in Lagos, Nigeria.
```

Later interaction:
```
You: What foods should I eat?
```
✅ Agent should provide Nigerian-specific foods without asking location again.

---

### 3. **Multi-Turn Context**
Turn 1:
```
You: I'm 8 weeks pregnant and feeling nauseous.
```

Turn 2:
```
You: Is this normal at my stage?
```
✅ Agent should remember you're 8 weeks and nauseous.

---

### 4. **Preference Memory**
Turn 1:
```
You: I'm vegetarian.
```

Turn 2:
```
You: What protein sources do you recommend?
```
✅ Agent should provide vegetarian protein options.

---

### 5. **Session Persistence Test**
To test if memory persists within the same session:

**Conversation Flow:**
1. Introduce yourself with name, location, and LMP
2. Ask about nutrition (agent should know your location)
3. Ask about your due date (agent should remember LMP)
4. Mention a symptom
5. Ask follow-up about the symptom (agent should remember it)

---

## Example Full Test Sequence:

```
You: Hello, I'm Fatima from Bamako. My last period was February 15, 2025.

Agent: [Calculates EDD, greets]

You: I've been having morning sickness. Is that normal?

Agent: [Responds about morning sickness]

You: What foods can help with the nausea?

Agent: [Should remember location and provide Malian-appropriate foods]

You: When is my baby due again?

Agent: [Should remember LMP from first message]

You: Can I travel at my current stage?

Agent: [Should know gestational age from LMP]
```

## What Memory Should Persist:
✅ Patient name
✅ Location/country
✅ LMP date
✅ Due date (once calculated)
✅ Gestational age
✅ Symptoms mentioned
✅ Preferences (diet, etc.)
✅ Previous questions/concerns

## Memory Limitations:
⚠️ Memory only persists within the SAME session_id
⚠️ If you restart interactive_demo.py, it creates a NEW session
⚠️ For true persistent memory across restarts, you'd need database storage

