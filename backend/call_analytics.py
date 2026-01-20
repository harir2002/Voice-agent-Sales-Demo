"""
Call Analytics Module for Voice Agent Demo
Handles call logging, transcription storage, sentiment analysis, and analytics
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
from collections import defaultdict

# Sentiment analysis using pattern matching (lightweight approach)
# For production, you would use a proper ML model

logger = logging.getLogger(__name__)

# Router for call analytics endpoints
analytics_router = APIRouter(prefix="/analytics", tags=["Call Analytics"])


# ==================== ENUMS ====================

class CallType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    CANCELED = "canceled"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class CallOutcome(str, Enum):
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CALLBACK_REQUESTED = "callback_requested"
    ABANDONED = "abandoned"
    UNKNOWN = "unknown"


# ==================== PYDANTIC MODELS ====================

class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    speaker: str = Field(..., description="'customer' or 'agent'")
    text: str
    timestamp: str
    sentiment: Optional[Sentiment] = None
    latency_ms: Optional[int] = None  # For agent responses


class CallRecord(BaseModel):
    """Complete call record with all details"""
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    call_sid: Optional[str] = None  # Twilio Call SID
    call_type: CallType
    status: CallStatus
    sector: str
    
    # Phone numbers
    from_number: str
    to_number: str
    
    # Timing
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    ring_duration_seconds: Optional[int] = None
    
    # Conversation
    transcription: List[ConversationTurn] = []
    full_transcript: Optional[str] = None
    
    # Analysis
    overall_sentiment: Optional[Sentiment] = None
    sentiment_breakdown: Optional[Dict[str, float]] = None  # positive, neutral, negative percentages
    customer_intent: Optional[str] = None
    topics_discussed: List[str] = []
    outcome: CallOutcome = CallOutcome.UNKNOWN
    
    # Performance metrics
    avg_response_latency_ms: Optional[int] = None
    total_agent_turns: int = 0
    total_customer_turns: int = 0
    human_handoff_requested: bool = False
    
    # Additional metadata
    language: str = "en"
    notes: Optional[str] = None
    tags: List[str] = []


class CallAnalyticsSummary(BaseModel):
    """Summary statistics for calls"""
    total_calls: int
    inbound_calls: int
    outbound_calls: int
    completed_calls: int
    avg_duration_seconds: float
    avg_sentiment_score: float
    sentiment_distribution: Dict[str, int]
    top_intents: List[Dict[str, Any]]
    calls_by_sector: Dict[str, int]
    calls_by_hour: Dict[int, int]
    resolution_rate: float
    human_handoff_rate: float


class CreateCallRecordRequest(BaseModel):
    """Request to create a new call record"""
    call_sid: Optional[str] = None
    call_type: CallType
    sector: str
    from_number: str
    to_number: str
    language: str = "en"


class UpdateCallRecordRequest(BaseModel):
    """Request to update an existing call record"""
    status: Optional[CallStatus] = None
    end_time: Optional[str] = None
    transcription_turn: Optional[ConversationTurn] = None
    outcome: Optional[CallOutcome] = None
    notes: Optional[str] = None
    human_handoff_requested: Optional[bool] = None


# ==================== PERSISTENT STORAGE ====================
# Call logs are saved to a JSON file to persist across server restarts

CALL_LOGS_FILE = os.path.join(os.path.dirname(__file__), "data", "call_logs.json")

# Ensure data directory exists
os.makedirs(os.path.dirname(CALL_LOGS_FILE), exist_ok=True)

# In-memory storage (loaded from file on startup)
call_records: Dict[str, CallRecord] = {}

# Call SID to Call ID mapping for quick lookup
call_sid_mapping: Dict[str, str] = {}


def save_call_logs():
    """Save call records to JSON file for persistence"""
    try:
        data = {
            "call_records": {k: v.model_dump() for k, v in call_records.items()},
            "call_sid_mapping": call_sid_mapping,
            "last_saved": datetime.now().isoformat()
        }
        with open(CALL_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved {len(call_records)} call records to disk")
    except Exception as e:
        logger.error(f"❌ Failed to save call logs: {e}")


def load_call_logs():
    """Load call records from JSON file on startup"""
    global call_records, call_sid_mapping
    
    if not os.path.exists(CALL_LOGS_FILE):
        logger.info("📂 No existing call logs file found. Starting fresh.")
        return
    
    try:
        with open(CALL_LOGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Restore call records
        for call_id, call_data in data.get("call_records", {}).items():
            call_records[call_id] = CallRecord(**call_data)
        
        # Restore SID mapping
        call_sid_mapping.update(data.get("call_sid_mapping", {}))
        
        last_saved = data.get("last_saved", "unknown")
        logger.info(f"📂 Loaded {len(call_records)} call records from disk (last saved: {last_saved})")
    except Exception as e:
        logger.error(f"❌ Failed to load call logs: {e}")


# Load existing call logs on module import
load_call_logs()


# ==================== HELPER FUNCTIONS FOR TWILIO INTEGRATION ====================

def create_call_from_twilio(
    call_sid: str,
    call_type: str,
    from_number: str,
    to_number: str,
    sector: str = "banking",
    language: str = "en"
) -> CallRecord:
    """Create a new call record when a Twilio call starts"""
    call = CallRecord(
        call_sid=call_sid,
        call_type=CallType.INBOUND if call_type == "inbound" else CallType.OUTBOUND,
        status=CallStatus.IN_PROGRESS,
        sector=sector,
        from_number=from_number,
        to_number=to_number,
        start_time=datetime.now().isoformat(),
        language=language
    )
    
    call_records[call.call_id] = call
    call_sid_mapping[call_sid] = call.call_id
    
    # Save to disk for persistence
    save_call_logs()
    
    logger.info(f"📞 Created live call record: {call.call_id} (SID: {call_sid}, Type: {call_type})")
    return call


def add_transcription_turn(
    call_sid: str,
    speaker: str,
    text: str,
    latency_ms: Optional[int] = None
) -> Optional[CallRecord]:
    """Add a transcription turn to an existing call"""
    if call_sid not in call_sid_mapping:
        logger.warning(f"⚠️ Call SID not found: {call_sid}")
        return None
    
    call_id = call_sid_mapping[call_sid]
    if call_id not in call_records:
        return None
    
    call = call_records[call_id]
    
    # Create conversation turn
    turn = ConversationTurn(
        speaker=speaker,
        text=text,
        timestamp=datetime.now().strftime("%H:%M:%S"),
        sentiment=analyze_sentiment(text),
        latency_ms=latency_ms
    )
    
    call.transcription.append(turn)
    
    # Update turn counts
    if speaker == "agent":
        call.total_agent_turns += 1
    else:
        call.total_customer_turns += 1
    
    call_records[call_id] = call
    
    # Save periodically (every 5 turns to avoid too frequent writes)
    if (call.total_agent_turns + call.total_customer_turns) % 5 == 0:
        save_call_logs()
    
    logger.info(f"💬 Added turn to call {call_sid}: [{speaker}] {text[:50]}...")
    
    return call


def complete_call_from_twilio(
    call_sid: str,
    status: str = "completed",
    duration: Optional[int] = None
) -> Optional[CallRecord]:
    """Complete a call record when the Twilio call ends"""
    if call_sid not in call_sid_mapping:
        logger.warning(f"⚠️ Call SID not found for completion: {call_sid}")
        return None
    
    call_id = call_sid_mapping[call_sid]
    if call_id not in call_records:
        return None
    
    call = call_records[call_id]
    
    # Map Twilio status to our status
    status_map = {
        "completed": CallStatus.COMPLETED,
        "failed": CallStatus.FAILED,
        "busy": CallStatus.BUSY,
        "no-answer": CallStatus.NO_ANSWER,
        "canceled": CallStatus.CANCELED
    }
    call.status = status_map.get(status, CallStatus.COMPLETED)
    call.end_time = datetime.now().isoformat()
    
    if duration:
        call.duration_seconds = duration
    else:
        # Calculate from timestamps
        start = datetime.fromisoformat(call.start_time)
        end = datetime.fromisoformat(call.end_time)
        call.duration_seconds = int((end - start).total_seconds())
    
    # Perform final analysis
    if call.transcription:
        # Calculate overall sentiment
        sentiments = [turn.sentiment for turn in call.transcription if turn.sentiment]
        if sentiments:
            pos_count = sentiments.count(Sentiment.POSITIVE)
            neu_count = sentiments.count(Sentiment.NEUTRAL)
            neg_count = sentiments.count(Sentiment.NEGATIVE)
            total = len(sentiments)
            
            call.sentiment_breakdown = {
                "positive": round(pos_count / total * 100),
                "neutral": round(neu_count / total * 100),
                "negative": round(neg_count / total * 100)
            }
            
            if pos_count >= neg_count and pos_count >= neu_count:
                call.overall_sentiment = Sentiment.POSITIVE
            elif neg_count > pos_count and neg_count > neu_count:
                call.overall_sentiment = Sentiment.NEGATIVE
            else:
                call.overall_sentiment = Sentiment.NEUTRAL
        
        # Calculate average latency
        latencies = [turn.latency_ms for turn in call.transcription if turn.latency_ms]
        if latencies:
            call.avg_response_latency_ms = int(sum(latencies) / len(latencies))
        
        # Extract intent
        call.customer_intent = extract_intent(call.transcription)
        
        # Generate full transcript
        call.full_transcript = "\n".join([
            f"{turn.speaker.upper()}: {turn.text}" for turn in call.transcription
        ])
    
    # Determine outcome
    if call.human_handoff_requested:
        call.outcome = CallOutcome.ESCALATED
    elif call.transcription and any("thank" in t.text.lower() for t in call.transcription):
        call.outcome = CallOutcome.RESOLVED
    elif call.status == CallStatus.COMPLETED:
        call.outcome = CallOutcome.RESOLVED
    else:
        call.outcome = CallOutcome.ABANDONED
    
    call_records[call_id] = call
    
    # Save to disk on call completion (important!)
    save_call_logs()
    
    logger.info(f"✅ Completed call record: {call_id} (SID: {call_sid}, Duration: {call.duration_seconds}s)")
    
    return call


def get_call_by_sid(call_sid: str) -> Optional[CallRecord]:
    """Get a call record by Twilio Call SID"""
    if call_sid not in call_sid_mapping:
        return None
    return call_records.get(call_sid_mapping[call_sid])


def set_human_handoff(call_sid: str) -> Optional[CallRecord]:
    """Mark a call as requiring human handoff"""
    if call_sid not in call_sid_mapping:
        return None
    
    call_id = call_sid_mapping[call_sid]
    if call_id not in call_records:
        return None
    
    call = call_records[call_id]
    call.human_handoff_requested = True
    call_records[call_id] = call
    
    logger.info(f"🚨 Human handoff triggered for call: {call_sid}")
    return call


# ==================== TWILIO CALL HISTORY SYNC ====================

async def sync_twilio_call_history(client, phone_number: str, limit: int = 50):
    """
    Fetch call history from Twilio and add to our records.
    This imports historical calls that happened before the dashboard was active.
    """
    try:
        logger.info(f"📥 Syncing call history from Twilio for {phone_number}...")
        
        # Fetch inbound calls (calls TO our number)
        inbound_calls = client.calls.list(to=phone_number, limit=limit)
        
        # Fetch outbound calls (calls FROM our number)
        outbound_calls = client.calls.list(from_=phone_number, limit=limit)
        
        synced_count = 0
        
        for twilio_call in inbound_calls + outbound_calls:
            # Skip if we already have this call
            if twilio_call.sid in call_sid_mapping:
                continue
            
            # Determine call type
            call_type = CallType.INBOUND if twilio_call.to == phone_number else CallType.OUTBOUND
            
            # Map Twilio status
            status_map = {
                "completed": CallStatus.COMPLETED,
                "failed": CallStatus.FAILED,
                "busy": CallStatus.BUSY,
                "no-answer": CallStatus.NO_ANSWER,
                "canceled": CallStatus.CANCELED,
                "in-progress": CallStatus.IN_PROGRESS,
                "ringing": CallStatus.RINGING,
                "queued": CallStatus.INITIATED
            }
            
            # Create call record
            call = CallRecord(
                call_sid=twilio_call.sid,
                call_type=call_type,
                status=status_map.get(twilio_call.status, CallStatus.COMPLETED),
                sector="unknown",  # Twilio doesn't track this
                from_number=twilio_call.from_,
                to_number=twilio_call.to,
                start_time=twilio_call.start_time.isoformat() if twilio_call.start_time else datetime.now().isoformat(),
                end_time=twilio_call.end_time.isoformat() if twilio_call.end_time else None,
                duration_seconds=twilio_call.duration if twilio_call.duration else 0,
                overall_sentiment=Sentiment.NEUTRAL,  # Unknown without transcription
                outcome=CallOutcome.RESOLVED if twilio_call.status == "completed" else CallOutcome.UNKNOWN
            )
            
            call_records[call.call_id] = call
            call_sid_mapping[twilio_call.sid] = call.call_id
            synced_count += 1
        # Save all synced records to disk
        if synced_count > 0:
            save_call_logs()
        
        logger.info(f"✅ Synced {synced_count} calls from Twilio history")
        return synced_count
        
    except Exception as e:
        logger.error(f"❌ Failed to sync Twilio call history: {e}")
        return 0


# ==================== SENTIMENT ANALYSIS ====================

def analyze_sentiment(text: str) -> Sentiment:
    """Simple keyword-based sentiment analysis"""
    text_lower = text.lower()
    
    positive_keywords = [
        "thank", "thanks", "great", "excellent", "perfect", "amazing", "wonderful",
        "helpful", "good", "appreciate", "happy", "pleased", "satisfied", "love",
        "fantastic", "awesome", "brilliant", "superb", "delighted"
    ]
    
    negative_keywords = [
        "angry", "frustrated", "upset", "terrible", "horrible", "bad", "worst",
        "unacceptable", "disappointed", "unhappy", "hate", "annoying", "useless",
        "painful", "worried", "problem", "issue", "complaint", "waiting"
    ]
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    
    if positive_count > negative_count:
        return Sentiment.POSITIVE
    elif negative_count > positive_count:
        return Sentiment.NEGATIVE
    return Sentiment.NEUTRAL


def extract_intent(transcription: List[ConversationTurn]) -> str:
    """Extract customer intent from conversation"""
    intent_keywords = {
        "Account Balance Inquiry": ["balance", "account", "how much"],
        "Transaction History": ["transaction", "history", "statement", "recent"],
        "Loan Inquiry": ["loan", "emi", "interest rate", "borrow"],
        "Policy Renewal": ["renew", "renewal", "policy", "expire"],
        "Claim Status": ["claim", "status", "submitted"],
        "Appointment Booking": ["book", "appointment", "schedule", "slot"],
        "Refund Request": ["refund", "return", "money back"],
        "Technical Support": ["not working", "error", "problem", "issue"],
        "Investment Query": ["invest", "sip", "mutual fund", "stock", "portfolio"],
        "General Inquiry": ["information", "know", "tell me about"]
    }
    
    customer_texts = " ".join([
        turn.text.lower() for turn in transcription if turn.speaker == "customer"
    ])
    
    for intent, keywords in intent_keywords.items():
        if any(keyword in customer_texts for keyword in keywords):
            return intent
    
    return "General Inquiry"


# ==================== API ENDPOINTS ====================

@analytics_router.post("/calls", response_model=CallRecord)
async def create_call_record(request: CreateCallRecordRequest):
    """Create a new call record when a call starts"""
    call = CallRecord(
        call_sid=request.call_sid,
        call_type=request.call_type,
        status=CallStatus.INITIATED,
        sector=request.sector,
        from_number=request.from_number,
        to_number=request.to_number,
        start_time=datetime.now().isoformat(),
        language=request.language
    )
    
    call_records[call.call_id] = call
    save_call_logs()
    logger.info(f"📞 Created call record: {call.call_id} ({call.call_type.value})")
    
    return call


@analytics_router.patch("/calls/{call_id}", response_model=CallRecord)
async def update_call_record(call_id: str, request: UpdateCallRecordRequest):
    """Update an existing call record"""
    if call_id not in call_records:
        raise HTTPException(status_code=404, detail="Call record not found")
    
    call = call_records[call_id]
    
    if request.status:
        call.status = request.status
        
    if request.end_time:
        call.end_time = request.end_time
        # Calculate duration
        start = datetime.fromisoformat(call.start_time)
        end = datetime.fromisoformat(request.end_time)
        call.duration_seconds = int((end - start).total_seconds())
        
    if request.transcription_turn:
        # Analyze sentiment for the turn
        request.transcription_turn.sentiment = analyze_sentiment(request.transcription_turn.text)
        call.transcription.append(request.transcription_turn)
        
        # Update turn counts
        if request.transcription_turn.speaker == "agent":
            call.total_agent_turns += 1
        else:
            call.total_customer_turns += 1
        
    if request.outcome:
        call.outcome = request.outcome
        
    if request.notes:
        call.notes = request.notes
        
    if request.human_handoff_requested is not None:
        call.human_handoff_requested = request.human_handoff_requested
    
    call_records[call_id] = call
    save_call_logs()
    return call


@analytics_router.post("/calls/{call_id}/complete")
async def complete_call_record(call_id: str):
    """Mark a call as completed and perform final analysis"""
    if call_id not in call_records:
        raise HTTPException(status_code=404, detail="Call record not found")
    
    call = call_records[call_id]
    call.status = CallStatus.COMPLETED
    call.end_time = datetime.now().isoformat()
    
    # Calculate duration
    start = datetime.fromisoformat(call.start_time)
    end = datetime.fromisoformat(call.end_time)
    call.duration_seconds = int((end - start).total_seconds())
    
    # Analyze transcription
    if call.transcription:
        # Calculate overall sentiment
        sentiments = [turn.sentiment for turn in call.transcription if turn.sentiment]
        if sentiments:
            pos_count = sentiments.count(Sentiment.POSITIVE)
            neu_count = sentiments.count(Sentiment.NEUTRAL)
            neg_count = sentiments.count(Sentiment.NEGATIVE)
            total = len(sentiments)
            
            call.sentiment_breakdown = {
                "positive": round(pos_count / total * 100),
                "neutral": round(neu_count / total * 100),
                "negative": round(neg_count / total * 100)
            }
            
            if pos_count >= neg_count and pos_count >= neu_count:
                call.overall_sentiment = Sentiment.POSITIVE
            elif neg_count > pos_count and neg_count > neu_count:
                call.overall_sentiment = Sentiment.NEGATIVE
            else:
                call.overall_sentiment = Sentiment.NEUTRAL
        
        # Calculate average latency
        latencies = [turn.latency_ms for turn in call.transcription if turn.latency_ms]
        if latencies:
            call.avg_response_latency_ms = int(sum(latencies) / len(latencies))
        
        # Extract intent
        call.customer_intent = extract_intent(call.transcription)
        
        # Generate full transcript
        call.full_transcript = "\n".join([
            f"{turn.speaker.upper()}: {turn.text}" for turn in call.transcription
        ])
    
    # Determine outcome if not set
    if call.outcome == CallOutcome.UNKNOWN:
        if call.human_handoff_requested:
            call.outcome = CallOutcome.ESCALATED
        elif call.transcription and any("thank" in t.text.lower() for t in call.transcription):
            call.outcome = CallOutcome.RESOLVED
    
    call_records[call_id] = call
    save_call_logs()
    logger.info(f"✅ Completed call record: {call_id} (Duration: {call.duration_seconds}s)")
    
    return call


@analytics_router.get("/calls", response_model=List[CallRecord])
async def get_calls(
    call_type: Optional[CallType] = None,
    sector: Optional[str] = None,
    status: Optional[CallStatus] = None,
    sentiment: Optional[Sentiment] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get call records with optional filtering"""
    results = list(call_records.values())
    
    # Apply filters
    if call_type:
        results = [c for c in results if c.call_type == call_type]
    if sector:
        results = [c for c in results if c.sector == sector]
    if status:
        results = [c for c in results if c.status == status]
    if sentiment:
        results = [c for c in results if c.overall_sentiment == sentiment]
    if start_date:
        results = [c for c in results if c.start_time >= start_date]
    if end_date:
        results = [c for c in results if c.start_time <= end_date]
    
    # Sort by start time (newest first)
    results = sorted(results, key=lambda c: c.start_time, reverse=True)
    
    # Paginate
    return results[offset:offset + limit]


@analytics_router.get("/calls/{call_id}", response_model=CallRecord)
async def get_call(call_id: str):
    """Get a specific call record"""
    if call_id not in call_records:
        raise HTTPException(status_code=404, detail="Call record not found")
    return call_records[call_id]


@analytics_router.get("/summary", response_model=CallAnalyticsSummary)
async def get_analytics_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sector: Optional[str] = None
):
    """Get aggregated analytics summary"""
    calls = list(call_records.values())
    
    # Apply filters
    if sector:
        calls = [c for c in calls if c.sector == sector]
    if start_date:
        calls = [c for c in calls if c.start_time >= start_date]
    if end_date:
        calls = [c for c in calls if c.start_time <= end_date]
    
    total_calls = len(calls)
    
    if total_calls == 0:
        return CallAnalyticsSummary(
            total_calls=0,
            inbound_calls=0,
            outbound_calls=0,
            completed_calls=0,
            avg_duration_seconds=0,
            avg_sentiment_score=0,
            sentiment_distribution={},
            top_intents=[],
            calls_by_sector={},
            calls_by_hour={},
            resolution_rate=0,
            human_handoff_rate=0
        )
    
    # Calculate metrics
    inbound = len([c for c in calls if c.call_type == CallType.INBOUND])
    outbound = len([c for c in calls if c.call_type == CallType.OUTBOUND])
    completed = len([c for c in calls if c.status == CallStatus.COMPLETED])
    
    durations = [c.duration_seconds for c in calls if c.duration_seconds]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Sentiment distribution
    sentiment_dist = {
        "positive": len([c for c in calls if c.overall_sentiment == Sentiment.POSITIVE]),
        "neutral": len([c for c in calls if c.overall_sentiment == Sentiment.NEUTRAL]),
        "negative": len([c for c in calls if c.overall_sentiment == Sentiment.NEGATIVE])
    }
    
    # Sentiment score (1=negative, 2=neutral, 3=positive)
    scores = []
    for c in calls:
        if c.overall_sentiment == Sentiment.POSITIVE:
            scores.append(3)
        elif c.overall_sentiment == Sentiment.NEUTRAL:
            scores.append(2)
        elif c.overall_sentiment == Sentiment.NEGATIVE:
            scores.append(1)
    avg_sentiment = sum(scores) / len(scores) if scores else 2
    
    # Intent distribution
    intent_counts = defaultdict(int)
    for c in calls:
        if c.customer_intent:
            intent_counts[c.customer_intent] += 1
    top_intents = [
        {"intent": k, "count": v, "percentage": round(v/total_calls*100, 1)}
        for k, v in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Calls by sector
    sector_counts = defaultdict(int)
    for c in calls:
        sector_counts[c.sector] += 1
    
    # Calls by hour
    hour_counts = defaultdict(int)
    for c in calls:
        try:
            hour = datetime.fromisoformat(c.start_time).hour
            hour_counts[hour] += 1
        except:
            pass
    
    # Resolution rate
    resolved = len([c for c in calls if c.outcome == CallOutcome.RESOLVED])
    resolution_rate = round(resolved / total_calls * 100, 1) if total_calls > 0 else 0
    
    # Human handoff rate
    handoffs = len([c for c in calls if c.human_handoff_requested])
    handoff_rate = round(handoffs / total_calls * 100, 1) if total_calls > 0 else 0
    
    return CallAnalyticsSummary(
        total_calls=total_calls,
        inbound_calls=inbound,
        outbound_calls=outbound,
        completed_calls=completed,
        avg_duration_seconds=round(avg_duration, 1),
        avg_sentiment_score=round(avg_sentiment, 2),
        sentiment_distribution=sentiment_dist,
        top_intents=top_intents,
        calls_by_sector=dict(sector_counts),
        calls_by_hour=dict(hour_counts),
        resolution_rate=resolution_rate,
        human_handoff_rate=handoff_rate
    )


@analytics_router.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time metrics for dashboard"""
    calls = list(call_records.values())
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Today's calls
    today_calls = [c for c in calls if c.start_time >= today.isoformat()]
    
    # Active calls (in_progress status)
    active = [c for c in calls if c.status == CallStatus.IN_PROGRESS]
    
    # Hourly trend (last 24 hours)
    hourly_trend = []
    for i in range(24):
        hour_start = (now - timedelta(hours=24-i)).replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        hour_calls = len([
            c for c in calls 
            if c.start_time >= hour_start.isoformat() and c.start_time < hour_end.isoformat()
        ])
        hourly_trend.append({
            "hour": hour_start.strftime("%H:00"),
            "calls": hour_calls
        })
    
    return {
        "active_calls": len(active),
        "today_total": len(today_calls),
        "today_inbound": len([c for c in today_calls if c.call_type == CallType.INBOUND]),
        "today_outbound": len([c for c in today_calls if c.call_type == CallType.OUTBOUND]),
        "today_resolved": len([c for c in today_calls if c.outcome == CallOutcome.RESOLVED]),
        "today_escalated": len([c for c in today_calls if c.outcome == CallOutcome.ESCALATED]),
        "hourly_trend": hourly_trend,
        "last_updated": now.isoformat()
    }


@analytics_router.delete("/calls/{call_id}")
async def delete_call_record(call_id: str):
    """Delete a call record"""
    if call_id not in call_records:
        raise HTTPException(status_code=404, detail="Call record not found")
    
    del call_records[call_id]
    save_call_logs()
    return {"success": True, "message": f"Call record {call_id} deleted"}


@analytics_router.post("/sync-twilio")
async def sync_twilio_history_endpoint():
    """
    Sync call history from Twilio.
    This fetches historical calls and imports them into the dashboard.
    Requires Twilio to be configured.
    """
    from twilio_integration import twilio_config
    
    if not twilio_config.get("configured"):
        raise HTTPException(
            status_code=400, 
            detail="Twilio is not configured. Please configure Twilio credentials first."
        )
    
    client = twilio_config.get("client")
    phone_number = twilio_config.get("phone_number")
    
    try:
        synced_count = await sync_twilio_call_history(client, phone_number, limit=100)
        return {
            "success": True,
            "message": f"Successfully synced {synced_count} calls from Twilio",
            "synced_calls": synced_count,
            "total_calls": len(call_records)
        }
    except Exception as e:
        logger.error(f"Failed to sync Twilio history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync: {str(e)}")


@analytics_router.get("/status")
async def get_analytics_status():
    """Get analytics system status"""
    from twilio_integration import twilio_config
    
    return {
        "total_call_records": len(call_records),
        "twilio_configured": twilio_config.get("configured", False),
        "twilio_phone": twilio_config.get("phone_number") if twilio_config.get("configured") else None,
        "message": "Real-time call logging is active" if twilio_config.get("configured") else "Configure Twilio to enable live call logging"
    }

