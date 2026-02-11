---
title: BFSI Voice Agent Backend
emoji: 🏦
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# BFSI Voice Agent Backend

This is the backend for the Voice Agent Demo, built with FastAPI and Python.

It handles:
- **Speech-to-Text (STT)**: Transcribes user audio.
- **LLM Processing**: Generates AI responses using Groq (Llama 3).
- **Text-to-Speech (TTS)**: Converts AI text to speech using Sarvam.
- **RAG (Retrieval-Augmented Generation)**: Uses ChromaDB to provide relevant context.
- **Twilio Integration**: Handles phone calls.

## Deployment Notes
- This Space uses Docker.
- Environment variables (API keys) must be set in the Space settings.
