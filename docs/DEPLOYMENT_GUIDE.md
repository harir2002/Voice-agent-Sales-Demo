# 🚀 Deployment Guide: Vercel + Render

This guide covers deploying the Voice Agent application with:
- **Frontend (React/Vite)** → Vercel
- **Backend (FastAPI)** → Render

---

## 📋 Prerequisites

1. GitHub repository: https://github.com/harir2002/Voice-agent-Sales-Demo
2. Accounts on:
   - [Vercel](https://vercel.com) (sign up with GitHub)
   - [Render](https://render.com) (sign up with GitHub)

---

## 🔵 Part 1: Deploy Backend to Render

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your **GitHub account** (harir2002)

### Step 2: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `harir2002/Voice-agent-Sales-Demo`
3. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `voice-agent-backend` |
| **Region** | Choose closest (Singapore for India) |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` (or paid for production) |

### Step 3: Set Environment Variables
In Render dashboard, go to **Environment** tab and add:

| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | Your Groq API key |
| `SARVAM_API_KEY` | Your Sarvam API key |
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number |
| `FRONTEND_URL` | (Will be added after Vercel deploy) |

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Note your backend URL: `https://voice-agent-backend.onrender.com`

---

## 🔷 Part 2: Deploy Frontend to Vercel

### Step 1: Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with your **GitHub account** (harir2002)

### Step 2: Import Project
1. Click **"Add New..."** → **"Project"**
2. Import from GitHub: `harir2002/Voice-agent-Sales-Demo`

### Step 3: Configure Project
| Setting | Value |
|---------|-------|
| **Project Name** | `voice-agent-frontend` |
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### Step 4: Set Environment Variable
Add this environment variable:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://voice-agent-backend.onrender.com` |

> ⚠️ Replace with your actual Render backend URL!

### Step 5: Deploy
1. Click **"Deploy"**
2. Wait for deployment (2-3 minutes)
3. Your frontend URL: `https://voice-agent-frontend.vercel.app`

---

## 🔗 Part 3: Connect Frontend & Backend

### Update Render Environment Variable
Go back to Render and add:

| Variable | Value |
|----------|-------|
| `FRONTEND_URL` | `https://voice-agent-frontend.vercel.app` |

This enables proper CORS for your frontend.

---

## 📞 Part 4: Configure Twilio Webhook

For inbound calls to work, update your Twilio webhook URL:

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to **Phone Numbers** → Your number
3. Under **Voice & Fax**, set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://voice-agent-backend.onrender.com/twilio/inbound/banking`
   - **HTTP Method**: POST

---

## ✅ Verification Checklist

- [ ] Backend health check: `https://your-backend.onrender.com/health`
- [ ] Frontend loads: `https://your-frontend.vercel.app`
- [ ] API connection works: Try the Voice Agent demo
- [ ] Twilio calls work: Make a test call

---

## 🔄 Auto-Deployment

Both platforms auto-deploy when you push to the `main` branch:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

- **Vercel**: Deploys in ~2-3 minutes
- **Render**: Deploys in ~5-10 minutes

---

## 💡 Tips

### Free Tier Limitations

| Platform | Limitation | Solution |
|----------|------------|----------|
| **Render** | Sleeps after 15 min inactive | First request takes ~30s to wake |
| **Vercel** | 100 deployments/day | More than enough for most projects |

### Upgrading for Production
- **Render**: $7/month for always-on server
- **Vercel**: Free tier is usually sufficient for frontend

---

## 🆘 Troubleshooting

### Backend not responding
1. Check Render logs in dashboard
2. Verify all environment variables are set
3. Check if service is sleeping (free tier)

### CORS errors
1. Ensure `FRONTEND_URL` is set correctly in Render
2. Check browser console for exact error

### Twilio calls not working
1. Verify webhook URL is correct
2. Check ngrok if testing locally
3. Review Twilio call logs in console

---

## 📁 Repository Structure

```
Voice-agent-Sales-Demo/
├── backend/           # → Deployed to Render
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # → Deployed to Vercel
│   ├── src/
│   ├── package.json
│   └── vercel.json
├── render.yaml        # Render configuration
└── README.md
```
