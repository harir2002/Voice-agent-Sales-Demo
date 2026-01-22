# AI Voice Agent Demo - Complete Documentation

**SBA Info Solutions Private Limited**

A comprehensive AI-powered voice agent system with sector-specific knowledge bases, featuring real-time speech recognition, intelligent responses, and natural voice synthesis.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Sectors Supported](#sectors-supported)
6. [Multi-Language Support](#multi-language-support)
7. [Human Handoff Protocol](#human-handoff-protocol)
8. [Installation & Setup](#installation--setup)
9. [Running the Application](#running-the-application)
10. [Project Structure](#project-structure)
11. [API Documentation](#api-documentation)
12. [Configuration](#configuration)
13. [Monitoring & Performance](#monitoring--performance)
14. [Recent Updates](#recent-updates)
15. [Troubleshooting](#troubleshooting)
16. [Testing](#testing)
17. [Deployment](#deployment)
18. [Twilio Voice Agent Guide](#twilio-voice-agent-guide)
19. [Question Bank](#question-bank)

---

## Overview

This AI Voice Agent Demo is a production-ready application that provides intelligent voice-based assistance across multiple industry sectors. The system uses advanced AI technologies for speech-to-text, natural language understanding, and text-to-speech to create seamless conversational experiences.

### Key Capabilities

- **Real-time Voice Interaction**: Continuous speech recognition with auto-submission
- **Sector-Specific Intelligence**: Dedicated knowledge bases for 6 different sectors
- **Interruption Handling**: Users can interrupt AI responses naturally
- **Context Switching**: Seamless topic changes within conversations
- **Sub-2 Second Latency**: Optimized with intelligent caching and parallel processing
- **Natural Voice Synthesis**: Sector-specific voice personalities
- **Multi-Language Support**: Supports 8 Indian languages and accents
- **Context Window**: Maintains conversation history for coherent responses
- **Human Handoff**: Automatic escalation to human agents when needed

---

## Features

### Core Features

- ✅ **Voice Recognition**: Browser-based Web Speech API with live transcription
- ✅ **AI-Powered Responses**: Groq Llama3 LLM with RAG (Retrieval Augmented Generation)
- ✅ **Natural Voice Output**: Sarvam AI TTS with sector-specific voices
- ✅ **Knowledge Base**: ChromaDB vector database with sector-specific documents
- ✅ **Intelligent Caching**: Multi-layer caching (Response, TTS, RAG)
- ✅ **Filler Phrases**: Masks processing delays for better UX
- ✅ **Auto-Detection**: Automatic silence detection and query submission
- ✅ **Interruption Support**: Stop AI mid-response to ask new questions

### Advanced Features
- 🤖 **Voice Agent (Twilio)**: Automated inbound/outbound calls with VoIP integration
- 📞 **Inbound Call Handling**: AI-driven responses for customer support via phone
- 📤 **Outbound Proactive Calls**: Automated reminders and offers with one-way message delivery
- 🔊 **Clear Audio (Neural)**: Optimized for phone lines using high-quality neural voices
- 🛡️ **Compliance & Privacy**: PII masking and automated consent recording
- 📊 **Call Analytics**: Live tracking of call status, duration, and sentiment
- 🔄 **Auto-Hangup**: Purpose-driven reminders automatically terminate after message delivery
- 🎨 **Modern UI**: Glassmorphism design with dashboard for call management
- 🎯 **Context Switching**: Change topics naturally without losing context
- 🌐 **Multi-Language Support**: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi
- 🧠 **Context Window**: Maintains last 10 messages for contextual responses
- 🤝 **Human Handoff**: Automatic detection and escalation to human agents
- 📱 **Responsive Design**: Works on desktop and mobile devices

---

## Architecture

### System Flow

```
User Speech → Web Speech API (STT) → Backend API → RAG Search (ChromaDB)
    ↓                                      ↓
Groq Llama3 (LLM) → Response Generation → Sarvam AI (TTS)
    ↓                                      ↓
Audio Playback ← Base64 Audio ← Backend Response
```

### Components

1. **Frontend (React + Vite)**
   - Voice input handling
   - Real-time transcription display
   - Audio playback management
   - Sector selection interface

2. **Backend (FastAPI)**
   - RESTful API endpoints
   - RAG implementation
   - LLM integration
   - TTS processing
   - Caching layer

3. **Knowledge Base (ChromaDB)**
   - Vector embeddings
   - Semantic search
   - Sector-specific collections

---

## Technology Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Vanilla CSS with Glassmorphism
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Speech Recognition**: Web Speech API

### Backend
- **Framework**: FastAPI (Python)
- **LLM**: Groq Llama3-8B-Instant
- **STT**: Groq Whisper-Large-V3
- **TTS**: Sarvam AI (Hindi/English)
- **Vector DB**: ChromaDB
- **Caching**: In-memory (Python dictionaries)

### AI Services
- **Groq**: Speech-to-Text & LLM
- **Sarvam AI**: Text-to-Speech
- **ChromaDB**: Vector embeddings & semantic search

---

## Sectors Supported

### 1. Banking (DEMO 1)
**Focus**: Account & Loan Support
- Account balance inquiries
- Loan applications and status
- Card services
- Fund transfers
- Interest rate information

### 2. Fintech/Financial Services (DEMO 2) ⭐ **Recently Updated**
**Focus**: Digital Payments, Investment & Wealth Management

**Fintech Services:**
- UPI & Digital Payments (Google Pay, PhonePe, Paytm)
- Digital Wallets & Prepaid Cards
- Neobanking (Jupiter, Fi, NiyoX)
- Buy Now Pay Later (BNPL)
- Cryptocurrency & Blockchain
- P2P Lending
- Robo-Advisory & AI Investing
- Digital Lending & Instant Loans
- Insurtech & Digital Insurance

**Traditional Financial Services:**
- Mutual Funds & SIPs
- Stock Trading & Equity
- Fixed Deposits & Bonds
- Portfolio Management
- Retirement Planning
- Tax Optimization
- Wealth Management

### 3. Insurance (DEMO 3)
**Focus**: Policy & Claim Support
- Policy information
- Claims status tracking
- Premium calculations
- Coverage details
- Policy renewals

### 4. BPO/KPO (DEMO 4)
**Focus**: Customer Support & Ticketing
- Ticket creation and tracking
- Issue resolution
- Escalation handling
- FAQ assistance

### 5. Healthcare - Appointments (DEMO 5)
**Focus**: Appointment Scheduling
- Doctor availability
- Appointment booking
- Rescheduling/Cancellation
- Clinic locations

### 6. Healthcare - Patient Records (DEMO 6)
**Focus**: Medical Records & Patient Services
- Lab results access
- Prescription refills
- Medication information
- Vaccination history

---

## Installation & Setup

### Prerequisites

- **Node.js**: v16 or higher
- **Python**: 3.9 or higher
- **API Keys**: Groq API Key, Sarvam API Key

### Step 1: Clone Repository

```bash
cd "c:\Users\HARI R\Desktop\Sales Application and Demo\Voice agents Demo"
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env

# Edit .env and add your API keys:
# GROQ_API_KEY=your_groq_api_key
# SARVAM_API_KEY=your_sarvam_api_key
# SARVAM_SPEAKER=anushka
# SARVAM_LANGUAGE=hi-IN
```

### Step 3: Initialize Knowledge Base

```bash
python init_knowledge_base.py
```

This will:
- Create ChromaDB collections for each sector
- Load and chunk knowledge base documents
- Generate vector embeddings
- Index all documents

### Step 4: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

---

## Running the Application

### Quick Start (Recommended)

Use the provided PowerShell script:

```powershell
.\start.ps1
```

This will:
1. Start the backend server (port 8000)
2. Start the frontend dev server (port 5173)
3. Open the application in your browser

### Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the Application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Project Structure

```
Voice agents Demo/
├── backend/
│   ├── knowledge_base/           # Sector-specific knowledge documents
│   │   ├── DEMO 1 BANKING - Account & Loan Support.txt
│   │   ├── DEMO 2 FINANCIAL SERVICES - Investment & Wealth Management.txt
│   │   ├── DEMO 3 INSURANCE - Policy & Claim Support.txt
│   │   ├── DEMO 4 BPOKPO - Customer Support & Ticketing.txt
│   │   ├── DEMO 5 HEALTHCARE - Appointment Scheduling.txt
│   │   └── DEMO 6 HEALTHCARE - Patient Support & Medical Records.txt
│   ├── chroma_db_v2/             # ChromaDB vector database
│   ├── venv/                     # Python virtual environment
│   ├── main.py                   # Main FastAPI application
│   ├── sarvam_tts.py            # Sarvam TTS integration
│   ├── monitoring.py            # Monitoring & metrics
│   ├── init_knowledge_base.py   # KB initialization script
│   ├── test_suite.py            # Test suite
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables (not in git)
│   └── .env.example             # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HomePage.jsx           # Landing page with sector selection
│   │   │   ├── DemoPage.jsx           # Demo page with sidebar
│   │   │   ├── VoiceAgentPage.jsx     # Main voice agent interface
│   │   │   ├── HomePage.css
│   │   │   ├── DemoPage.css
│   │   │   ├── VoiceAgentPage.css
│   │   │   └── CompanyStyles.css      # Shared styles
│   │   ├── App.jsx                    # Main app component
│   │   ├── App.css
│   │   └── main.jsx                   # Entry point
│   ├── public/
│   │   └── logo.png                   # Company logo
│   ├── package.json
│   └── vite.config.js
├── start.ps1                     # Quick start script
└── README.md                     # This file
```

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "online",
  "service": "Voice Agent API",
  "version": "1.0.0",
  "groq_status": "connected",
  "sarvam_tts_status": "connected",
  "cache_stats": {
    "response_cache": 0,
    "tts_cache": 0,
    "tts_cache_mb": 0.0,
    "rag_cache": 0
  }
}
```

#### 2. Get All Sectors
```http
GET /sectors
```

**Response:**
```json
[
  {
    "id": "banking",
    "title": "Banking AI Agent",
    "subtitle": "Automated Account & Loan Support",
    "icon": "🏦",
    "tags": "Retail Banking | Customer Service",
    "description": "AI-powered banking assistant",
    "features": [...],
    "sampleQueries": [...]
  },
  ...
]
```

#### 3. Get Specific Sector
```http
GET /sectors/{sector_id}
```

**Parameters:**
- `sector_id`: banking, financial, insurance, bpo, healthcare_appt, healthcare_patient

#### 4. Chat (Text Query)
```http
POST /chat
```

**Request Body:**
```json
{
  "query": "How do I use UPI for payments?",
  "sector": "financial"
}
```

**Response:**
```json
{
  "response": "UPI (Unified Payments Interface) allows instant bank-to-bank transfers 24/7. Download apps like Google Pay, PhonePe, or Paytm, link your bank account, and create a UPI PIN. You can then send money using UPI ID or QR code scanning.",
  "timestamp": "2025-12-06T11:30:00.000Z"
}
```

#### 5. Text-to-Speech
```http
POST /tts
```

**Request Body:**
```json
{
  "text": "Hello, how can I help you?",
  "sector": "financial"
}
```

**Response:**
```json
{
  "audio": "base64_encoded_audio_data",
  "timestamp": "2025-12-06T11:30:00.000Z"
}
```

#### 6. Speech-to-Text (Transcription)
```http
POST /transcribe
```

**Request:**
- Content-Type: multipart/form-data
- Field: `audio` (audio file)

**Response:**
```json
{
  "transcription": "How do I use UPI for payments?",
  "timestamp": "2025-12-06T11:30:00.000Z"
}
```

#### 7. Monitoring Endpoints

**Health Check:**
```http
GET /monitoring/health
```

**Metrics:**
```http
GET /monitoring/metrics
```

**Performance:**
```http
GET /monitoring/performance
```

**Errors:**
```http
GET /monitoring/errors
```

**Cache Stats:**
```http
GET /monitoring/cache
```

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Sarvam TTS Configuration
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_SPEAKER=anushka
SARVAM_LANGUAGE=hi-IN
```

### Voice Configuration

Sector-specific voices are configured in `backend/main.py`:

```python
VOICE_MAPPING = {
    "banking": "manisha",
    "financial": "manisha",
    "insurance": "manisha",
    "bpo": "manisha",
    "healthcare_appt": "manisha",
    "healthcare_patient": "manisha"
}
```

Available Sarvam AI voices:
- `meera` - Female voice (Hindi)
- `anushka` - Female voice (Hindi)
- `manisha` - Female voice (Hindi)
- `abhilash` - Male voice (Hindi)

### Frontend Configuration

API base URL is configured in each component:

```javascript
const API_BASE_URL = 'http://localhost:8000'
```

For production, update this to your deployed backend URL.

---

## Monitoring & Performance

### Built-in Monitoring

The application includes comprehensive monitoring capabilities:

1. **Health Checks**: Real-time service status
2. **Metrics Collection**: Request counts, response times, error rates
3. **Performance Tracking**: Latency measurements for each component
4. **Error Logging**: Detailed error tracking and reporting
5. **Cache Statistics**: Cache hit rates and memory usage

### Performance Optimizations

1. **Multi-Layer Caching**:
   - Response cache (LLM responses)
   - TTS cache (audio files)
   - RAG cache (search results)

2. **Smart RAG Skipping**:
   - Simple queries (greetings, thanks) bypass RAG
   - Saves 200-400ms per query

3. **Parallel Processing**:
   - TTS generation starts while LLM is processing
   - Audio playback begins immediately

4. **Fast LLM Model**:
   - Uses Llama-3.1-8B-Instant for sub-second responses
   - Optimized token limits (150 tokens max)

5. **Reduced Document Retrieval**:
   - Retrieves 2 documents instead of 3
   - Faster vector search

### Latency Targets

- **Total Response Time**: < 2 seconds
- **RAG Search**: < 300ms
- **LLM Generation**: < 800ms
- **TTS Generation**: < 600ms

---

## Recent Updates

### Fintech/Financial Services Enhancement (December 2025)

The Financial Services sector has been significantly expanded to include comprehensive Fintech capabilities:

#### What Changed:

1. **Knowledge Base Expansion** (3x content increase):
   - Added 9 new Fintech service categories
   - Enhanced traditional finance content
   - Expanded from 55 to 172 lines (12,318 characters)

2. **New Fintech Topics**:
   - Digital Payments & UPI
   - Digital Wallets & Prepaid Cards
   - Neobanking & Digital Banking
   - Buy Now Pay Later (BNPL)
   - Cryptocurrency & Blockchain
   - Peer-to-Peer (P2P) Lending
   - Robo-Advisory & AI Investing
   - Digital Lending & Instant Loans
   - Insurtech & Digital Insurance

3. **UI Updates**:
   - Title: "Fintech/Financial Services AI"
   - Subtitle: "Digital Payments, Investment & Wealth Management"
   - Updated welcome message
   - Added 10 new fintech sample queries

4. **Backend Updates**:
   - Enhanced sector configuration
   - Updated AI system prompt
   - Added fintech-specific features

#### Sample Fintech Queries:

- "How do I use UPI for payments?"
- "What is the UPI transaction limit?"
- "What are neobanks?"
- "Should I invest in cryptocurrency?"
- "How does BNPL work?"
- "Tell me about P2P lending"
- "What is robo-advisory?"

---

## Troubleshooting

### Common Issues

#### 1. ChromaDB Error: "no such column: collections.topic"

**Solution:**
```bash
cd backend
Remove-Item -Path "chroma_db_v2" -Recurse -Force
python init_knowledge_base.py
python main.py
```

#### 2. Frontend Not Connecting to Backend

**Check:**
- Backend is running on port 8000
- No CORS errors in browser console
- API_BASE_URL is correct in frontend components

**Solution:**
```bash
# Restart backend
cd backend
python main.py

# Restart frontend
cd frontend
npm run dev
```

#### 3. Voice Recognition Not Working

**Requirements:**
- Use Google Chrome browser
- Allow microphone permissions
- HTTPS connection (or localhost)

#### 4. TTS Audio Not Playing

**Check:**
- Sarvam API key is valid
- Speaker name is correct
- Audio format is supported by browser

#### 5. Slow Response Times

**Optimizations:**
- Clear caches: Restart backend
- Check internet connection
- Verify API rate limits
- Monitor backend logs for bottlenecks

### Debug Mode

Enable detailed logging in `backend/main.py`:

```python
logger.setLevel(logging.DEBUG)
```

---

## Testing

### Run Test Suite

```bash
cd backend
python test_suite.py
```

### Test Coverage

The test suite includes:
- ✅ Health check endpoint
- ✅ Sectors endpoint
- ✅ Chat endpoint (all sectors)
- ✅ TTS endpoint (all sectors)
- ✅ Transcription endpoint
- ✅ Knowledge base verification
- ✅ Cache functionality
- ✅ Error handling

### Manual Testing

1. **Voice Input**: Click mic, speak clearly, verify transcription
2. **AI Response**: Check response accuracy and relevance
3. **Audio Output**: Verify natural voice synthesis
4. **Interruption**: Speak while AI is talking
5. **Context Switch**: Change topics mid-conversation
6. **Sample Queries**: Test all sample queries for each sector

---

## Deployment

### Production Checklist

- [ ] Update API_BASE_URL in frontend to production URL
- [ ] Set up environment variables on server
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure auto-restart on failure
- [ ] Set up database backups
- [ ] Optimize caching strategy
- [ ] Load test the application
- [ ] Set up CDN for frontend assets

### Deployment Options

1. **Backend**:
   - Docker container
   - Cloud platforms (AWS, GCP, Azure)
   - Heroku, Railway, Render

2. **Frontend**:
   - Vercel, Netlify (recommended)
   - AWS S3 + CloudFront
   - GitHub Pages

3. **Database**:
   - Persistent volume for ChromaDB
   - Cloud storage for backups

### Docker Deployment (Optional)

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Support & Contact

**Company**: SBA Info Solutions Private Limited

For issues, questions, or feature requests, please contact the development team.

---

## License

Proprietary - SBA Info Solutions Private Limited

---

## Changelog

### Version 2.2 (January 2026) ⭐ **Latest**
- ✅ **Shareable Links**: Added React Router for direct URL access to individual demos
- ✅ **Sector-Specific URLs**: Each sector now has unique shareable links (e.g., `/demo/banking`, `/phone/insurance`)
- ✅ **Phone Call Links**: Separate URLs for phone demos with pre-selected sectors
- ✅ **Quick Action Links**: Direct access to Analytics, Calculators, and Playground
- ✅ **Documentation**: Added `SHAREABLE_LINKS.md` and `QUICK_LINKS.md` reference guides
- ✅ **Client-Ready**: Easy to share specific demos without navigation

### Version 2.1 (December 2025)
- ✅ **Multi-Language Support**: Added support for 8 Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi)
- ✅ **Indian Accent Recognition**: Enhanced speech recognition for Indian English accents
- ✅ **Context Window**: Implemented conversation history tracking (last 10 messages)
- ✅ **Human Handoff**: Automatic detection and escalation to human agents
- ✅ **Handoff Keywords**: 13+ trigger phrases for human escalation
- ✅ **Visual Indicators**: Language selector UI and handoff alert banners
- ✅ **Comprehensive Documentation**: Added HUMAN_HANDOFF_SCRIPT.md with agent protocols
- ✅ **Enhanced Instructions**: Updated UI with new feature indicators

### Version 2.0 (December 2025)
- ✅ Added comprehensive Fintech services to Financial sector
- ✅ Expanded knowledge base with 9 new fintech categories
- ✅ Updated UI branding to "Fintech/Financial Services"
- ✅ Enhanced AI system prompts
- ✅ Added 10 new fintech sample queries

### Version 1.0 (November 2025)
- ✅ Initial release with 6 sectors
- ✅ Voice recognition and synthesis
- ✅ RAG implementation with ChromaDB
- ✅ Interruption handling
- ✅ Context switching
- ✅ Performance optimizations
- ✅ Monitoring and metrics


---

## 🔗 Shareable Links

### Direct Access URLs

Each sector demo and phone call interface now has its own unique URL that can be shared directly with clients. This allows you to:
- Share specific demos without requiring navigation
- Bookmark frequently used demos
- Create custom landing pages for different clients

### Web Chat Interface Links

Access individual sector demos directly:

| Sector | URL Path | Example |
|--------|----------|---------|
| 🏦 Banking | `/demo/banking` | `https://your-app.com/demo/banking` |
| 📈 Financial Services | `/demo/financial` | `https://your-app.com/demo/financial` |
| 🛡️ Insurance | `/demo/insurance` | `https://your-app.com/demo/insurance` |
| 🎧 BPO/Support | `/demo/bpo` | `https://your-app.com/demo/bpo` |
| 🗓️ Healthcare (Appt) | `/demo/healthcare-appt` | `https://your-app.com/demo/healthcare-appt` |
| 📋 Healthcare (Patient) | `/demo/healthcare-patient` | `https://your-app.com/demo/healthcare-patient` |

### Phone Call Demo Links

Access Twilio phone demos with sector pre-selected:

| Sector | URL Path | Example |
|--------|----------|---------|
| 🏦 Banking Calls | `/phone/banking` | `https://your-app.com/phone/banking` |
| 📈 Financial Calls | `/phone/financial` | `https://your-app.com/phone/financial` |
| 🛡️ Insurance Calls | `/phone/insurance` | `https://your-app.com/phone/insurance` |
| 🎧 BPO Calls | `/phone/bpo` | `https://your-app.com/phone/bpo` |
| 🗓️ Healthcare (Appt) Calls | `/phone/healthcare-appt` | `https://your-app.com/phone/healthcare-appt` |
| 📋 Healthcare (Patient) Calls | `/phone/healthcare-patient` | `https://your-app.com/phone/healthcare-patient` |

### Other Quick Actions

| Feature | URL Path |
|---------|----------|
| 📊 Analytics Dashboard | `/analytics` |
| 🧮 ROI Calculators | `/calculators` |
| 🔊 TTS Playground | `/playground` |

### Usage Examples

**For Client Demos:**
```
Send to banking client: https://your-app.com/demo/banking
Send to insurance client: https://your-app.com/phone/insurance
```

**For Sales Presentations:**
- Share sector-specific links based on prospect's industry
- Each link opens directly to the relevant demo
- No navigation required - instant access

**Local Development:**
```
http://localhost:5173/demo/banking
http://localhost:5173/phone/financial
```

📋 **See `SHAREABLE_LINKS.md` and `QUICK_LINKS.md` for complete reference**

---

## Twilio Voice Agent Guide

The demo now includes a fully integrated **Twilio Voice Agent** for real-world VoIP interactions.

### 📞 Inbound Calls
- Customers can call your Twilio number.
- AI answers automatically with sector-specific knowledge.
- Live transcription and sentiment analysis are logged to the dashboard.

### 📤 Outbound Proactive Calls
- **Purpose-Driven**: Initiate calls for EMI reminders, appointment confirmations, etc.
- **Auto-Hangup**: For simple reminders, the AI delivers the message and hangs up automatically.
- **Conversational**: For "General" or "Offer" purposes, the AI engages in full conversation.

### 🛠️ Setup
1. Configure Twilio credentials in the **Twilio Demo** tab.
2. Use **ngrok** to expose your local server.
3. Update the Webhook URL in Twilio.

---

## Question Bank

A comprehensive question bank for testing all sectors in English and Hinglish is available in:
- 📄 `docs/VOICE_AGENT_QUESTION_BANK.md`
- 📄 `docs/TEST_QUESTIONS.md`

Use these scripts to verify the agent's accuracy and natural speech patterns.

---

**Built with ❤️ by SBA Info Solutions Private Limited**
