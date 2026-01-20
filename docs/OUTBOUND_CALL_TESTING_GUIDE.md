# 📞 Outbound Call Testing Guide

## Complete Step-by-Step Flow for Testing Outbound Calls

---

## 🚀 Prerequisites

Before testing outbound calls, ensure:

1. ✅ **Backend is running**: `python main.py` in the `backend` folder
2. ✅ **Frontend is running**: `npm run dev` in the `frontend` folder  
3. ✅ **ngrok is running**: Expose your backend (port 8000) to the internet
4. ✅ **Twilio credentials configured** in the app

---

## 📋 Step-by-Step Testing Flow

### **Step 1: Start ngrok Tunnel**

Open a new terminal and run:
```powershell
ngrok http 8000
```

Copy the **HTTPS forwarding URL** (e.g., `https://abc123.ngrok.io`)

---

### **Step 2: Access the Frontend**

Open your browser and go to:
```
http://localhost:5173
```

---

### **Step 3: Navigate to Twilio Demo Page**

1. Click on **"Twilio Demo"** or **"Call Dashboard"** from the navigation
2. You should see the Twilio configuration panel

---

### **Step 4: Configure Twilio Credentials**

Fill in the following fields:
- **Account SID**: Your Twilio Account SID (from Twilio Console)
- **Auth Token**: Your Twilio Auth Token
- **Phone Number**: Your Twilio phone number (e.g., `+17174448044`)
- **Webhook URL**: Your ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)

Click **"Save Configuration"**

---

### **Step 5: Configure Phone Webhooks**

After saving credentials:
1. Click **"Configure Webhooks"** button
2. Select the sector you want to test (e.g., Banking)
3. This automatically sets up Twilio webhooks

---

### **Step 6: Initiate an Outbound Call**

1. Look for the **"Make Outbound Call"** section
2. Enter the **destination phone number** (your mobile number with country code)
   - Format: `+919876543210` (India) or `+1234567890` (US)
3. Select the **sector** (Banking, Insurance, etc.)
4. Click **"Call"** or **"Initiate Call"** button

---

### **Step 7: Answer the Call on Your Phone**

1. Your phone will ring from the Twilio number
2. **Answer the call**
3. The AI agent will greet you with a sector-specific welcome message

---

### **Step 8: Test the Conversation**

Once connected, test with these questions:

#### For **Banking** Sector:
**English:**
- "What is the interest rate for personal loan?"
- "How do I check my account balance?"
- "How do I block my lost debit card?"

**Hinglish:**
- "Personal loan ka interest rate kya hai?"
- "Mera account balance kaise check karun?"
- "Mera ATM card kho gaya, kaise block karun?"

#### For **Insurance** Sector:
**English:**
- "How do I file a claim?"
- "What does my health insurance cover?"

**Hinglish:**
- "Claim kaise file karun?"
- "Meri policy mein kya cover hota hai?"

---

## 🔧 API Testing with cURL

You can also test outbound calls directly via API:

### **1. Configure Twilio**
```bash
curl -X POST http://localhost:8000/twilio/config \
  -H "Content-Type: application/json" \
  -d '{
    "account_sid": "YOUR_ACCOUNT_SID",
    "auth_token": "YOUR_AUTH_TOKEN",
    "phone_number": "+17174448044",
    "webhook_url": "https://your-ngrok-url.ngrok.io"
  }'
```

### **2. Initiate Outbound Call**
```bash
curl -X POST http://localhost:8000/twilio/call/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+919876543210",
    "sector": "banking",
    "greeting": "Hello! This is your banking assistant."
  }'
```

### **3. Check Active Calls**
```bash
curl http://localhost:8000/twilio/calls/active
```

### **4. Hang Up a Call**
```bash
curl -X POST http://localhost:8000/twilio/call/hangup/CALL_SID_HERE
```

---

## 📊 Monitoring the Call

### **Check Backend Logs**
Watch the terminal where `python main.py` is running. You should see:
```
📤 Outbound call initiated: +17174448044 → +919876543210
📞 Call answered, starting AI conversation
🎤 Customer said: "What is the interest rate?"
🤖 AI response: "Personal loan interest rates..."
🔊 TTS audio generated successfully
```

### **Check Call Analytics Dashboard**
- Go to **Call Dashboard** in the frontend
- See real-time call logs and transcripts

---

## 🎙️ Voice Quality Tips

If voice is **breaking or unclear**, check:

1. **Sample Rate**: Should be 8kHz (already fixed in code)
2. **Speaker**: Using `manisha` (clear professional voice)
3. **Network**: Ensure stable internet connection
4. **ngrok**: Use paid ngrok for better stability

---

## 🔄 Complete Call Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUTBOUND CALL FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Make Outbound Call" in Frontend                │
│             ↓                                                   │
│  2. Frontend sends POST to /twilio/call/outbound                │
│             ↓                                                   │
│  3. Backend uses Twilio API to initiate call                    │
│             ↓                                                   │
│  4. Twilio calls the destination number                         │
│             ↓                                                   │
│  5. When answered, Twilio makes webhook request to:             │
│     /twilio/voice/outbound/{sector}                             │
│             ↓                                                   │
│  6. Backend returns TwiML with Media Stream connection          │
│             ↓                                                   │
│  7. WebSocket connection established for real-time audio        │
│             ↓                                                   │
│  8. AI greets customer with sector-specific welcome             │
│             ↓                                                   │
│  9. Customer speaks → STT → AI Response → TTS → Customer hears  │
│             ↓                                                   │
│  10. Loop continues until call ends                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❌ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Twilio not configured" | Enter and save Twilio credentials |
| "Webhook URL required" | Enter your ngrok HTTPS URL |
| Call drops immediately | Check ngrok is running and URL is correct |
| No AI response | Check backend logs for errors |
| Voice is breaking | Restart backend after TTS sample rate fix |
| "Speaker not compatible" | Use only: anushka, abhilash, manisha, vidya, arya, karun, hitesh |

---

## 📱 Sectors Available for Testing

| Sector | ID | Best For Testing |
|--------|-----|------------------|
| Banking | `banking` | Loans, accounts, cards |
| Financial Services | `financial` | Investments, SIP, UPI |
| Insurance | `insurance` | Claims, policies |
| BPO/KPO | `bpo` | Support tickets |
| Healthcare (Appointments) | `healthcare_appt` | Doctor appointments |
| Healthcare (Records) | `healthcare_patient` | Lab reports, prescriptions |

---

## ✅ Checklist Before Testing

- [ ] Backend running (`python main.py`)
- [ ] Frontend running (`npm run dev`)
- [ ] ngrok running and URL copied
- [ ] Twilio credentials configured
- [ ] Webhooks configured
- [ ] Test phone number ready

---

*Happy Testing! 🎉*
