"""
Twilio Integration for Voice Agent Demo
Handles Inbound and Outbound calls using Twilio Media Streams
"""

import os
import json
import base64
import asyncio
import logging
import struct
# audioop was removed in Python 3.13, use audioop-lts as fallback
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
import wave
import io
import time
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

# Import call analytics for live call logging
from call_analytics import (
    create_call_from_twilio,
    add_transcription_turn,
    complete_call_from_twilio,
    set_human_handoff,
    sync_twilio_call_history
)

# Import enterprise modules
from turn_taking import TurnTakingController, TurnState
from voice_naturalness import speech_enhancer, get_filler, FillerContext
from compliance import compliance_engine, mask_pii, sanitize_log, get_consent_script


logger = logging.getLogger("voice_agent")

# Router for Twilio endpoints
twilio_router = APIRouter(prefix="/twilio", tags=["Twilio Voice"])

# In-memory storage for Twilio credentials (pre-populate from env if available for production)
twilio_config: Dict[str, Any] = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
    "phone_number": os.getenv("TWILIO_PHONE_NUMBER"),
    "webhook_url": os.getenv("TWILIO_WEBHOOK_URL"),
    "configured": all([os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_PHONE_NUMBER")])
}

# Active call sessions
active_calls: Dict[str, Dict] = {}


# ==================== PYDANTIC MODELS ====================

class TwilioCredentials(BaseModel):
    account_sid: str
    auth_token: str
    phone_number: str
    webhook_url: Optional[str] = None  # ngrok or public URL


class OutboundCallRequest(BaseModel):
    to_number: str
    sector: str = "banking"
    greeting: Optional[str] = None
    call_purpose: Optional[str] = "general"  # Purpose: loan_reminder, payment_due, appointment_confirmation, policy_renewal, offer, follow_up, etc.
    customer_name: Optional[str] = "valued customer"  # For personalized calls


class TwilioConfigResponse(BaseModel):
    configured: bool
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None


# ==================== CONFIGURATION ENDPOINTS ====================

@twilio_router.post("/configure")
async def configure_twilio(credentials: TwilioCredentials):
    """Configure Twilio credentials from the UI"""
    global twilio_config
    
    try:
        # Validate credentials by creating a client and fetching account
        client = Client(credentials.account_sid, credentials.auth_token)
        account = client.api.accounts(credentials.account_sid).fetch()
        
        if account.status != "active":
            raise HTTPException(status_code=400, detail="Twilio account is not active")
        
        # Store credentials (strip whitespace from URLs)
        twilio_config = {
            "account_sid": credentials.account_sid.strip() if credentials.account_sid else None,
            "auth_token": credentials.auth_token.strip() if credentials.auth_token else None,
            "phone_number": credentials.phone_number.strip() if credentials.phone_number else None,
            "webhook_url": credentials.webhook_url.strip() if credentials.webhook_url else None,
            "configured": True,
            "client": client
        }
        
        logger.info(f"✅ Twilio configured successfully with number: {credentials.phone_number}")
        
        return {
            "success": True,
            "message": "Twilio configured successfully",
            "phone_number": credentials.phone_number,
            "account_name": account.friendly_name
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to configure Twilio: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Twilio credentials: {str(e)}")


@twilio_router.get("/config")
async def get_twilio_config():
    """Get current Twilio configuration status"""
    return TwilioConfigResponse(
        configured=twilio_config["configured"],
        phone_number=twilio_config.get("phone_number"),
        webhook_url=twilio_config.get("webhook_url")
    )


@twilio_router.get("/diagnostics")
async def get_twilio_diagnostics():
    """Full diagnostics for Twilio setup - use this to debug issues"""
    print("\n" + "=" * 60)
    print("📊 TWILIO DIAGNOSTICS REQUESTED")
    print("=" * 60)
    
    diagnostics = {
        "configured": twilio_config.get("configured", False),
        "phone_number": twilio_config.get("phone_number"),
        "webhook_url": twilio_config.get("webhook_url"),
        "has_client": twilio_config.get("client") is not None,
        "active_calls_count": len(active_calls),
        "active_calls": list(active_calls.keys()),
        "expected_inbound_webhook": f"{twilio_config.get('webhook_url', 'NOT_SET')}/twilio/voice/inbound/banking",
        "expected_outbound_webhook": f"{twilio_config.get('webhook_url', 'NOT_SET')}/twilio/voice/outbound/banking",
        "expected_websocket": f"{twilio_config.get('webhook_url', 'NOT_SET').replace('https://', 'wss://').replace('http://', 'ws://')}/twilio/media-stream/CALL_SID"
    }
    
    print(f"   Configured: {diagnostics['configured']}")
    print(f"   Phone: {diagnostics['phone_number']}")
    print(f"   Webhook URL: {diagnostics['webhook_url']}")
    print(f"   Active Calls: {diagnostics['active_calls_count']}")
    print(f"   Inbound Webhook: {diagnostics['expected_inbound_webhook']}")
    print(f"   Outbound Webhook: {diagnostics['expected_outbound_webhook']}")
    print(f"   WebSocket: {diagnostics['expected_websocket']}")
    print("=" * 60 + "\n")
    
    return diagnostics


@twilio_router.delete("/config")
async def clear_twilio_config():
    """Clear Twilio configuration"""
    global twilio_config
    twilio_config = {
        "account_sid": None,
        "auth_token": None,
        "phone_number": None,
        "webhook_url": None,
        "configured": False
    }
    return {"success": True, "message": "Twilio configuration cleared"}


class WebhookConfigRequest(BaseModel):
    sector: str = "banking"  # Default sector for inbound calls


@twilio_router.post("/configure-webhook")
async def configure_phone_webhook(config: WebhookConfigRequest):
    """
    Configure the Twilio phone number's webhook settings automatically.
    This sets up the Voice URL and Status Callback URL on the phone number.
    """
    if not twilio_config.get("configured"):
        raise HTTPException(status_code=400, detail="Twilio is not configured. Please add credentials first.")
    
    client = twilio_config.get("client")
    phone_number = twilio_config.get("phone_number")
    
    # Safely get webhook URL, handling None
    webhook_url = twilio_config.get("webhook_url")
    if webhook_url:
        webhook_url = webhook_url.strip().rstrip("/")
    else:
        webhook_url = ""
    
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL is required. Please set VITE_WEBHOOK_URL.")
    
    try:
        # Find the phone number SID
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not incoming_numbers:
            raise HTTPException(status_code=404, detail=f"Phone number {phone_number} not found in your Twilio account")
        
        phone_sid = incoming_numbers[0].sid
        
        # Build webhook URLs
        voice_url = f"{webhook_url}/twilio/voice/inbound/{config.sector}"
        status_callback = f"{webhook_url}/twilio/call/status"
        
        # Update the phone number with webhook URLs
        updated_number = client.incoming_phone_numbers(phone_sid).update(
            voice_url=voice_url,
            voice_method="POST",
            status_callback=status_callback,
            status_callback_method="POST"
        )
        
        logger.info(f"✅ Webhook configured for {phone_number}: {voice_url}")
        
        return {
            "success": True,
            "message": "Webhook configured successfully!",
            "phone_number": phone_number,
            "voice_url": voice_url,
            "status_callback": status_callback,
            "sector": config.sector
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to configure webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure webhook: {str(e)}")


# ==================== INBOUND CALL HANDLING ====================

@twilio_router.post("/voice/inbound")
async def handle_inbound_call(request: Request):
    """
    Webhook for incoming calls to your Twilio number.
    Returns TwiML to connect the call to a Media Stream.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    from_number = form_data.get("From", "unknown")
    to_number = form_data.get("To", "unknown")
    
    logger.info(f"📞 Inbound call: {from_number} → {to_number} (CallSid: {call_sid})")
    
    # Store call info
    active_calls[call_sid] = {
        "type": "inbound",
        "from": from_number,
        "to": to_number,
        "status": "connected",
        "sector": "banking"  # Default sector, can be customized
    }
    
    # Build TwiML response with Media Stream
    response = VoiceResponse()
    
    # Say a welcome message
    response.say(
        "Hello! Welcome to SBA Info Solutions AI Voice Agent. How can I help you today?",
        voice="Polly.Aditi",  # Indian English voice
        language="en-IN"
    )
    
    # Connect to WebSocket for real-time audio streaming
    webhook_url = twilio_config.get("webhook_url")
    if webhook_url:
        webhook_url = webhook_url.strip()
    else:
        webhook_url = ""
    if webhook_url:
        webhook_url = webhook_url.rstrip("/")
        # Convert HTTP URL to WebSocket URL
        ws_url = webhook_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/twilio/media-stream/{call_sid}"
        
        connect = Connect()
        stream = Stream(url=ws_url)
        stream.parameter(name="callSid", value=call_sid)
        connect.append(stream)
        response.append(connect)
    else:
        # Fallback: Simple response without streaming
        response.say(
            "I'm sorry, the voice agent is not fully configured. Please try again later.",
            voice="Polly.Aditi"
        )
        response.hangup()
    
    return Response(content=str(response), media_type="application/xml")


@twilio_router.post("/voice/inbound/{sector}")
async def handle_inbound_call_sector(sector: str, request: Request):
    """
    Sector-specific inbound call webhook.
    E.g., /twilio/voice/inbound/banking or /twilio/voice/inbound/insurance
    
    ENTERPRISE FEATURES:
    - Consent script for regulatory compliance
    - Sector-specific welcome messages
    - Analytics integration
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    from_number = form_data.get("From", "unknown")
    to_number = form_data.get("To", twilio_config.get("phone_number", "unknown"))
    
    # VISIBLE CONSOLE OUTPUT FOR DEBUGGING - with flush=True for immediate display
    import sys
    print("\n" + "=" * 60, flush=True)
    print(f"📞 INBOUND CALL RECEIVED!", flush=True)
    print(f"   Sector: {sector}", flush=True)
    print(f"   From: {from_number}", flush=True)
    print(f"   CallSid: {call_sid}", flush=True)
    print("=" * 60 + "\n", flush=True)
    sys.stdout.flush()
    
    logger.info(f"📞 Inbound call for {sector}: {from_number} (CallSid: {call_sid})")
    
    # ==================== ENTERPRISE: Get Consent Script ====================
    consent_script = get_consent_script(sector)
    compliance_engine.record_consent(call_sid, True)  # Implied consent for inbound
    
    # Sector-specific welcome messages
    welcome_messages = {
        "banking": "Hello! Welcome to Banking Services. I'm your AI assistant. How may I help you with your banking needs today?",
        "financial": "Good day! Welcome to Financial Services. I'm here to help with investments and wealth management. How can I assist you?",
        "insurance": "Hello! Welcome to Insurance Services. I'm your AI assistant for policy and claims support. How can I help?",
        "bpo": "Hello! Welcome to Customer Support. I'm your AI support agent. How may I assist you today?",
        "healthcare_appt": "Hello! Welcome to Healthcare Appointments. I can help you schedule or manage appointments. How can I assist?",
        "healthcare_patient": "Hello! Welcome to Patient Support. I'm here to help with your healthcare queries. How can I assist?"
    }
    
    active_calls[call_sid] = {
        "type": "inbound",
        "from": from_number,
        "to": to_number,
        "sector": sector,
        "status": "connected"
    }
    
    # 📊 Log to Call Analytics Dashboard
    try:
        call_record = create_call_from_twilio(
            call_sid=call_sid,
            call_type="inbound",
            from_number=from_number,
            to_number=to_number,
            sector=sector
        )
        # Log the AI welcome message
        welcome = welcome_messages.get(sector, "Hello! How can I help you today?")
        add_transcription_turn(call_sid, "agent", f"{consent_script} {welcome}")
        logger.info(f"📊 Call logged to analytics: {call_record.call_id}")
    except Exception as e:
        logger.error(f"Failed to log call to analytics: {e}")
    
    response = VoiceResponse()
    
    # Using Twilio's 'alice' voice - clearer and doesn't break on phone lines
    VOICE = "alice"
    LANG = "en-IN"
    
    # Play consent script first
    response.say(consent_script, voice=VOICE, language=LANG)
    response.pause(length=1)  # Brief pause after consent
    
    # Then play welcome message
    welcome = welcome_messages.get(sector, "Hello! How can I help you today?")
    response.say(welcome, voice=VOICE, language=LANG)
    
    # Add media stream connection
    webhook_url = twilio_config.get("webhook_url")
    if webhook_url:
        webhook_url = webhook_url.strip()
    else:
        webhook_url = ""
    if webhook_url:
        webhook_url = webhook_url.rstrip("/")
        ws_url = webhook_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/twilio/media-stream/{call_sid}?sector={sector}"
        
        connect = Connect()
        stream = Stream(url=ws_url)
        stream.parameter(name="callSid", value=call_sid)
        stream.parameter(name="sector", value=sector)
        connect.append(stream)
        response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


# ==================== OUTBOUND CALL HANDLING ====================

@twilio_router.post("/call/outbound")
async def initiate_outbound_call(call_request: OutboundCallRequest):
    """
    Initiate an outbound call to a customer.
    The AI agent will speak first when the call is answered.
    """
    if not twilio_config.get("configured"):
        raise HTTPException(status_code=400, detail="Twilio is not configured. Please add credentials first.")
    
    client = twilio_config.get("client")
    
    # Safely get webhook URL
    webhook_url = twilio_config.get("webhook_url")
    if webhook_url:
        webhook_url = webhook_url.strip()
    else:
        webhook_url = ""
        
    from_number = twilio_config.get("phone_number")
    
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL is required for outbound calls")
    
    try:
        # Build the URL for outbound call webhook with purpose parameters
        webhook_url = webhook_url.rstrip("/")
        # Include call_purpose and customer_name in URL for the webhook
        import urllib.parse
        purpose_encoded = urllib.parse.quote(call_request.call_purpose or "general")
        name_encoded = urllib.parse.quote(call_request.customer_name or "valued customer")
        outbound_webhook = f"{webhook_url}/twilio/voice/outbound/{call_request.sector}?purpose={purpose_encoded}&customer_name={name_encoded}"
        status_callback = f"{webhook_url}/twilio/call/status"
        
        # VISIBLE CONSOLE OUTPUT - with flush=True for immediate display
        import sys
        print("\n" + "=" * 60, flush=True)
        print(f"📤 INITIATING OUTBOUND CALL", flush=True)
        print(f"   To: {call_request.to_number}", flush=True)
        print(f"   Sector: {call_request.sector}", flush=True)
        print(f"   Purpose: {call_request.call_purpose}", flush=True)
        print(f"   Customer: {call_request.customer_name}", flush=True)
        print("=" * 60 + "\n", flush=True)
        sys.stdout.flush()
        
        # Initiate the call
        call = client.calls.create(
            to=call_request.to_number,
            from_=from_number,
            url=outbound_webhook,
            status_callback=status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST"
        )
        
        logger.info(f"📤 Outbound call initiated: {from_number} → {call_request.to_number} (CallSid: {call.sid}, Purpose: {call_request.call_purpose})")
        
        active_calls[call.sid] = {
            "type": "outbound",
            "to": call_request.to_number,
            "from": from_number,
            "sector": call_request.sector,
            "status": "initiated",
            "purpose": call_request.call_purpose,
            "customer_name": call_request.customer_name
        }
        
        # 📊 Log to Call Analytics Dashboard
        try:
            call_record = create_call_from_twilio(
                call_sid=call.sid,
                call_type="outbound",
                from_number=from_number,
                to_number=call_request.to_number,
                sector=call_request.sector
            )
            logger.info(f"📊 Outbound call logged to analytics: {call_record.call_id}")
        except Exception as e:
            logger.error(f"Failed to log outbound call to analytics: {e}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "to": call_request.to_number,
            "from": from_number,
            "status": "initiated"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initiate outbound call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@twilio_router.post("/voice/outbound/{sector}")
async def handle_outbound_call_answered(sector: str, request: Request, purpose: str = "general", customer_name: str = "valued customer"):
    """
    Webhook called when an outbound call is answered.
    AI agent speaks PROACTIVELY based on call purpose.
    
    PROACTIVE CALL TYPES:
    - loan_reminder: "Your EMI payment of ₹X is due on..."
    - appointment_confirmation: "Confirming your appointment with Dr..."
    - payment_due: "This is a reminder about your pending payment..."
    - policy_renewal: "Your insurance policy is expiring on..."
    - offer: "We have an exclusive offer for you..."
    - follow_up: "Following up on your recent inquiry..."
    - general: Generic greeting (like inbound)
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid", "unknown")
        call_status = form_data.get("CallStatus", "unknown")
        from_number = twilio_config.get("phone_number", "unknown")
        to_number = form_data.get("To", "unknown")
        
        # URL decode the customer name
        import urllib.parse
        customer_name = urllib.parse.unquote(customer_name)
        purpose = urllib.parse.unquote(purpose)
        
        # VISIBLE CONSOLE OUTPUT FOR DEBUGGING - with flush=True for immediate display
        import sys
        print("\n" + "=" * 60, flush=True)
        print(f"📤 OUTBOUND CALL ANSWERED!", flush=True)
        print(f"   Sector: {sector}", flush=True)
        print(f"   Purpose: {purpose}", flush=True)
        print(f"   Customer: {customer_name}", flush=True)
        print(f"   To: {to_number}", flush=True)
        print(f"   Status: {call_status}", flush=True)
        print(f"   CallSid: {call_sid}", flush=True)
        print("=" * 60 + "\n", flush=True)
        sys.stdout.flush()
        
        logger.info(f"📤 Outbound call answered ({sector}, purpose={purpose}): CallSid={call_sid}")
        
        # ==================== GET CONSENT SCRIPT ====================
        consent_script = get_consent_script(sector)
        compliance_engine.record_consent(call_sid, True)
        
        # ==================== PURPOSE-DRIVEN REMINDER SCRIPTS ====================
        # These are ONE-WAY REMINDER calls - deliver message and hang up!
        
        purpose_scripts = {
            # Banking Sector Purposes - Simple Reminders
            "loan_reminder": f"Hello {customer_name}! This is SBA Banking. This is a reminder that your loan EMI payment of Ten Thousand Five Hundred Rupees is due on the 5th of this month. Please ensure timely payment to avoid late fees. Thank you!",
            
            "payment_due": f"Hello {customer_name}! This is SBA Banking. Your payment of Eight Thousand Rupees is pending since January 10th. Kindly complete the payment at your earliest convenience. Thank you for banking with us!",
            
            "loan_offer": f"Hello {customer_name}! Congratulations from SBA Banking! Based on your excellent credit history, you're pre-approved for a personal loan of up to 5 lakh rupees at just 10.5 percent interest rate. Visit your nearest branch or log in to our app to avail this offer. Thank you!",
            
            "kyc_update": f"Hello {customer_name}! This is SBA Banking. Your KYC documents need to be updated as per RBI guidelines. Please visit your nearest branch with your Aadhaar and PAN card within 15 days. Thank you for your cooperation!",
            
            # Insurance Sector Purposes - Simple Reminders
            "policy_renewal": f"Hello {customer_name}! This is SBA Insurance. Your health insurance policy is expiring on January 31st. Please renew your policy to continue enjoying uninterrupted coverage. You can renew online or call our helpline. Thank you!",
            
            "claim_status": f"Hello {customer_name}! This is SBA Insurance with good news! Your claim has been approved and the amount will be credited to your bank account within 3 business days. Thank you for choosing SBA Insurance!",
            
            "premium_reminder": f"Hello {customer_name}! This is SBA Insurance. Your quarterly premium payment of Eight Thousand Rupees is due on January 25th. Please ensure timely payment to keep your policy active. Thank you!",
            
            # Healthcare Sector Purposes - Simple Reminders
            "appointment_confirmation": f"Hello {customer_name}! This is SBA Healthcare. This is to confirm your appointment with Dr. Rajesh Kumar tomorrow at 10 AM. Please arrive 15 minutes early for registration and carry your ID proof. Thank you!",
            
            "lab_report_ready": f"Hello {customer_name}! This is SBA Healthcare. Your lab reports are ready and have been uploaded to your patient portal. Please log in to view them or collect a printed copy from the reception. Thank you!",
            
            "vaccination_reminder": f"Hello {customer_name}! This is SBA Healthcare. According to our records, your flu vaccination is due this month. Please visit our clinic or book an appointment through our app. Stay healthy!",
            
            "checkup_reminder": f"Hello {customer_name}! This is SBA Healthcare. It's been 6 months since your last health checkup. We recommend scheduling a routine screening. Contact our reception to book your appointment. Thank you!",
            
            # Financial Services Purposes - Simple Reminders
            "investment_update": f"Hello {customer_name}! This is SBA Financial Services with great news! Your investments have grown by 12 percent this quarter. Log in to your portfolio to view the detailed performance report. Happy investing!",
            
            "sip_reminder": f"Hello {customer_name}! This is SBA Financial Services. Your SIP of Five Thousand Rupees is scheduled for tomorrow. Please ensure sufficient balance in your linked bank account. Thank you!",
            
            "tax_saving": f"Hello {customer_name}! This is SBA Financial Services. Reminder: You can save up to 46 thousand rupees in taxes by investing in ELSS funds before March 31st. Visit our website or app to invest now. Thank you!",
            
            # BPO/Support Purposes - Simple Reminders
            "follow_up": f"Hello {customer_name}! This is SBA Customer Support. We're following up on the support ticket you raised on January 15th. If your issue is not resolved, please call our helpline or reply to the email. Thank you!",
            
            "feedback": f"Hello {customer_name}! This is SBA. Thank you for using our services. We would love to hear your feedback. Please take a moment to rate us on our app or website. Your opinion matters to us!",
            
            "subscription_expiry": f"Hello {customer_name}! This is SBA. Your subscription is expiring in 3 days. Renew now to get a 20 percent discount! Visit our website or app to continue enjoying uninterrupted services. Thank you!",
            
            # General purpose (this one keeps conversation for flexibility)
            "general": f"Hello {customer_name}! This is an AI assistant from SBA. Thank you for your time. Have a great day!",
            "offer": f"Hello {customer_name}! This is SBA with an exclusive offer for you! Please check your email or SMS for details. Thank you and have a wonderful day!"
        }
        
        # Get the appropriate script
        proactive_script = purpose_scripts.get(purpose, purpose_scripts.get("general"))
        
        # Log what we're saying - with flush for immediate display
        logger.info(f"📢 Reminder Script ({purpose}): {proactive_script[:50]}...")
        print(f"📢 Reminder Script: {proactive_script[:80]}...", flush=True)
        
        # 📊 Log to Call Analytics Dashboard
        try:
            call_record = create_call_from_twilio(
                call_sid=call_sid,
                call_type="outbound",
                from_number=from_number,
                to_number=to_number,
                sector=sector
            )
            add_transcription_turn(call_sid, "agent", f"[REMINDER: {purpose}] {proactive_script}")
            logger.info(f"📊 Outbound call logged to analytics: {call_record.call_id}")
        except Exception as e:
            logger.error(f"Failed to log outbound call to analytics: {e}")
        
        response = VoiceResponse()
        
        # Using Twilio's 'alice' voice - clearer and doesn't break on phone lines
        # alice is a high-quality neural voice that works well with phone audio
        VOICE = "alice"
        LANG = "en-IN"
        
        # Step 1: Play consent script first (short)
        response.say(consent_script, voice=VOICE, language=LANG)
        response.pause(length=1)
        
        # Step 2: Play the reminder message
        response.say(proactive_script, voice=VOICE, language=LANG)
        
        # Step 3: Short pause and goodbye
        response.pause(length=1)
        response.say("Thank you for your time. Goodbye!", voice=VOICE, language=LANG)
        
        # Step 4: Hang up automatically - NO conversation
        response.hangup()
        
        print(f"📞 Call will auto-hangup after message (Reminder Mode)")
        logger.info(f"📞 Reminder call - auto hangup after message")
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ OUTBOUND WEBHOOK ERROR: {e}")
        logger.error(f"❌ Full traceback:\n{error_trace}")
        print(f"❌ OUTBOUND WEBHOOK ERROR: {e}")
        print(f"❌ Full traceback:\n{error_trace}")
        
        # Return a basic TwiML response with error message so call doesn't fail completely
        response = VoiceResponse()
        response.say("I apologize, but there was a technical issue. Please try again later.", voice="alice", language="en-IN")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


# ==================== CALL STATUS & MANAGEMENT ====================

@twilio_router.post("/call/status")
async def handle_call_status(request: Request):
    """Handle call status updates from Twilio"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    call_status = form_data.get("CallStatus", "unknown")
    duration = form_data.get("CallDuration")  # Duration in seconds when completed
    
    logger.info(f"   📊 Call status update: {call_sid} → {call_status}")
    import sys
    print(f"📊 CALL STATUS: {call_status} (CallSid: {call_sid})", flush=True)
    sys.stdout.flush()
    
    if call_sid in active_calls:
        active_calls[call_sid]["status"] = call_status
        
        if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
            # 📊 Complete call record in analytics
            try:
                call_record = complete_call_from_twilio(
                    call_sid=call_sid,
                    status=call_status,
                    duration=int(duration) if duration else None
                )
                if call_record:
                    logger.info(f"📊 Call completed in analytics: {call_record.call_id} (Duration: {call_record.duration_seconds}s)")
            except Exception as e:
                logger.error(f"Failed to complete call in analytics: {e}")
            
            # Clean up completed calls after a delay
            asyncio.create_task(cleanup_call(call_sid, delay=60))
    
    return {"status": "received"}


async def cleanup_call(call_sid: str, delay: int = 60):
    """Remove completed call from active calls after delay"""
    await asyncio.sleep(delay)
    if call_sid in active_calls:
        del active_calls[call_sid]
        logger.info(f"🧹 Cleaned up call: {call_sid}")


@twilio_router.get("/calls/active")
async def get_active_calls():
    """Get list of active calls"""
    return {
        "active_calls": len(active_calls),
        "calls": active_calls
    }


@twilio_router.post("/call/{call_sid}/hangup")
async def hangup_call(call_sid: str):
    """Hang up an active call"""
    if not twilio_config.get("configured"):
        raise HTTPException(status_code=400, detail="Twilio is not configured")
    
    try:
        client = twilio_config.get("client")
        call = client.calls(call_sid).update(status="completed")
        
        if call_sid in active_calls:
            active_calls[call_sid]["status"] = "completed"
        
        return {"success": True, "call_sid": call_sid, "status": "completed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to hangup call: {str(e)}")


# ==================== MEDIA STREAM WEBSOCKET ====================

# Helper function to convert mulaw to WAV
def mulaw_to_wav(mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
    """Convert mulaw audio to WAV format for STT processing"""
    try:
        # Convert mulaw to linear PCM (16-bit)
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    except Exception as e:
        logger.error(f"Error converting mulaw to WAV: {e}")
        return None


# Helper function to convert WAV/PCM audio to mulaw for Twilio
def wav_to_mulaw(audio_bytes: bytes) -> bytes:
    """
    Convert WAV or PCM audio to mulaw format for Twilio streaming
    
    QUALITY IMPROVEMENTS:
    - Better resampling for clearer audio
    - Volume normalization to boost clarity
    - Proper multi-step conversion
    """
    try:
        # Try to read as WAV file first
        wav_buffer = io.BytesIO(audio_bytes)
        try:
            with wave.open(wav_buffer, 'rb') as wav_file:
                params = wav_file.getparams()
                pcm_data = wav_file.readframes(params.nframes)
                sample_width = params.sampwidth
                sample_rate = params.framerate
                channels = params.nchannels
                
                logger.debug(f"📊 Audio: {sample_rate}Hz, {sample_width}B, {channels}ch, {len(pcm_data)}B")
                
                # Convert to mono if stereo
                if channels == 2:
                    pcm_data = audioop.tomono(pcm_data, sample_width, 0.5, 0.5)
                
                # Convert to 16-bit if not already
                if sample_width != 2:
                    pcm_data = audioop.lin2lin(pcm_data, sample_width, 2)
                    sample_width = 2
                
                # ==================== QUALITY IMPROVEMENT: Volume Normalization ====================
                # Normalize volume to improve clarity (boost quiet audio)
                try:
                    max_sample = audioop.max(pcm_data, 2)
                    if max_sample > 0 and max_sample < 20000:
                        # Audio is too quiet, boost it
                        # Target max is about 28000 (leaving headroom for peaks)
                        gain = min(28000 / max_sample, 3.0)  # Max 3x boost
                        if gain > 1.2:
                            pcm_data = audioop.mul(pcm_data, 2, gain)
                            logger.debug(f"📈 Volume boosted by {gain:.1f}x")
                except:
                    pass  # Skip normalization on error
                
                # ==================== QUALITY IMPROVEMENT: Multi-step Resampling ====================
                # Resample to 8000Hz if needed (Twilio requires 8kHz)
                if sample_rate != 8000:
                    # For better quality, use higher quality state
                    pcm_data, _ = audioop.ratecv(pcm_data, sample_width, 1, sample_rate, 8000, None, 3, 3)
                    logger.debug(f"🔄 Resampled from {sample_rate}Hz to 8000Hz")
                
                # Convert to mulaw
                mulaw_data = audioop.lin2ulaw(pcm_data, 2)
                
                logger.debug(f"✅ Mulaw conversion: {len(mulaw_data)} bytes")
                return mulaw_data
                
        except wave.Error:
            # If not a WAV file, treat as raw PCM
            logger.warning("Not a WAV file, treating as raw PCM")
            pcm_data = audio_bytes
            mulaw_data = audioop.lin2ulaw(pcm_data, 2)
            return mulaw_data
            
    except Exception as e:
        logger.error(f"Error converting to mulaw: {e}")
        return None


# Helper function to check for silence in audio (enhanced VAD)
def is_silence(audio_data: bytes, threshold: int = 150) -> bool:
    """
    Enhanced silence detection with lower threshold for better sensitivity to soft speech
    Uses threshold (150) to capture more speech including soft voices
    """
    try:
        if len(audio_data) < 2:
            return True
        # Convert mulaw to linear for analysis
        pcm_data = audioop.ulaw2lin(audio_data, 2)
        rms = audioop.rms(pcm_data, 2)
        
        # Log RMS values for debugging voice detection (lowered from 500)
        if rms > 300:
            logger.debug(f"   🔊 Voice detected: RMS={rms}")
        
        return rms < threshold
    except Exception:
        return True


def calculate_audio_energy(audio_data: bytes) -> int:
    """
    Calculate RMS energy of mulaw audio chunk
    Returns: RMS value (0-32768 range for 16-bit)
    """
    try:
        if len(audio_data) < 2:
            return 0
        pcm_data = audioop.ulaw2lin(audio_data, 2)
        return audioop.rms(pcm_data, 2)
    except Exception:
        return 0


@twilio_router.websocket("/media-stream/{call_sid}")
async def media_stream_websocket(websocket: WebSocket, call_sid: str, sector: str = "banking"):
    """
    WebSocket endpoint for Twilio Media Streams.
    Handles real-time audio streaming with STT → LLM → TTS pipeline.
    
    ENTERPRISE FEATURES:
    - Turn-taking state machine for natural conversation
    - Voice naturalness with contextual fillers
    - PII masking for compliance
    - Adaptive VAD thresholds
    """
    await websocket.accept()
    import sys
    print(f"🔌 WebSocket connected for call: {call_sid} (sector: {sector})", flush=True)
    sys.stdout.flush()
    logger.info(f"🔌 WebSocket connected for call: {call_sid} (sector: {sector})")
    
    # ==================== ENTERPRISE: Initialize Controllers ====================
    turn_controller = TurnTakingController()
    speech_enhancer.reset()
    
    stream_sid = None
    audio_buffer = bytearray()
    last_audio_time = time.time()
    is_processing = False
    conversation_history = []
    user_sentiment = "neutral"  # Track user sentiment for empathy
    
    # Enhanced audio capture settings for ROBUST speech recognition
    MIN_AUDIO_BUFFER = 8000   # Minimum 8KB for reliable transcription
    MAX_AUDIO_BUFFER = 80000  # Maximum 80KB to prevent memory issues
    websocket_active = True
    filler_index = 0
    
    # Import here to avoid circular imports
    from main import transcribe_audio, search_knowledge_base, text_to_speech, groq_client, get_precached_filler, FILLER_PHRASES
    from multi_agent import generate_multi_agent_response, get_sector_greeting

    
    async def clear_audio_playback():
        """Send clear event to Twilio to stop current audio playback immediately"""
        nonlocal stream_sid, websocket_active
        if not websocket_active or not stream_sid:
            return
        try:
            clear_message = {
                "event": "clear",
                "streamSid": stream_sid
            }
            await websocket.send_text(json.dumps(clear_message))
            logger.info("🛑 Cleared audio playback (user interrupted)")
            print("🛑 INTERRUPTION: Cleared audio playback")
        except Exception as e:
            logger.error(f"Failed to clear audio: {e}")
    
    async def send_audio_to_twilio(audio_bytes: bytes):
        """Send audio to Twilio with proper streaming - uses turn-taking state machine"""
        nonlocal websocket_active
        
        if not websocket_active or not stream_sid:
            return False
            
        try:
            # Mark agent as speaking using turn controller
            turn_controller.on_agent_start_speaking()
            
            mulaw_audio = wav_to_mulaw(audio_bytes)
            if not mulaw_audio:
                logger.error("Failed to convert audio to mulaw")
                turn_controller.on_agent_done_speaking()
                return False
            
            # Send audio in larger chunks for smoother playback
            # Twilio expects 8kHz mulaw - larger chunks = less choppy
            chunk_size = 1600  # 200ms chunks for smooth, continuous audio
            
            for i in range(0, len(mulaw_audio), chunk_size):
                # Check for interruption using turn-taking state machine
                if turn_controller.should_clear_audio_playback() or not websocket_active:
                    logger.info("⚡ Audio sending stopped due to interruption")
                    turn_controller.on_agent_done_speaking()
                    return False
                    
                chunk = mulaw_audio[i:i + chunk_size]
                audio_payload = base64.b64encode(chunk).decode('utf-8')
                
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": audio_payload
                    }
                }
                
                try:
                    await websocket.send_text(json.dumps(media_message))
                except Exception as e:
                    logger.error(f"Failed to send audio chunk: {e}")
                    websocket_active = False
                    turn_controller.on_agent_done_speaking()
                    return False
            
            # Send mark to indicate end of this audio segment
            mark_message = {
                "event": "mark",
                "streamSid": stream_sid,
                "mark": {"name": f"audio_{int(time.time() * 1000)}"}
            }
            await websocket.send_text(json.dumps(mark_message))
            
            turn_controller.on_agent_done_speaking()
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            websocket_active = False
            turn_controller.on_agent_done_speaking()
            return False
    
    async def send_filler(context: str = "searching"):
        """
        Send a contextual filler phrase while processing
        Uses enterprise voice naturalness module for human-like responses
        """
        nonlocal filler_index, user_sentiment
        
        if not websocket_active:
            return
            
        try:
            # Get contextual filler using enterprise module
            filler_text, pause_before, pause_after = get_filler(
                context=context,
                sentiment=user_sentiment,
                sector=sector
            )
            
            # Try pre-cached filler first (instant - 0ms latency)
            filler_audio = get_precached_filler(filler_index)
            filler_index += 1
            
            if filler_audio:
                logger.info(f"🎯 Sending PRE-CACHED filler (instant)")
                await send_audio_to_twilio(filler_audio)
            else:
                # Generate contextual filler audio
                logger.info(f"🎯 Generating contextual filler: '{filler_text}'")
                filler_audio, error = await text_to_speech(filler_text, sector)
                if filler_audio and not error:
                    await send_audio_to_twilio(filler_audio)
                    
        except Exception as e:
            logger.error(f"Filler error: {e}")
    
    async def process_audio_and_respond():
        """
        Process buffered audio and send response back to Twilio
        
        ENTERPRISE FEATURES:
        - Turn-taking state machine integration
        - PII masking for compliance
        - Sentiment-aware responses
        - Natural speech enhancement
        """
        nonlocal audio_buffer, is_processing, conversation_history, websocket_active, user_sentiment
        
        # Check if we should process audio using turn-taking controller
        if is_processing or len(audio_buffer) < MIN_AUDIO_BUFFER or not websocket_active:
            return
        
        # Mark turn controller that we're processing
        turn_controller.on_processing_complete()
        
        is_processing = True
        process_start = time.time()
        
        try:
            # Copy buffer and clear for new audio
            audio_to_process = bytes(audio_buffer)
            audio_buffer.clear()
            
            logger.info("=" * 70)
            logger.info("🎙️ TWILIO CALL PROCESSING PIPELINE STARTED")
            logger.info("=" * 70)
            logger.info(f"📞 Call SID: {call_sid}")
            logger.info(f"📂 Sector: {sector}")
            
            # Step 1: Convert mulaw to WAV
            logger.info("-" * 40)
            logger.info("🔄 STEP 1: Audio Conversion (mulaw → WAV)")
            logger.info(f"   📊 Input audio: {len(audio_to_process)} bytes ({len(audio_to_process)/1000:.1f}KB)")
            wav_audio = mulaw_to_wav(audio_to_process)
            if not wav_audio:
                logger.error("   ❌ Failed to convert audio to WAV")
                return
            logger.info(f"   ✅ WAV audio: {len(wav_audio)} bytes ({len(wav_audio)/1000:.1f}KB)")
            
            # Step 2: Transcribe audio using ROBUST STT
            logger.info("-" * 40)
            logger.info("🎤 STEP 2: ROBUST Speech-to-Text (Groq Whisper + Preprocessing)")
            stt_start = time.time()
            
            # Use enhanced transcription with sector-specific prompting
            transcription, trans_error = transcribe_audio(wav_audio, sector)
            stt_time = (time.time() - stt_start) * 1000
            
            if trans_error or not transcription:
                logger.warning(f"   ❌ Transcription failed: {trans_error}")
                # Ask user to repeat instead of silently failing
                retry_msg = "I'm having trouble hearing you. Could you please speak a bit louder and clearer?"
                tts_audio, _ = await text_to_speech(retry_msg, sector)
                if tts_audio:
                    await send_audio_to_twilio(tts_audio)
                return
            
            # Skip empty or very short transcriptions
            if len(transcription.strip()) < 2:
                logger.info("   ⏭️ Skipping empty transcription")
                return
            
            logger.info(f"   ⏱️ STT Time: {stt_time:.0f}ms")
            logger.info(f"   📝 Transcription: '{transcription}'")
            # VISIBLE CONSOLE LOG
            print(f"👤 USER: {transcription}", flush=True)
            sys.stdout.flush()
            
            # Quality check: SIMPLIFIED - only reject truly empty/gibberish transcriptions
            logger.info("-" * 40)
            logger.info("🔍 STEP 3: Transcription Quality Check")
            words = transcription.strip().split()
            
            # Only reject if it's a known Whisper artifact (not user speech)
            whisper_artifacts = ['[music]', '[silence]', '[inaudible]', 'thank you for watching', 'please subscribe']
            is_artifact = any(artifact in transcription.lower() for artifact in whisper_artifacts)
            
            logger.info(f"   📊 Word count: {len(words)}")
            logger.info(f"   🔎 Artifact check: {'FAILED' if is_artifact else 'PASSED'}")
            
            # Only ask to repeat if it's a Whisper artifact, NOT for short valid speech
            if is_artifact:
                logger.warning(f"   ⚠️ Detected Whisper artifact - asking to repeat")
                clarify_msg = "I'm sorry, could you please repeat that more clearly?"
                tts_audio, _ = await text_to_speech(clarify_msg, sector)
                if tts_audio:
                    await send_audio_to_twilio(tts_audio)
                return
            
            logger.info(f"   ✅ Quality check PASSED")
            
            # Detect user's language from transcription for proper response matching
            import re
            has_hindi_script = len(re.findall(r'[\u0900-\u097F]', transcription)) > 0
            hinglish_words = ['kya', 'hai', 'mera', 'kaise', 'chahiye', 'kitna', 'karna', 'hoga', 'karun', 'batao']
            has_hinglish = any(word in transcription.lower() for word in hinglish_words)
            user_language = "hi" if (has_hindi_script or has_hinglish) else "en"
            logger.info(f"   🌐 Detected user language: {user_language}")
            
            # ==================== ENTERPRISE: PII Masking for Compliance ====================
            # Mask PII in transcription for secure logging
            masked_transcription = sanitize_log(call_sid, "customer", transcription)
            logger.info(f"   🛡️ PII Check: {'Masked' if masked_transcription != transcription else 'Clean'}")
            
            # ==================== ENTERPRISE: Sentiment Detection ====================
            # Detect sentiment for empathetic responses
            negative_indicators = ['problem', 'issue', 'frustrated', 'angry', 'upset', 'not working', 'disappointed']
            positive_indicators = ['thank', 'great', 'excellent', 'happy', 'good']
            
            trans_lower = transcription.lower()
            if any(word in trans_lower for word in negative_indicators):
                user_sentiment = "negative"
            elif any(word in trans_lower for word in positive_indicators):
                user_sentiment = "positive"
            else:
                user_sentiment = "neutral"
            logger.info(f"   😊 User Sentiment: {user_sentiment}")
            
            # Log customer speech (PII masked for analytics)
            add_transcription_turn(call_sid, "customer", masked_transcription)
            conversation_history.append({"type": "user", "text": transcription})
            
            # 🎯 SEND CONTEXTUAL FILLER based on sentiment
            # Empathetic filler for negative sentiment, searching filler otherwise
            logger.info("-" * 40)
            logger.info("🎯 STEP 3.5: Playing Contextual Filler (while processing)")
            filler_start = time.time()
            filler_context = "empathizing" if user_sentiment == "negative" else "searching"
            await send_filler(context=filler_context)
            filler_time = (time.time() - filler_start) * 1000
            logger.info(f"   ⏱️ Filler Time: {filler_time:.0f}ms")
            
            # Step 4: Search knowledge base (RAG)
            logger.info("-" * 40)
            logger.info("📚 STEP 4: Knowledge Base Search (RAG)")
            rag_start = time.time()
            context_docs = search_knowledge_base(transcription, sector)
            rag_time = (time.time() - rag_start) * 1000
            logger.info(f"   ⏱️ RAG Time: {rag_time:.0f}ms")
            logger.info(f"   📄 Documents found: {len(context_docs)}")
            
            # Step 5: Generate AI response using Multi-Agent system
            logger.info("-" * 40)
            logger.info("🤖 STEP 5: Multi-Agent Response Generation")
            llm_start = time.time()
            response_text, needs_handoff, handoff_reason = generate_multi_agent_response(
                transcription, 
                context_docs, 
                sector,
                conversation_history,
                user_language,
                groq_client
            )
            llm_time = (time.time() - llm_start) * 1000
            logger.info(f"   ⏱️ LLM Time: {llm_time:.0f}ms")
            # VISIBLE CONSOLE LOG
            print(f"🤖 AGENT: {response_text}", flush=True)
            sys.stdout.flush()
            
            # ==================== ENTERPRISE: Response Validation & Enhancement ====================
            # Validate response for compliance
            validation = compliance_engine.validate_response(response_text, sector)
            if not validation["valid"]:
                logger.warning(f"   ⚠️ Response compliance issues: {validation['issues']}")
            
            # Enhance response with natural speech patterns
            enhanced_response = speech_enhancer.enhance_response(
                response_text,
                sentiment=user_sentiment,
                add_acknowledgement=(len(conversation_history) <= 2)  # Acknowledge first messages
            )
            logger.info(f"   💬 Response: '{enhanced_response}'")
            
            # Log agent response (use enhanced version)
            add_transcription_turn(call_sid, "agent", enhanced_response)
            
            if needs_handoff:
                set_human_handoff(call_sid, handoff_reason)
                logger.info(f"   🚨 HUMAN HANDOFF TRIGGERED: {handoff_reason}")
            
            conversation_history.append({"type": "ai", "text": enhanced_response})
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            # Step 6: Generate TTS audio (use enhanced response)
            logger.info("-" * 40)
            logger.info("🔊 STEP 6: Text-to-Speech (Sarvam AI)")
            tts_start = time.time()
            tts_audio, tts_error = await text_to_speech(enhanced_response, sector)
            tts_time = (time.time() - tts_start) * 1000
            
            if tts_error or not tts_audio:
                logger.error(f"   ❌ TTS failed ({tts_time:.0f}ms): {tts_error}")
                return
            
            logger.info(f"   ⏱️ TTS Time: {tts_time:.0f}ms")
            logger.info(f"   📤 Audio size: {len(tts_audio)} bytes ({len(tts_audio)/1000:.1f}KB)")
            
            # Check for interruption before sending response using turn controller
            if turn_controller.should_clear_audio_playback():
                logger.info("⚡ Skipping audio send - user interrupted")
                return
            
            # Step 7: Send audio to Twilio
            logger.info("-" * 40)
            logger.info("📡 STEP 7: Streaming Audio to Twilio")
            send_start = time.time()
            success = await send_audio_to_twilio(tts_audio)
            send_time = (time.time() - send_start) * 1000
            
            if turn_controller.context.state == TurnState.AGENT_INTERRUPTED:
                logger.info("⚡ Audio was interrupted during playback")
            else:
                logger.info(f"   ⏱️ Stream Time: {send_time:.0f}ms")
                logger.info(f"   ✅ Audio sent: {'SUCCESS' if success else 'FAILED'}")
            
            # Final summary with turn-taking stats
            total_time = (time.time() - process_start) * 1000
            turn_stats = turn_controller.get_stats()
            logger.info("=" * 70)
            logger.info("✅ PIPELINE COMPLETE - Summary")
            logger.info(f"   📞 Call: {call_sid}")
            logger.info(f"   ⏱️ Total Time: {total_time:.0f}ms")
            logger.info(f"   📊 Breakdown: STT={stt_time:.0f}ms | RAG={rag_time:.0f}ms | LLM={llm_time:.0f}ms | TTS={tts_time:.0f}ms | Stream={send_time:.0f}ms")
            logger.info(f"   🎛️ Turn Stats: {turn_stats}")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            import traceback
            traceback.print_exc()
        finally:
            is_processing = False
    
    try:
        async for message in websocket.iter_text():
            if not websocket_active:
                break
                
            data = json.loads(message)
            event_type = data.get("event")
            
            if event_type == "connected":
                logger.info(f"📡 Media stream connected: {call_sid}")
                turn_controller.reset_for_new_call()
                
            elif event_type == "start":
                stream_sid = data.get("streamSid")
                start_data = data.get("start", {})
                logger.info(f"🎬 Media stream started: {stream_sid}")
                custom_params = start_data.get("customParameters", {})
                if custom_params:
                    logger.info(f"Custom parameters: {custom_params}")
                
            elif event_type == "media":
                payload = data.get("media", {}).get("payload", "")
                if payload:
                    audio_chunk = base64.b64decode(payload)
                    
                    # Calculate RMS energy for turn-taking
                    try:
                        pcm_data = audioop.ulaw2lin(audio_chunk, 2)
                        rms_energy = audioop.rms(pcm_data, 2)
                    except:
                        rms_energy = 0
                    
                    if not is_silence(audio_chunk):
                        # Voice detected - update turn controller and buffer
                        turn_controller.on_voice_detected(rms_energy, len(audio_chunk))
                        audio_buffer.extend(audio_chunk)
                        last_audio_time = time.time()
                        
                        # Handle interruption if agent is speaking
                        if turn_controller.context.state == TurnState.AGENT_SPEAKING:
                            logger.info("⚡ INTERRUPTION DETECTED!")
                            print("⚡ INTERRUPTION DETECTED!")
                            await clear_audio_playback()
                            is_processing = False
                            
                    else:
                        # Silence detected - check if we should process
                        silence_duration = time.time() - last_audio_time
                        silence_duration_ms = int(silence_duration * 1000)
                        
                        # Update turn controller
                        turn_controller.on_silence_detected(silence_duration_ms)
                        
                        # Use simple time-based fallback for reliable processing
                        # Process if: enough buffer + enough silence + not already processing
                        SILENCE_THRESHOLD_SECONDS = 1.5  # 1.5 seconds of silence
                        
                        if (len(audio_buffer) > MIN_AUDIO_BUFFER and 
                            silence_duration > SILENCE_THRESHOLD_SECONDS and 
                            not is_processing):
                            logger.info(f"   🎙️ Audio ready: {len(audio_buffer)/1024:.1f}KB after {silence_duration:.2f}s silence")
                            asyncio.create_task(process_audio_and_respond())
                            
            elif event_type == "mark":
                mark_name = data.get("mark", {}).get("name", "")
                logger.debug(f"📍 Mark received: {mark_name}")
                
            elif event_type == "stop":
                logger.info(f"🛑 Media stream stopped: {call_sid}")
                websocket_active = False
                
                # Log final turn-taking stats
                final_stats = turn_controller.get_stats()
                logger.info(f"📊 Final Turn Stats: {final_stats}")
                
                # Cleanup compliance records
                compliance_engine.cleanup_call(call_sid)
                
                # Process any remaining audio
                if len(audio_buffer) > MIN_AUDIO_BUFFER // 2 and not is_processing:
                    logger.info(f"   🛑 Processing final audio: {len(audio_buffer)/1024:.1f}KB")
                    await process_audio_and_respond()
                break
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {call_sid}")
        websocket_active = False
    except Exception as e:
        logger.error(f"❌ WebSocket error for {call_sid}: {e}")
        import traceback
        traceback.print_exc()
        websocket_active = False
    finally:
        websocket_active = False
        compliance_engine.cleanup_call(call_sid)
        if call_sid in active_calls:
            active_calls[call_sid]["status"] = "disconnected"


# ==================== HELPER FUNCTIONS ====================

def get_twilio_client():
    """Get the configured Twilio client"""
    if not twilio_config.get("configured"):
        return None
    return twilio_config.get("client")


def is_twilio_configured():
    """Check if Twilio is configured"""
    return twilio_config.get("configured", False)
