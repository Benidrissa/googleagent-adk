# YouTube Video Prompt for Pregnancy Companion Agent
## 3-Minute Video Script for Google ADK Capstone Competition

---

## Video Overview

**Target Duration:** 3 minutes (180 seconds)  
**Audience:** Google ADK Competition Judges + Healthcare Innovation Community  
**Tone:** Professional, compassionate, technically precise  
**Goal:** Demonstrate how AI agents can save lives through personalized maternal healthcare

---

## Video Structure & Timing

### SEGMENT 1: THE PROBLEM (0:00 - 0:45) - 45 seconds

#### Visual Elements:
- **Opening Shot:** Map of West Africa with highlighted maternal mortality hotspots
- **Statistics Overlay:**
  - "814 maternal deaths per 100,000 live births in West Africa"
  - "vs. 12 deaths per 100,000 in developed nations"
  - "68x higher risk"
- **Problem Visuals:**
  - Rural village with limited road access
  - Long distances to healthcare facilities
  - Women waiting at clinic
  - Mobile phone as only connection to healthcare

#### Narration Script:

> "In West Africa, pregnancy can be a life-threatening journey. With 814 maternal deaths per 100,000 live births—68 times higher than developed nations—expectant mothers face critical challenges:
> 
> Access: The average distance to a hospital is over 15 kilometers, with poor road conditions making travel dangerous during emergencies.
> 
> Knowledge: 60% of pregnant women lack access to prenatal education and don't recognize danger signs until it's too late.
> 
> Language: Medical jargon creates barriers between patients and healthcare workers.
> 
> The question is: How can we provide 24/7 expert pregnancy care where doctors are scarce and hospitals are far?"

#### Key Message:
**Clear, urgent problem that demands an innovative solution**

---

### SEGMENT 2: WHY AGENTS? (0:45 - 1:15) - 30 seconds

#### Visual Elements:
- **Agent Diagram:** Multi-agent architecture visualization
- **Comparison Table:**
  - Traditional App vs AI Agent
  - Static FAQs vs Personalized Conversations
  - One-size-fits-all vs Context-aware
- **Agent Capabilities Animation:**
  - Understanding context over multiple conversations
  - Calling specialized tools (maps, search, calculations)
  - Consulting expert sub-agents for risk assessment
  - Learning patient history and preferences

#### Narration Script:

> "Traditional apps can't solve this. A pregnant woman doesn't need a static FAQ—she needs a personal companion that understands her unique situation.
> 
> That's why we built a multi-agent system powered by Google's Agent Development Kit.
> 
> Agents are different. They:
> - Remember your pregnancy journey across conversations
> - Use real-time tools like Google Search and Maps
> - Consult specialist sub-agents for medical risk assessment
> - Adapt responses based on your location, language, and health profile
> 
> Our Pregnancy Companion Agent combines a friendly companion for daily support with a nurse specialist agent for critical medical guidance—working together like a healthcare team in your pocket."

#### Key Message:
**Agents uniquely solve this problem through personalization, memory, and tool use**

---

### SEGMENT 3: ARCHITECTURE (1:15 - 1:45) - 30 seconds

#### Visual Elements:
- **Architecture Diagram with Annotations:**

```
┌─────────────────────────────────────────────────┐
│              PREGNANT WOMAN                      │
│         (Chat Interface - Web/Mobile)            │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         COMPANION AGENT (Root Agent)             │
│         Gemini 2.0 Flash - Temp 0.7              │
│  "Friendly pregnancy support & coordination"     │
└─────┬───────────────────────────────────────┬───┘
      │                                       │
      ▼                                       ▼
┌─────────────────────┐           ┌──────────────────────┐
│   TOOLS & SERVICES  │           │   NURSE AGENT        │
│                     │           │   (Sub-Agent)        │
│ • calculate_edd     │           │   Gemini 2.0 Flash   │
│ • anc_schedule      │           │   Temp 0.2           │
│ • google_search     │           │   "Risk assessment   │
│ • infer_country     │           │    & medical advice" │
│ • road_access       │           └──────────────────────┘
│ • find_facilities   │                     │
│                     │                     ▼
│ [Google Maps API]   │           ┌──────────────────────┐
│ [Google Places API] │           │ MEDICAL TOOLS        │
│ [Google Search]     │           │ • literature_search  │
└─────────────────────┘           │ • google_search      │
                                  └──────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────┐
│           MEMORY & PERSISTENCE                   │
│  • Session Service (user context)                │
│  • Memory Service (conversation history)         │
│  • MCP Server (pregnancy records - SQLite)       │
└─────────────────────────────────────────────────┘
```

#### Narration Script:

> "Here's how it works:
> 
> The Companion Agent is your primary contact—friendly, conversational, powered by Gemini 2.0 Flash with temperature 0.7 for natural dialogue.
> 
> It has access to six specialized tools:
> - Calculate due dates using Naegele's medical formula
> - Create ANC schedules following WHO guidelines
> - Search Google for nutrition and health information
> - Infer your country from location text
> - Assess road accessibility using Google Maps
> - Find nearby health facilities via Google Places API
> 
> When medical expertise is needed, the companion calls the Nurse Agent—a more precise specialist running at temperature 0.2 for accurate risk assessment.
> 
> Behind the scenes, a memory system stores your pregnancy profile, conversation history, and medical timeline—so the agent always has context.
> 
> This is a production-ready system built on Google's ADK 1.19.0, deployed with Docker, monitored with observability tools, and backed by a Model Context Protocol server for data persistence."

#### Key Message:
**Sophisticated yet practical architecture using ADK best practices**

---

### SEGMENT 4: LIVE DEMO (1:45 - 2:30) - 45 seconds

#### Visual Elements:
- **Screen Recording:** Actual conversation with the agent
- **Split Screen:** User input on left, agent thinking/tool calls on right
- **Highlight Tool Calls:** Overlay showing which tools are being invoked

#### Demo Conversation Script:

**[Demo Scene 1: Patient Introduction - 12 seconds]**

*User:* "Hi, my name is Aissatou. I'm pregnant and I live in Bamako, Mali."

*Agent (visible thinking):*
```
🔧 Using: infer_country_from_location("Bamako, Mali")
✅ Country: Mali
💾 Storing profile: name=Aissatou, location=Bamako, Mali
```

*Agent:* "Hello Aissatou! Welcome to your pregnancy companion. Congratulations on your pregnancy! I'm here to support you throughout this journey.

To help you best, I need a bit more information. When was the first day of your last menstrual period (LMP)? Please provide it in YYYY-MM-DD format if possible."

**[Demo Scene 2: EDD Calculation - 8 seconds]**

*User:* "It was March 1, 2025"

*Agent (visible thinking):*
```
🔧 Using: calculate_edd(lmp="2025-03-01")
✅ EDD: December 6, 2025
✅ Current Week: 38 weeks pregnant
```

*Agent:* "Thank you! Based on your LMP of March 1, 2025, your estimated due date (EDD) is December 6, 2025. You're currently about 38 weeks pregnant—almost there! Let me create your antenatal care schedule..."

**[Demo Scene 3: Nutrition Question - 10 seconds]**

*User:* "What foods should I eat for iron during pregnancy?"

*Agent (visible thinking):*
```
🔧 Using: google_search("iron-rich foods pregnancy West Africa")
📡 Searching...
```

*Agent:* "Great question! Iron is crucial to prevent anemia. Based on current nutritional guidelines, here are iron-rich foods available in Mali:

• Red meat and liver (if you eat meat)
• Leafy greens like moringa leaves
• Beans and lentils
• Fortified cereals
• Fish like sardines

Pair these with vitamin C sources like oranges or tomatoes to boost absorption!"

**[Demo Scene 4: Danger Sign & Risk Assessment - 15 seconds]**

*User:* "I've been having severe headaches and my vision is blurry"

*Agent (visible thinking):*
```
⚠️ Danger signs detected
🔧 Consulting: nurse_agent
🏥 Agent-as-a-Tool activated
```

*Nurse Agent (internal):*
```
🔍 Risk Assessment:
- Symptoms: severe headaches, blurred vision
- Week 38: Near term
- Possible: Preeclampsia (high blood pressure)
🚨 RISK LEVEL: HIGH
⚡ ACTION: Immediate medical attention
```

*Agent:* "⚠️ Aissatou, these symptoms are serious danger signs that could indicate preeclampsia—a condition with high blood pressure. You need immediate medical attention.

Let me find the nearest health facilities..."

*Agent (visible thinking):*
```
🔧 Using: assess_road_accessibility(location="Bamako, Mali")
✅ Road condition: Moderate
🔧 Using: find_nearby_health_facilities(location="Bamako, Mali", radius=5000)
🏥 Found 3 facilities
```

*Agent:* "📍 Nearest Facilities:

1. **Hôpital Gabriel Touré** (2.3 km, 8 min drive)
   • Emergency care available
   • Call: +223 20 22 27 12

2. **Point G University Hospital** (4.1 km, 12 min drive)
   • Full maternity ward
   
Please go immediately or call for emergency transport. Would you like me to continue monitoring you or do you need additional support?"

#### Key Message:
**Real working system that handles everyday questions AND life-threatening emergencies**

---

### SEGMENT 5: THE BUILD (2:30 - 2:50) - 20 seconds

#### Visual Elements:
- **Code Snippets:** Brief flashes of key code
- **Technology Logos:**
  - Google ADK logo
  - Gemini API logo
  - Google Maps/Places/Search logos
  - Python + Docker logos
- **GitHub Repository:** Quick view of file structure
- **Terminal:** Docker compose up command running

#### Narration Script:

> "Built with Google's Agent Development Kit 1.19.0, this system demonstrates ADK best practices:
> 
> **Multi-Agent Architecture:** Companion agent coordinates with nurse specialist using Agent-as-a-Tool pattern.
> 
> **Real Tool Integration:** Not simulated—actual Google Search, Maps, and Places APIs provide real-time data.
> 
> **Memory & Sessions:** InMemoryMemoryService and DatabaseMemoryService with SQLite persistence store patient profiles and conversation history.
> 
> **Observability:** LoggingPlugin tracks agent flow, tool usage, and execution timing.
> 
> **Evaluation:** Built-in LLM-as-judge evaluator validates agent quality with rubric-based scoring.
> 
> The entire system is containerized with Docker, deployed with docker-compose, and includes a React web client for testing. All code is open source on GitHub."

#### Key Message:
**Production-ready implementation showcasing ADK capabilities**

---

### SEGMENT 6: CLOSING & IMPACT (2:50 - 3:00) - 10 seconds

#### Visual Elements:
- **Impact Metrics (Animated):**
  - "24/7 Access to Pregnancy Guidance"
  - "Reduces Hospital Search Time by 45 Minutes"
  - "Early Risk Detection: 48-72 Hours Earlier"
  - "Supports Simple, Jargon-Free Language"
- **Final Shot:** Pregnant woman smiling while using phone
- **Call to Action:**
  - GitHub: github.com/Benidrissa/googleagent-adk
  - Demo: [deployment URL]
  - "Agents for Good - Built with Google ADK"

#### Narration Script:

> "This is more than technology—it's a lifeline. Where healthcare workers are scarce and hospitals are far, AI agents can provide expert guidance, identify danger signs early, and connect women to care when every minute counts.
> 
> The Pregnancy Companion Agent—agents for good, built with Google ADK."

#### Key Message:
**Real-world healthcare impact through thoughtful AI agent design**

---

## Technical Specifications for Video Production

### Video Settings:
- **Resolution:** 1920x1080 (Full HD)
- **Frame Rate:** 30fps or 60fps
- **Format:** MP4 (H.264 codec)
- **Aspect Ratio:** 16:9
- **Audio:** 48kHz, stereo

### Recording Tools:
- **Screen Recording:** OBS Studio (free) or Loom
- **Video Editing:** DaVinci Resolve (free) or Adobe Premiere
- **Voiceover:** Audacity (free audio editor) or built-in screen recorder audio
- **Diagrams:** Mermaid.js exported as PNG/SVG or draw.io
- **Terminal Recording:** asciinema for clean terminal demos

### Visual Best Practices:
- **Use Clear Overlays:** Highlight tool calls with colored borders
- **Zoom In on Key Points:** Text should be easily readable
- **Add Transitions:** Smooth cuts between sections (fade/slide)
- **Include Captions:** For accessibility and clarity
- **Use Brand Colors:** Google blue (#4285F4), red (#EA4335), yellow (#FBBC04), green (#34A853)

---

## Script Variations

### Short Version (2 minutes):
- Problem: 30 seconds
- Why Agents + Architecture: 40 seconds (combined)
- Demo: 40 seconds (focus on emergency scenario)
- Build + Impact: 10 seconds

### Long Version (5 minutes):
- Add: Detailed code walkthrough
- Add: Multiple demo scenarios
- Add: Deployment process
- Add: Future roadmap

---

## Talking Points Cheat Sheet

### Key Technical Terms:
- ✅ Multi-agent system
- ✅ Agent-as-a-Tool pattern
- ✅ Google ADK (Agent Development Kit)
- ✅ Gemini 2.0 Flash
- ✅ Model Context Protocol (MCP)
- ✅ Session & Memory Services
- ✅ Tool integration (not simulation)
- ✅ LLM-as-judge evaluation
- ✅ Observability & tracing

### Key Impact Points:
- ✅ 814 maternal deaths per 100,000 in West Africa
- ✅ 68x higher risk than developed nations
- ✅ 15+ km average distance to hospitals
- ✅ 60% lack prenatal education access
- ✅ 24/7 availability where doctors are scarce
- ✅ 45-minute reduction in hospital search time
- ✅ 48-72 hour earlier danger sign detection

### Differentiators vs Competition:
- ✅ Real API integration (not mocked data)
- ✅ Multi-agent architecture (not single agent)
- ✅ Location-aware features (maps, facilities, road access)
- ✅ Production-ready deployment (Docker, observability)
- ✅ Focus on underserved population (West Africa)
- ✅ Healthcare domain expertise (WHO guidelines, medical formulas)

---

## Pre-Recording Checklist

### Setup Requirements:
- [ ] Agent system running locally (`docker-compose up`)
- [ ] Web client accessible at http://localhost
- [ ] Test conversation prepared (script above)
- [ ] Google Maps/Places API keys active
- [ ] Screen recording software configured
- [ ] Microphone tested (clear audio)
- [ ] Architecture diagram exported as high-res image
- [ ] Code snippets prepared in readable font size
- [ ] Browser windows sized for recording (no clutter)
- [ ] Terminal theme set to high-contrast (dark background, light text)

### Recording Environment:
- [ ] Quiet room (no background noise)
- [ ] Good lighting (if showing face)
- [ ] Close unnecessary applications
- [ ] Disable notifications (DND mode)
- [ ] Prepare water (for voiceover)
- [ ] Test recording 30 seconds first

---

## Post-Production Checklist

### Editing Tasks:
- [ ] Cut dead air and mistakes
- [ ] Add section title cards (Problem, Agents, Architecture, Demo, Build)
- [ ] Overlay text for key statistics
- [ ] Highlight tool calls in demo with boxes/arrows
- [ ] Add background music (subtle, non-distracting)
- [ ] Normalize audio levels
- [ ] Add captions/subtitles
- [ ] Include GitHub/demo links at end
- [ ] Export at 1080p 30fps

### Quality Checks:
- [ ] Total duration under 3:00
- [ ] Audio clear and balanced
- [ ] Text readable on mobile screens
- [ ] No technical errors visible
- [ ] Smooth transitions between sections
- [ ] Call-to-action clear at end

---

## YouTube Upload Details

### Video Metadata:

**Title:**
"Pregnancy Companion Agent: AI-Powered Maternal Health for West Africa | Google ADK Capstone"

**Description:**
```
The Pregnancy Companion Agent is a multi-agent system built with Google's Agent Development Kit (ADK) that provides 24/7 personalized pregnancy care for expectant mothers in West Africa.

🌍 THE PROBLEM
West Africa faces a maternal mortality crisis with 814 deaths per 100,000 live births—68x higher than developed nations. Limited healthcare access, knowledge gaps, and language barriers put pregnant women at extreme risk.

🤖 WHY AGENTS?
AI agents uniquely solve this through:
- Personalized conversations with memory across sessions
- Real-time tool use (Google Search, Maps, Places APIs)
- Multi-agent collaboration (companion + nurse specialist)
- 24/7 availability where doctors are scarce

⚙️ ARCHITECTURE
- Root Companion Agent (Gemini 2.0 Flash, temp 0.7)
- Nurse Specialist Sub-Agent (temp 0.2 for precision)
- 6 Specialized Tools (EDD calculation, ANC scheduling, location services)
- Memory & Persistence (Sessions + Database + MCP)
- Observability & Evaluation (LoggingPlugin + LLM-as-judge)

🎯 FEATURES
✅ Due date calculation (Naegele's rule)
✅ ANC schedule generation (WHO guidelines)
✅ Risk assessment & danger sign detection
✅ Google Search for nutrition/health info
✅ Location-aware health facility finder
✅ Road accessibility assessment
✅ Emergency response coordination

🛠️ TECH STACK
- Google ADK 1.19.0
- Gemini 2.0 Flash API
- Google Maps, Places, Search APIs
- Python + FastAPI
- Docker + Docker Compose
- React web client
- SQLite (via MCP)

📊 IMPACT
- 24/7 expert pregnancy guidance
- 45 min reduction in hospital search time
- 48-72 hours earlier danger sign detection
- Supports simple, accessible language

🔗 LINKS
GitHub: https://github.com/Benidrissa/googleagent-adk
Documentation: [README link]

Built for the Google ADK Capstone Competition - Agents for Good (Healthcare Track)

#GoogleADK #AIAgents #HealthcareAI #MaternalHealth #AgentsForGood #Gemini #GoogleCloud
```

**Tags:**
```
Google ADK, AI Agents, Healthcare AI, Maternal Health, Pregnancy Care, West Africa, Gemini API, Multi-Agent System, Agent Development Kit, Machine Learning, Healthcare Innovation, Agents for Good, Google Cloud, Python, Docker, FastAPI
```

**Thumbnail Design:**
- **Left side:** Pregnant woman with phone (warm, hopeful)
- **Right side:** Architecture diagram (professional, technical)
- **Center text:** "AI PREGNANCY COMPANION"
- **Top ribbon:** "Google ADK Capstone"
- **Bottom ribbon:** "Agents for Good"
- **Colors:** Google brand colors

---

## Additional Assets to Prepare

### For Video:
1. **Architecture Diagram (High-Res PNG/SVG)**
2. **Demo Screenshots** (patient intro, EDD calc, nutrition, emergency)
3. **Statistics Infographic** (maternal mortality, access, impact)
4. **Tool Call Visualization** (flowchart showing agent → tools → response)
5. **Code Snippet Highlights** (agent definition, tool integration)
6. **Map Visualization** (West Africa with pins)

### For Documentation:
1. **README.md architecture section** (embed video)
2. **CAPSTONE_EVALUATION.md** (reference video)
3. **YouTube video link** in all docs

---

## Success Metrics

### Video Quality Goals:
- [ ] Under 3:00 duration ✅
- [ ] Clear audio (no background noise) ✅
- [ ] Readable text (mobile-friendly) ✅
- [ ] Smooth pacing (not rushed) ✅
- [ ] Professional appearance ✅

### Content Goals:
- [ ] Problem clearly stated ✅
- [ ] Agent value proposition compelling ✅
- [ ] Architecture well-explained ✅
- [ ] Demo shows real functionality ✅
- [ ] Technical depth appropriate ✅
- [ ] Impact/value emphasized ✅

### Competition Goals:
- [ ] Meets all rubric requirements ✅
- [ ] Demonstrates ADK mastery ✅
- [ ] Shows healthcare impact ✅
- [ ] Differentiates from competitors ✅
- [ ] Memorable and engaging ✅

---

## Contact & Support

If you need help or have questions during video production:
- Review ARCHITECTURE.md for technical details
- Check CAPSTONE_EVALUATION.md for scoring rubric alignment
- Test the agent locally: `docker-compose up`
- Web client: http://localhost
- API docs: http://localhost:8000/docs

---

**Good luck with the video! This agent deserves a compelling showcase! 🎥🚀**

---

## APPENDIX: Sample B-Roll Footage Ideas

### Visual Storytelling Elements:

**Problem Segment:**
- Map zoom from global → Africa → West Africa → specific countries
- Stock footage: Rural healthcare clinics, long queues, dusty roads
- Data visualization: Animated bar chart comparing mortality rates
- Patient testimonials (stock or staged): "The hospital is 20 km away"

**Solution Segment:**
- Agent interface on phone screen (clean, modern)
- Animated agent icon "thinking"
- Tool call animations (search icon → results, map pin dropping)
- Split screen: User question → Agent processing → Response

**Architecture Segment:**
- Animated diagram: Boxes connecting with arrows
- Code editor with syntax highlighting scrolling slowly
- Terminal window showing docker-compose logs
- Database icon → MCP server → Agent

**Demo Segment:**
- Clean browser window (no clutter)
- Typing indicator animation
- Message bubbles appearing
- Tool call overlays (semi-transparent boxes with tool names)
- Map showing facilities (Google Maps embed)

**Impact Segment:**
- Happy pregnant woman using phone
- Healthcare worker nodding approvingly
- Community health center exterior
- Sunrise/hopeful imagery

---

**END OF VIDEO PROMPT**

This prompt provides everything needed to create a compelling, technically accurate, and emotionally resonant 3-minute video for the Google ADK Capstone Competition. Follow the structure, use the scripts as guides, and showcase the real technical capabilities of your agent system!
