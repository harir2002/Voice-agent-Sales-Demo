"""
FastAPI Backend for Voice Agent Demo
Handles STT, LLM, TTS, and RAG operations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
import time
import io
import wave
from datetime import datetime
import asyncio

# Import Sarvam TTS module
from sarvam_tts import (
    text_to_speech_stream, 
    text_to_speech_sync, 
    precache_common_phrases, 
    get_cache_stats as get_tts_cache_stats,
    get_precached_filler,
    FILLER_PHRASES
)

# Import Monitoring module
from monitoring import router as monitoring_router, MetricsCollector

# Import Twilio Integration module
from twilio_integration import twilio_router

# Import Call Analytics module for Dashboard
from call_analytics import analytics_router

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Voice Agent API", version="1.0.0")

# Configure Logging - ensure logs always appear
import logging
import sys

# Create logger
logger = logging.getLogger("voice_agent")
logger.setLevel(logging.INFO)
logger.propagate = False

# Clear any existing handlers and add fresh one (handles hot-reload)
logger.handlers.clear()
handler = logging.StreamHandler(sys.stderr)  # stderr is unbuffered
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Monitoring Router
app.include_router(monitoring_router)

# Include Twilio Router for Voice Calls
app.include_router(twilio_router)

# Include Call Analytics Router for Dashboard
app.include_router(analytics_router)

# Startup event to pre-cache filler phrases
@app.on_event("startup")
async def startup_event():
    """Pre-cache TTS filler phrases for instant playback during calls"""
    global sarvam_api_key
    if sarvam_api_key:
        logger.info("🚀 Pre-caching TTS filler phrases for low-latency calls...")
        try:
            await precache_common_phrases(sarvam_api_key)
            logger.info("✅ Filler phrases pre-cached successfully!")
        except Exception as e:
            logger.warning(f"⚠️ Failed to pre-cache filler phrases: {e}")
    else:
        logger.warning("⚠️ Sarvam API key not set - filler phrases won't be pre-cached")

# Request Logging Middleware with Metrics Collection
from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        
        # Record metrics for monitoring
        MetricsCollector.record_request(
            endpoint=request.url.path,
            duration_ms=process_time,
            status_code=response.status_code
        )
        
        # Only log slow requests or errors to keep logs clean, or specific endpoints
        if request.url.path in ["/chat", "/tts", "/transcribe"]:
            logger.info(f"🏁 {request.method} {request.url.path} completed in {process_time:.0f}ms")
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        
        # Record error for monitoring
        MetricsCollector.record_error(
            endpoint=request.url.path,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        
        raise

# Initialize clients
groq_client = None
sarvam_api_key = None
sarvam_speaker = "manisha"  # Default voice - bulbul:v2 valid speakers: anushka, abhilash, manisha, vidya, arya, karun, hitesh
sarvam_language = "en-IN"  # Default language - auto-detection will override if needed

try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq client: {e}")

# Language support for Indian accents and multilingual
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi"
}

# Human handoff triggers
HUMAN_HANDOFF_KEYWORDS = [
    "speak to human", "talk to human", "human agent", "real person",
    "escalate", "manager", "supervisor", "complaint", "not satisfied",
    "frustrated", "angry", "disappointed", "terrible service"
]

try:
    sarvam_api_key = os.getenv("SARVAM_API_KEY")
    if sarvam_api_key:
        # Get optional TTS settings
        sarvam_speaker = os.getenv("SARVAM_SPEAKER", "manisha")
        sarvam_language = os.getenv("SARVAM_LANGUAGE", "en-IN")  # Default to English
        logger.info(f"✅ Sarvam TTS configured: speaker={sarvam_speaker}, lang={sarvam_language}")
except Exception as e:
    logger.error(f"❌ Failed to initialize Sarvam TTS: {e}")

# ChromaDB client
try:
    # Disable telemetry to prevent warnings
    import chromadb.config
    chromadb.config.Settings(anonymized_telemetry=False)
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db_v2')
    chroma_client = chromadb.PersistentClient(
        path=db_path,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )
except Exception as e:
    logger.error(f"❌ Failed to initialize ChromaDB: {e}")

# ... (rest of the file)

    try:
        total_docs = 0
        for sector_id, config in SECTOR_CONFIG.items():
            try:
                collection_name = f"{sector_id}_knowledge"
                collection = chroma_client.get_or_create_collection(name=collection_name)
                count = collection.count()
                total_docs += count
                print(f"   📂 {config['title']:<30} : {count} documents")
            except Exception as e:
                print(f"   ⚠️ {sector_id:<30} : Error - {str(e)[:50]}...")
        
        print(f"\n   ✅ Total Indexed Documents: {total_docs}")
        
    except Exception as e:
        print(f"   ❌ Failed to check Knowledge Base: {e}")

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    sector: str
    conversation_history: Optional[List[dict]] = []  # For context window
    language: Optional[str] = "en"  # Support for multiple languages

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    needs_human_handoff: bool = False  # Flag for human escalation
    handoff_reason: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    sector: str = "banking"

class SectorInfo(BaseModel):
    id: str
    title: str
    subtitle: str
    icon: str
    tags: str
    description: str
    features: List[str]
    sampleQueries: List[str]

# Sector configurations
SECTOR_CONFIG = {
    "banking": {
        "id": "banking",
        "title": "Banking AI Agent",
        "subtitle": "Automated Account & Loan Support",
        "icon": "🏦",
        "tags": "Retail Banking | Customer Service",
        "description": "AI-powered banking assistant for account management and loan services",
        "features": [
            "Account balance inquiries",
            "Loan application status",
            "Transaction history",
            "Card services",
            "Fund transfers",
            "Interest rate information"
        ],
        "sampleQueries": [
            # English (15 questions)
            "What is my current account balance?",
            "How do I apply for a personal loan?",
            "What are the interest rates for home loans?",
            "Can you help me with card activation?",
            "How do I block my lost debit card?",
            "What is the minimum balance requirement?",
            "How to open a fixed deposit account?",
            "What are the charges for NEFT transfer?",
            "How to link Aadhaar with my bank account?",
            "What is the daily withdrawal limit for ATM?",
            "How to update my mobile number in bank account?",
            "What are the benefits of premium savings account?",
            "How to get a new cheque book?",
            "What is the process for education loan?",
            "How to enable international transactions on my card?",
            # Hinglish (Hindi + English) (15 questions)
            "Mera account balance kitna hai?",
            "Personal loan ke liye kya documents chahiye?",
            "Home loan ka interest rate kya hai?",
            "ATM card block kaise karu?",
            "Savings account kholna hai, kya process hai?",
            "UPI se paisa kaise bhejun?",
            "Fixed deposit mein interest kitna milta hai?",
            "Net banking activate kaise karun?",
            "Loan EMI kaise check karun?",
            "Debit card ka PIN reset kaise hoga?",
            "Credit card apply karne ka process kya hai?",
            "Account statement download kaise karun?",
            "Cheque book request kaise daalu?",
            "Mobile number update kaise karun account mein?",
            "Auto debit setup kaise karein?"
        ]
    },
    "financial": {
        "id": "financial",
        "title": "Fintech/Financial Services AI",
        "subtitle": "Digital Payments, Investment & Wealth Management",
        "icon": "📈",
        "tags": "Fintech | Investment Advisory | Digital Banking",
        "description": "Smart fintech solutions and financial planning services",
        "features": [
            "UPI & Digital Payments",
            "Neobanking & Digital Wallets",
            "Cryptocurrency & Blockchain",
            "Portfolio analysis",
            "Investment recommendations",
            "Robo-advisory services",
            "Market insights",
            "Risk assessment",
            "Retirement planning",
            "Tax optimization"
        ],
        "sampleQueries": [
            # English (15 questions)
            "How do I use UPI for payments?",
            "What is the UPI transaction limit?",
            "Should I invest in mutual funds or stocks?",
            "How do I start a SIP?",
            "What is the best mutual fund for high returns?",
            "How to invest in gold bonds?",
            "What are the tax benefits of ELSS funds?",
            "How to create a diversified portfolio?",
            "What is the difference between equity and debt funds?",
            "How to calculate returns on my investment?",
            "What is the minimum amount for SIP?",
            "How to redeem my mutual fund units?",
            "What is the best time to invest in stock market?",
            "How to open a demat account?",
            "What are the risks of cryptocurrency investment?",
            # Hinglish (Hindi + English) (15 questions)
            "UPI payment kaise karte hain?",
            "Mutual fund mein invest karna chahiye ya stocks mein?",
            "SIP kaise start karun?",
            "Mera portfolio ka performance kaisa hai?",
            "Tax bachane ke liye kya karun?",
            "Cryptocurrency mein invest karna safe hai?",
            "Gold bond mein invest kaise karun?",
            "ELSS fund kya hota hai?",
            "Demat account kholne ka process kya hai?",
            "NPS mein invest karna chahiye?",
            "FD se better return kahan milega?",
            "Stock market mein loss se kaise bache?",
            "PPF account ke kya benefits hain?",
            "Monthly 5000 ka SIP karun toh kitna milega?",
            "Tax saving investments kaun se hain?"
        ]
    },
    "insurance": {
        "id": "insurance",
        "title": "Insurance AI Agent",
        "subtitle": "Policy & Claim Support",
        "icon": "🛡️",
        "tags": "Policy Management | Claims",
        "description": "Comprehensive insurance policy and claims assistance",
        "features": [
            "Policy information",
            "Claims status tracking",
            "Premium calculations",
            "Coverage details",
            "Policy renewals",
            "Beneficiary updates"
        ],
        "sampleQueries": [
            # English (15 questions)
            "What does my health insurance cover?",
            "How do I file a claim?",
            "When is my policy renewal due?",
            "What is the status of my claim?",
            "Can I increase my coverage amount?",
            "What is the waiting period for my policy?",
            "How to add a family member to my policy?",
            "What documents are needed for claim settlement?",
            "Is dental treatment covered in my plan?",
            "How to download my policy document?",
            "What is the cashless hospital network?",
            "Can I port my insurance to another company?",
            "What is the premium for family floater plan?",
            "How to get a duplicate policy copy?",
            "Is maternity covered in my health insurance?",
            # Hinglish (Hindi + English) (15 questions)
            "Meri health insurance mein kya cover hota hai?",
            "Claim kaise file karun?",
            "Policy renewal kab due hai?",
            "Claim status kya hai mera?",
            "Premium online kaise pay karun?",
            "Car insurance mein engine damage cover hai?",
            "Family floater plan ka premium kitna hai?",
            "Cashless claim kaise milega?",
            "Policy document download kaise karun?",
            "Waiting period kitna hai?",
            "Nominee change kaise karun?",
            "Critical illness cover add karna hai",
            "Claim reject hone ka reason kya hai?",
            "Two wheeler insurance renew karna hai",
            "Term insurance lena chahiye ya endowment?"
        ]
    },
    "bpo": {
        "id": "bpo",
        "title": "BPO/KPO AI Agent",
        "subtitle": "Customer Support & Ticketing",
        "icon": "🎧",
        "tags": "Support Services | CX",
        "description": "Intelligent customer support and ticketing system",
        "features": [
            "Ticket creation",
            "Status updates",
            "Issue resolution",
            "Escalation handling",
            "FAQ assistance",
            "Service requests"
        ],
        "sampleQueries": [
            # English (15 questions)
            "I need to raise a support ticket",
            "What's the status of my ticket?",
            "How do I reset my password?",
            "I have a billing issue",
            "Can you escalate this to a supervisor?",
            "My order has not been delivered yet",
            "I want to cancel my subscription",
            "How to change my registered email?",
            "When will my refund be processed?",
            "I am facing login issues",
            "How to track my order?",
            "I need to update my address",
            "What are your customer support hours?",
            "How to file a complaint?",
            "I want to speak with a human agent",
            # Hinglish (Hindi + English) (15 questions)
            "Mujhe support ticket raise karna hai",
            "Mera ticket status kya hai?",
            "Password reset kaise karun?",
            "Billing mein problem hai",
            "Refund kab milega mera?",
            "Internet slow chal raha hai",
            "Order cancel karna hai",
            "Subscription deactivate kaise karun?",
            "Delivery kab hogi meri?",
            "Account lock ho gaya hai",
            "Payment fail ho gaya, paisa kab wapas milega?",
            "Customer care ka number kya hai?",
            "Complaint register karna hai",
            "Order track kaise karun?",
            "Address change karna hai account mein"
        ]
    },
    "healthcare_appt": {
        "id": "healthcare_appt",
        "title": "Healthcare AI (Appointments)",
        "subtitle": "Appointment Scheduling",
        "icon": "🗓️",
        "tags": "Healthcare | Scheduling",
        "description": "Smart appointment scheduling and clinic management",
        "features": [
            "Appointment scheduling",
            "Doctor availability",
            "Appointment reminders",
            "Reschedule/Cancel",
            "Clinic locations",
            "Department information"
        ],
        "sampleQueries": [
            # English (15 questions)
            "I need to book an appointment with a cardiologist",
            "What slots are available tomorrow?",
            "Can I reschedule my appointment?",
            "Which doctors are available for consultation?",
            "What are the consultation fees?",
            "How to cancel my appointment?",
            "Is video consultation available?",
            "What is the waiting time for walk-in?",
            "Do you have a specialist for diabetes?",
            "How early should I arrive for my appointment?",
            "Can I book for a family member?",
            "What are the clinic timings?",
            "Do you offer home visit services?",
            "How to book an emergency appointment?",
            "What documents should I bring for first visit?",
            # Hinglish (Hindi + English) (15 questions)
            "Cardiologist se appointment book karna hai",
            "Kal ke liye kya slots available hain?",
            "Appointment reschedule kar sakte hain?",
            "Consultation fees kitni hai?",
            "Video consultation book ho sakta hai?",
            "Doctor available hain Monday ko?",
            "Appointment cancel kaise karun?",
            "OPD timing kya hai?",
            "Diabetes specialist available hai?",
            "Emergency appointment mil sakta hai?",
            "Family member ke liye appointment book karna hai",
            "Reports ke liye aana padega ya online milega?",
            "Waiting time kitna hota hai?",
            "Home visit available hai?",
            "Sunday ko clinic khula hai?"
        ]
    },
    "healthcare_patient": {
        "id": "healthcare_patient",
        "title": "Healthcare AI (Patient Records)",
        "subtitle": "Medical Records & Patient Services",
        "icon": "📋",
        "tags": "Healthcare | Records",
        "description": "Patient records management and medical information",
        "features": [
            "Medical records access",
            "Prescription refills",
            "Lab results",
            "Treatment history",
            "Medication information",
            "Health tips"
        ],
        "sampleQueries": [
            # English (15 questions)
            "Can I get my recent lab results?",
            "I need a prescription refill",
            "What medications am I currently taking?",
            "Show me my vaccination history",
            "I need a copy of my medical records",
            "When was my last checkup?",
            "What is my blood group?",
            "Can I get my X-ray reports online?",
            "Show me my previous prescriptions",
            "What tests has the doctor recommended?",
            "Can I share my records with another hospital?",
            "What was my last diagnosis?",
            "How to update my emergency contact?",
            "What allergies are on my record?",
            "Can I download my health summary?",
            # Hinglish (Hindi + English) (15 questions)
            "Meri lab reports chahiye",
            "Prescription refill karni hai",
            "Main kaun si medicine le raha hoon?",
            "Vaccination history dikhao",
            "Medical records ki copy chahiye",
            "Blood test ke liye kaise prepare karun?",
            "Mera blood group kya hai?",
            "X-ray report online mil sakti hai?",
            "Previous prescriptions dikhao",
            "Doctor ne kaun se tests recommend kiye hain?",
            "Last checkup kab hua tha?",
            "Allergy details update karna hai",
            "Health report download kaise karun?",
            "Emergency contact change karna hai",
            "Previous diagnosis kya tha mera?"
        ]
    }
}

# Sarvam TTS Voice/Speaker mapping for different sectors
# Using Manisha for all sectors for consistency and guaranteed compatibility
VOICE_MAPPING = {
    "banking": "manisha",           # Professional female voice
    "financial": "manisha",         # Professional female voice
    "insurance": "manisha",         # Warm female voice
    "bpo": "manisha",               # Clear female voice
    "healthcare_appt": "manisha",   # Caring female voice
    "healthcare_patient": "manisha" # Empathetic female voice
}

# Caching system for low latency
from functools import lru_cache
import hashlib

# Response cache (in-memory)
response_cache = {}
tts_cache = {}
rag_cache = {}

# Common responses that can be pre-cached
COMMON_RESPONSES = {
    "greeting": "Hello! I'm your AI assistant. How can I help you today?",
    "thanks": "Okay, thank you! Let me know if you need anything else.",
    "goodbye": "Thank you for using our service. Have a great day!",
}

def get_cache_key(text: str) -> str:
    """Generate cache key from text"""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def is_simple_query(query: str) -> bool:
    """Detect if query is simple (greeting, thanks, etc.) and doesn't need RAG"""
    query_lower = query.lower().strip()
    simple_patterns = [
        'hello', 'hi', 'hey', 'greetings',
        'thank', 'thanks', 'appreciate',
        'bye', 'goodbye', 'see you',
        'ok', 'okay', 'got it', 'understood'
    ]
    return any(pattern in query_lower for pattern in simple_patterns) and len(query.split()) < 5

# Helper functions
def validate_audio(audio_bytes: bytes) -> tuple[bool, Optional[str]]:
    """Validate audio format and duration"""
    try:
        size_mb = len(audio_bytes) / (1024 * 1024)
        logger.info(f"Validating audio: {size_mb:.2f} MB")
        
        if len(audio_bytes) < 1000:
            logger.warning("Audio file too small")
            return False, "Audio file is too small"
        if len(audio_bytes) > 10 * 1024 * 1024:
            logger.warning("Audio file too large")
            return False, "Audio file is too large"
        return True, None
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return False, str(e)

def transcribe_audio(audio_bytes: bytes, sector: str = "banking") -> tuple[Optional[str], Optional[str]]:
    """
    Transcribe audio using ROBUST STT system
    
    Features:
    - Audio preprocessing (16kHz resampling, volume normalization)
    - Voice Activity Detection (VAD) 
    - Multi-model fallback (whisper-large-v3 → whisper-large-v3-turbo)
    - Sector-specific prompts for domain accuracy
    - Quality validation and retry strategies
    """
    logger.info("🎤 Starting ROBUST audio transcription...")
    
    try:
        if not groq_client:
            return None, "Groq client not initialized"
        
        is_valid, error = validate_audio(audio_bytes)
        if not is_valid:
            return None, error
        
        # Use robust STT module for enhanced transcription
        from robust_stt import robust_transcribe_audio
        
        transcription, trans_error = robust_transcribe_audio(
            audio_bytes=audio_bytes,
            groq_client=groq_client,
            sector=sector,
            source_format="wav"
        )
        
        if trans_error:
            logger.error(f"Robust STT failed: {trans_error}")
            return None, trans_error
        
        if not transcription or len(transcription.strip()) == 0:
            logger.warning("Empty transcription received")
            return None, "Could not transcribe audio"
        
        logger.info(f"✅ ROBUST Transcription success: '{transcription.strip()[:50]}...'")
        return transcription.strip(), None
        
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Unexpected error: {str(e)[:100]}"

def search_knowledge_base(query: str, sector: str) -> List[str]:
    """Search ChromaDB for relevant documents with caching"""
    cache_key = f"{sector}:{get_cache_key(query)}"
    
    # Check cache first
    if cache_key in rag_cache:
        logger.info(f"✅ RAG cache hit for query")
        return rag_cache[cache_key]
    
    logger.info(f"🔍 Searching knowledge base for sector '{sector}' with query: '{query[:30]}...'")
    try:
        collection_name = f"{sector}_knowledge"
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
        # Reduced from 3 to 2 documents for faster retrieval
        results = collection.query(
            query_texts=[query],
            n_results=2
        )
        
        docs = []
        if results and results['documents']:
            docs = results['documents'][0]
            logger.info(f"✅ Found {len(docs)} relevant documents")
            for i, doc in enumerate(docs):
                preview = doc[:100].replace('\n', ' ') + "..."
                logger.info(f"   📄 Doc {i+1}: {preview}")
        else:
            logger.info("⚠️ No relevant documents found")
        
        # Cache the result
        rag_cache[cache_key] = docs
        return docs
        
    except Exception as e:
        logger.error(f"Knowledge base search error: {e}")
        return []

def check_human_handoff(query: str) -> tuple[bool, Optional[str]]:
    """Check if query requires human handoff"""
    query_lower = query.lower()
    for keyword in HUMAN_HANDOFF_KEYWORDS:
        if keyword in query_lower:
            logger.info(f"🚨 Human handoff triggered by keyword: '{keyword}'")
            return True, keyword
    return False, None

def generate_ai_response(query: str, context_docs: List[str], sector: str, conversation_history: List[dict] = None, language: str = "en") -> tuple[str, bool, Optional[str]]:
    """Generate AI response using Groq Llama3 with caching, context window, and handoff detection"""
    
    # Check for human handoff first
    needs_handoff, handoff_keyword = check_human_handoff(query)
    if needs_handoff:
        handoff_response = "I understand you'd like to speak with a human agent. Let me connect you to our support team. Please hold on."
        return handoff_response, True, f"User requested human agent (keyword: {handoff_keyword})"
    
    # Check cache first
    cache_key = get_cache_key(query)
    if cache_key in response_cache:
        logger.info("✅ Response cache hit!")
        return response_cache[cache_key], False, None
    
    logger.info("🤖 Generating AI response...")
    max_retries = 2
    retry_delay = 0.5
    
    # Use FAST model for low latency
    primary_model = "llama-3.1-8b-instant"
    fallback_model = "llama-3.1-8b-instant"
    
    try:
        if not groq_client:
            return "AI service is not available", False, None
        
        # ===== DETECT QUERY LANGUAGE FIRST =====
        import re
        has_hindi_script = len(re.findall(r'[\u0900-\u097F]', query)) > 0
        hinglish_words = ['kya', 'hai', 'hain', 'mera', 'meri', 'kaise', 'chahiye', 'kitna', 'karna', 
                          'hoga', 'aap', 'hum', 'nahi', 'aur', 'toh', 'abhi', 'kal', 'paise', 'rupaye']
        query_words = query.lower().split()
        has_hinglish = any(word in hinglish_words for word in query_words)
        
        # Determine query language
        if has_hindi_script:
            query_language = "HINDI"
            response_instruction = "RESPOND IN HINDI SCRIPT (देवनागरी)."
            max_tokens_limit = 200
            logger.info("🌐 Query Language: Hindi Script")
        elif has_hinglish:
            query_language = "HINGLISH"
            response_instruction = "RESPOND IN HINGLISH (mix of Hindi and English words)."
            max_tokens_limit = 200
            logger.info("🌐 Query Language: Hinglish")
        else:
            query_language = "ENGLISH"
            response_instruction = "RESPOND ONLY IN ENGLISH. DO NOT USE ANY HINDI WORDS."
            max_tokens_limit = 250
            logger.info("🌐 Query Language: English")
        
        # Build context from documents
        if context_docs:
            context = "\n\n".join(context_docs[:2])
            context_note = f"\n\nRelevant Information:\n{context}\n\nPlease use the above information to answer accurately."
        else:
            context_note = "\n\nNote: No specific context available. Provide general helpful information."
        
        # Build conversation context window (last 5 exchanges)
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            recent_history = conversation_history[-10:]  # Last 5 user-AI exchanges (10 messages)
            conversation_context = "\n\nPrevious conversation context:\n"
            for msg in recent_history:
                role = "User" if msg.get("type") == "user" else "AI"
                conversation_context += f"{role}: {msg.get('text', '')}\n"
            conversation_context += "\nUse this context to provide coherent, contextual responses.\n"
        
        # ===== LANGUAGE INSTRUCTION AT THE START =====
        language_instruction = f"""
**MANDATORY LANGUAGE RULE**: The user's query is in {query_language}. {response_instruction}

This is the most important rule. If you respond in the wrong language, it will be a failure.
"""
        
        # Sector prompts WITHOUT language instruction (will be added at start)
        sector_descriptions = {
            "banking": "You are a professional banking AI assistant. Help users with account information, loan queries, and banking services.",
            "financial": "You are a fintech and financial services AI assistant. Help users with digital payments (UPI, wallets), neobanking, cryptocurrency, investment advice, portfolio management, and wealth planning.",
            "insurance": "You are an insurance AI assistant. Help users with policy information, claims processing, and coverage queries.",
            "bpo": "You are a customer support AI assistant. Help users with tickets, inquiries, and general support.",
            "healthcare_appt": "You are a healthcare AI assistant. Help users schedule appointments and manage clinic visits.",
            "healthcare_patient": "You are a patient support AI assistant. Help users with medical records and patient services."
        }
        
        sector_description = sector_descriptions.get(sector, "You are a helpful AI assistant.")
        
        # Build system prompt with language instruction FIRST
        system_prompt = f"""{language_instruction}

{sector_description}

Keep your response under 40 words. Be helpful and informative. End with complete sentences.
{context_note}{conversation_context}"""
        
        for attempt in range(max_retries):
            try:
                model_to_use = fallback_model if attempt > 0 else primary_model
                logger.info(f"LLM attempt {attempt + 1} using model {model_to_use}")
                
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    model=model_to_use,
                    temperature=0.5,  # Lower temperature for more consistent language following
                    max_tokens=max_tokens_limit,
                    top_p=0.9,
                    stream=False
                )

                
                response = chat_completion.choices[0].message.content
                
                if response and len(response.strip()) > 0:
                    response = response.strip()
                    
                    # 🔧 POST-PROCESS: Ensure Hindi responses are complete
                    if has_hindi_script or has_hinglish:
                        # Check if response ends with proper punctuation
                        if not response.endswith(('.', '?', '!', '।')):
                            logger.warning(f"⚠️ Response incomplete, fixing: '{response[-30:]}'")
                            # Try to find last complete sentence
                            last_period = response.rfind('.')
                            last_question = response.rfind('?')
                            last_exclamation = response.rfind('!')
                            last_danda = response.rfind('।')
                            
                            cut_index = max(last_period, last_question, last_exclamation, last_danda)
                            
                            if cut_index > 10:  # Found a sentence ending
                                response = response[:cut_index + 1]
                                logger.info(f"✂️ Truncated to complete sentence: '{response}'")
                            else:
                                # No sentence ending found, append period
                                response = response.rstrip(',;: ') + '.'
                                logger.info(f"📝 Added period to complete: '{response}'")
                    
                    logger.info(f"✅ Final response ({len(response)} chars): '{response}'")
                    # Cache the response
                    response_cache[cache_key] = response
                    return response, False, None
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                    
            except Exception as e:
                logger.error(f"LLM generation failed (attempt {attempt +  1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return "I encountered an error. Please try again.", False, None
        
        return "I'm having trouble generating a response right now.", False, None
        
    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}")
        return "Unexpected error occurred. Please try again.", False, None

async def text_to_speech(text: str, sector: str = "banking") -> tuple[Optional[bytes], Optional[str]]:
    """Convert text to speech using Sarvam AI WebSocket streaming"""
    logger.info(f"🔊 Converting text to speech with Sarvam AI: '{text[:30]}...'")
    
    try:
        if not sarvam_api_key:
            logger.error("Sarvam API key not configured")
            return None, "TTS service not available"
        
        if not text or len(text.strip()) == 0:
            return None, "No text provided"
        
        # Get sector-specific voice
        speaker = VOICE_MAPPING.get(sector, sarvam_speaker)
        
        # Use Sarvam TTS streaming
        audio_bytes, error = await text_to_speech_stream(
            text=text,
            api_key=sarvam_api_key,
            speaker=speaker,
            language_code=sarvam_language,
            sector=sector
        )
        
        if error:
            logger.error(f"Sarvam TTS error: {error}")
            return None, error
        
        return audio_bytes, None
        
    except Exception as e:
        logger.error(f"Unexpected TTS error: {e}")
        return None, "TTS error"

# Synchronous wrapper for text_to_speech (for non-async endpoints)
def text_to_speech_blocking(text: str, sector: str = "banking") -> tuple[Optional[bytes], Optional[str]]:
    """Synchronous version of text_to_speech for compatibility"""
    try:
        if not sarvam_api_key:
            return None, "TTS service not available"
        
        speaker = VOICE_MAPPING.get(sector, sarvam_speaker)
        
        # Use synchronous wrapper
        return text_to_speech_sync(
            text=text,
            api_key=sarvam_api_key,
            speaker=speaker,
            language_code=sarvam_language,
            sector=sector
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None, str(e)

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    logger.info("Health check requested")
    tts_stats = get_tts_cache_stats()
    return {
        "status": "online",
        "service": "Voice Agent API",
        "version": "1.0.0",
        "groq_status": "connected" if groq_client else "disconnected",
        "sarvam_tts_status": "connected" if sarvam_api_key else "disconnected",
        "cache_stats": {
            "response_cache": len(response_cache),
            "tts_cache": tts_stats["cached_items"],
            "tts_cache_mb": tts_stats["total_size_mb"],
            "rag_cache": len(rag_cache)
        }
    }

@app.get("/sectors")
async def get_sectors():
    """Get all available sectors"""
    logger.info("Fetching all sectors")
    return list(SECTOR_CONFIG.values())

@app.get("/sectors/{sector_id}")
async def get_sector(sector_id: str):
    """Get specific sector info"""
    logger.info(f"Fetching sector info for: {sector_id}")
    if sector_id not in SECTOR_CONFIG:
        logger.warning(f"Sector not found: {sector_id}")
        raise HTTPException(status_code=404, detail="Sector not found")
    return SECTOR_CONFIG[sector_id]

@app.post("/chat")
async def chat(request: ChatRequest):
    """Process text chat query with smart RAG skipping, context window, and handoff detection"""
    start_time = time.time()
    logger.info(f"📨 Query Received: '{request.query}' (Sector: {request.sector}, Language: {request.language})")
    
    try:
        # Skip RAG for simple queries (saves ~200-400ms)
        if is_simple_query(request.query):
            logger.info("⚡ Simple query detected - skipping RAG")
            context_docs = []
            
            # Check for common responses
            query_lower = request.query.lower()
            response_text = None
            
            if any(w in query_lower for w in ['thank', 'thanks']):
                response_text = COMMON_RESPONSES["thanks"]
            elif any(w in query_lower for w in ['bye', 'goodbye']):
                response_text = COMMON_RESPONSES["goodbye"]
            elif any(w in query_lower for w in ['hello', 'hi', 'hey']):
                response_text = COMMON_RESPONSES["greeting"]
                
            if response_text:
                total_time = (time.time() - start_time) * 1000
                logger.info(f"✅ Instant Response Sent in {total_time:.0f}ms")
                return ChatResponse(
                    response=response_text,
                    timestamp=datetime.now().isoformat(),
                    needs_human_handoff=False
                )
        else:
            # Search knowledge base
            rag_start = time.time()
            context_docs = search_knowledge_base(request.query, request.sector)
            rag_time = (time.time() - rag_start) * 1000
            logger.info(f"🔍 RAG Search Completed in {rag_time:.0f}ms")
        
        # Generate response with context window and handoff detection
        llm_start = time.time()
        response, needs_handoff, handoff_reason = generate_ai_response(
            request.query, 
            context_docs, 
            request.sector,
            request.conversation_history,
            request.language
        )
        llm_time = (time.time() - llm_start) * 1000
        logger.info(f"🧠 LLM Generation Completed in {llm_time:.0f}ms")
        
        if needs_handoff:
            logger.warning(f"🚨 Human handoff required: {handoff_reason}")
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Total Chat Processing Time: {total_time:.0f}ms")
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            needs_human_handoff=needs_handoff,
            handoff_reason=handoff_reason
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe audio file"""
    logger.info("Processing transcription request")
    try:
        audio_bytes = await audio.read()
        transcription, error = transcribe_audio(audio_bytes)
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return {"transcription": transcription}
    except Exception as e:
        logger.error(f"Transcribe endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def tts(request: TTSRequest):
    """Convert text to speech"""
    start_time = time.time()
    logger.info(f"🔊 TTS Request: '{request.text[:50]}...'")
    
    try:
        audio_bytes, error = await text_to_speech(request.text, request.sector)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"✅ TTS Generation Completed in {total_time:.0f}ms")
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        return {"audio": audio_base64}
    except Exception as e:
        logger.error(f"TTS endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Pydantic model for playground TTS
class PlaygroundTTSRequest(BaseModel):
    text: str
    speaker: str = "anushka"
    language_code: str = "en-IN"
    pace: float = 1.0

@app.post("/tts/playground")
async def tts_playground(request: PlaygroundTTSRequest):
    """TTS Playground - test different voices, languages, and pace settings"""
    start_time = time.time()
    logger.info(f"🎮 Playground TTS: voice={request.speaker}, lang={request.language_code}, pace={request.pace}")
    logger.info(f"📝 Text: '{request.text[:50]}...'")
    
    try:
        if not sarvam_api_key:
            raise HTTPException(status_code=500, detail="Sarvam API key not configured")
        
        # Import the streaming function directly
        from sarvam_tts import text_to_speech_stream
        
        audio_bytes, error = await text_to_speech_stream(
            text=request.text,
            api_key=sarvam_api_key,
            speaker=request.speaker,
            language_code=request.language_code,
            sector="banking",  # Default sector
            pace=request.pace
        )
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Playground TTS Completed in {total_time:.0f}ms")
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        return {"audio": audio_base64, "duration_ms": total_time}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playground TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Filler phrases to mask processing delays
FILLER_PHRASES = {
    "banking": [
        "Let me check that for you...",
        "One moment please...",
        "Let me look into that...",
        "Give me just a second..."
    ],
    "financial": [
        "Let me analyze that...",
        "One moment while I check...",
        "Let me review that for you...",
        "Just a moment..."
    ],
    "insurance": [
        "Let me verify that...",
        "One moment please...",
        "Let me check your policy details...",
        "Give me a second..."
    ],
    "bpo": [
        "Let me check that for you...",
        "One moment please...",
        "Let me look that up...",
        "Just a second..."
    ],
    "healthcare_appt": [
        "Let me check the schedule...",
        "One moment please...",
        "Let me see what's available...",
        "Give me just a moment..."
    ],
    "healthcare_patient": [
        "Let me check your records...",
        "One moment please...",
        "Let me look that up for you...",
        "Just a second..."
    ]
}

import random

def get_filler_phrase(sector: str) -> str:
    """Get a random filler phrase for the sector"""
    phrases = FILLER_PHRASES.get(sector, FILLER_PHRASES["banking"])
    return random.choice(phrases)

@app.post("/voice-chat")
async def voice_chat(audio: UploadFile = File(...), sector: str = "banking"):
    """Complete voice chat flow: STT -> LLM -> TTS with filler phrases"""
    logger.info(f"🚀 Starting full voice chat flow for sector: {sector}")
    
    filler_audio = None
    try:
        # Step 1: Transcribe audio
        audio_bytes = await audio.read()
        transcription, trans_error = transcribe_audio(audio_bytes)
        
        if trans_error:
            logger.error(f"Voice chat flow failed at transcription: {trans_error}")
            raise HTTPException(status_code=400, detail=trans_error)
        
        # Step 2: Generate filler phrase audio (parallel with processing)
        filler_text = get_filler_phrase(sector)
        logger.info(f"💬 Using filler: '{filler_text}'")
        
        # Generate filler audio asynchronously
        filler_audio_bytes, _ = await text_to_speech(filler_text, sector)
        
        # Step 3: Search knowledge base
        context_docs = search_knowledge_base(transcription, sector)
        
        # Step 4: Generate AI response
        ai_response = generate_ai_response(transcription, context_docs, sector)
        
        # Step 5: Convert response to speech
        audio_response, tts_error = await text_to_speech(ai_response, sector)
        
        import base64
        audio_base64 = None
        filler_base64 = None
        
        if filler_audio_bytes:
            filler_base64 = base64.b64encode(filler_audio_bytes).decode()
        
        if audio_response and not tts_error:
            audio_base64 = base64.b64encode(audio_response).decode()
        else:
            logger.warning("Voice chat flow completed without audio response")
        
        logger.info("✅ Voice chat flow completed successfully")
        return {
            "transcription": transcription,
            "response": ai_response,
            "audio": audio_base64,
            "filler_audio": filler_base64,  # Filler to play while processing
            "filler_text": filler_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Voice chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def print_separator():
    print("=" * 80)

def log_startup_status():
    """Log detailed startup status in the requested format"""
    print("\n")
    print_separator()
    print("🚀 VOICE AGENT BACKEND INITIALIZATION")
    print_separator()
    
    # Check Clients
    print(f"🎤 Groq Whisper (STT):   {'✅ Ready' if groq_client else '❌ Not Configured'}")
    print(f"🤖 Groq Llama3 (LLM):    {'✅ Ready' if groq_client else '❌ Not Configured'}")
    print(f"🔊 Sarvam AI (TTS):      {'✅ Ready' if sarvam_api_key else '❌ Not Configured'}")
    print(f"💾 ChromaDB (RAG):       {'✅ Ready' if 'chroma_client' in globals() else '❌ Failed'}")
    
    print_separator()
    print("📊 KNOWLEDGE BASE STATUS")
    print_separator()
    
    try:
        total_docs = 0
        for sector_id, config in SECTOR_CONFIG.items():
            try:
                collection_name = f"{sector_id}_knowledge"
                collection = chroma_client.get_or_create_collection(name=collection_name)
                count = collection.count()
                total_docs += count
                print(f"   📂 {config['title']:<30} : {count} documents")
            except Exception as e:
                print(f"   ⚠️ {sector_id:<30} : Error - {str(e)[:50]}...")
        
        print(f"\n   ✅ Total Indexed Documents: {total_docs}")
        
    except Exception as e:
        print(f"   ❌ Failed to check Knowledge Base: {e}")

    print_separator()
    print("🎉 SYSTEM READY")
    print_separator()
    print(f"📍 Backend running on: http://0.0.0.0:8000")
    print(f"📍 Frontend running on: http://localhost:5173")
    print_separator()
    print("\n")

if __name__ == "__main__":
    import uvicorn
    
    # Print the beautiful startup logs
    log_startup_status()
    
    # Run the server
    # We suppress standard uvicorn logs to keep it clean, unless there's an error
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="error")
