"""
Sarvam AI TTS using REST API (simpler, proven to work)
Still much faster than ElevenLabs!
"""

import requests
import logging
from typing import Optional, Tuple
import hashlib

logger = logging.getLogger("voice_agent")

# Sarvam TTS REST endpoint
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# In-memory cache for TTS audio
tts_cache = {}

# Voice/Speaker mapping - bulbul:v2 compatible speakers ONLY
# Valid speakers for bulbul:v2: anushka, abhilash, manisha, vidya, arya, karun, hitesh
# anushka has the clearest pronunciation for English
SECTOR_VOICE_MAPPING = {
    "banking": "anushka",
    "financial": "anushka",
    "insurance": "anushka",
    "bpo": "anushka",
    "healthcare_appt": "anushka",
    "healthcare_patient": "anushka"
}

def get_cache_key(text: str) -> str:
    """Generate cache key from text"""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def detect_language(text: str) -> str:
    """
    Detect the language of text and return Sarvam language code.
    Supports: Hindi (hi-IN), English (en-IN)
    """
    import re
    import string
    
    # Count characters in different scripts
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))  # Devanagari
    english_chars = len(re.findall(r'[a-zA-Z]', text))  # Latin
    
    total = hindi_chars + english_chars
    
    if total == 0:
        return "en-IN"  # Default to English if no characters detected
    
    # Calculate percentages
    hindi_pct = hindi_chars / total if total > 0 else 0
    english_pct = english_chars / total if total > 0 else 0
    
    # If text has Devanagari script characters, use Hindi
    if hindi_pct > 0.2 or hindi_chars > 3:
        logger.info("🌐 Detected: Hindi (Devanagari script)")
        return "hi-IN"
    
    # Check for Hinglish (Hindi words written in English) - comprehensive list
    hinglish_words = [
        # Common Hindi words in Romanized form
        'kya', 'hai', 'hain', 'kaise', 'mera', 'meri', 'mere', 'aap', 'hum', 'yeh', 'woh', 
        'kyun', 'kab', 'kahan', 'kitna', 'kitni', 'kaun', 'achha', 'accha',
        'theek', 'thik', 'nahi', 'nahin', 'haan', 'han', 'aur', 'lekin', 'agar', 'toh', 'mein',
        'chahiye', 'chaiye', 'karna', 'karni', 'karo', 'karte', 'karenge', 'bataiye', 'dijiye',
        'paisa', 'paise', 'rupiya', 'rupaye', 'lena', 'dena', 'milega', 'milegi',
        'abhi', 'aaj', 'kal', 'parso', 'sahi', 'galat', 'bura',
        'samjha', 'samjhe', 'pata', 'batao', 'bataye', 'boliye', 'bolo',
        'aapka', 'aapki', 'humara', 'humari', 'unka', 'unki', 'iska', 'iski',
        'zaroor', 'zaruri', 'madad', 'seva', 'suvidha', 'jankari', 'dhanyavaad', 'shukriya'
    ]
    text_lower = text.lower()
    # Clean words - remove punctuation from word boundaries for accurate matching
    words_in_text = [word.strip(string.punctuation) for word in text_lower.split()]
    # EXACT word matching only - no substring matching to avoid false positives
    hinglish_count = sum(1 for word in words_in_text if word in hinglish_words)
    
    # Log detection for debugging
    logger.info(f"🌐 Language Detection: Hindi chars={hindi_chars}, English chars={english_chars}, Hinglish words={hinglish_count}")
    
    # Decision logic - need at least 2 regional words to classify as Hinglish
    # This prevents false positives on pure English text
    if hinglish_count >= 2:
        logger.info("🌐 Detected: Hinglish (Hindi TTS)")
        return "hi-IN"
    elif hinglish_count == 1:
        # Single word might be coincidence - check if rest is mostly English
        if english_pct > 0.8:
            logger.info("🌐 Detected: English (single Hindi word ignored)")
            return "en-IN"
        else:
            logger.info("🌐 Detected: Hinglish (single word)")
            return "hi-IN"
    else:
        logger.info("🌐 Detected: English")
        return "en-IN"  # Default to Indian English




async def text_to_speech_stream(
    text: str,
    api_key: str,
    speaker: str = "anushka",
    language_code: str = "en-IN",  # Default to English
    sector: str = "banking",
    pace: float = 1.0
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Convert text to speech using Sarvam AI REST API
    Still faster than ElevenLabs with better latency!
    """
    # Check cache first
    cache_key = get_cache_key(text)
    if cache_key in tts_cache:
        logger.info("✅ TTS cache hit!")
        return tts_cache[cache_key], None
    
    logger.info(f"🔊 Sarvam TTS REST: '{text[:30]}...'")
    
    if not text or len(text.strip()) == 0:
        return None, "No text provided"
    
    # Preprocess text for better pronunciation
    text = preprocess_text(text)
    
    # Sarvam API character limits - allow longer responses
    detected_lang_for_limit = detect_language(text)
    if detected_lang_for_limit == "hi-IN":
        char_limit = 400  # Hindi - 3-4 lines
        logger.info(f"🌐 Hindi - 400 char limit")
    else:
        char_limit = 490  # English - 3-4 lines
    
    if len(text) > char_limit:
        logger.warning(f"Text too long ({len(text)} chars), truncating to {char_limit} chars")
        truncated = text[:char_limit]
        
        # Find last sentence ending - include Tamil/Hindi punctuation
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        last_hindi_danda = truncated.rfind('।')  # Hindi/Sanskrit sentence ending
        last_tamil_period = truncated.rfind('॥')  # Double danda
        # Tamil doesn't use danda, so also check for Tamil-specific endings
        last_tamil_uyir = truncated.rfind('.')  # Tamil mostly uses period
        
        cut_index = max(last_period, last_question, last_exclamation, last_hindi_danda, last_tamil_period)
        
        if cut_index > 50:  # Lowered threshold for better sentence detection
            text = text[:cut_index+1]
            logger.info(f"Cut at sentence ending (index {cut_index})")
        else:
            # Try to find a comma or natural break
            last_comma = truncated.rfind(',')
            last_space = truncated.rfind(' ')
            break_index = max(last_comma, last_space)
            
            if break_index > 50:
                text = truncated[:break_index]
                logger.info(f"Cut at natural break (index {break_index})")
            else:
                # Hard cut as last resort
                text = truncated
            
        logger.info(f"Truncated text length: {len(text)} chars")

    # Use sector-specific voice
    speaker = SECTOR_VOICE_MAPPING.get(sector, speaker)

    # 🌐 AUTO-DETECT LANGUAGE from text content
    detected_language = detect_language(text)
    if detected_language != language_code:
        logger.info(f"🌐 Language detected: {detected_language} (original: {language_code})")
        language_code = detected_language
    
    try:
        headers = {
            "Api-Subscription-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Log the exact text being sent for debugging
        logger.info(f"📝 TTS Text ({len(text)} chars): '{text}'")
        
        # Use v2 model (stable)
        model = "bulbul:v2"
        
        # Use pace from parameter (default 1.0 for natural speech)
        
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": speaker,
            "model": model,
            "enable_preprocessing": True,
            "speech_sample_rate": 8000,  # 8kHz to match Twilio's native format (reduces conversion artifacts)
            "pace": 1.0  # Natural pace for clearer speech
        }
        
        logger.info(f"Calling Sarvam TTS: model={model}, speaker={speaker}, lang={language_code}, pace={pace}, text_len={len(text)}")
        
        response = requests.post(
            SARVAM_TTS_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Get audio from response
            if "audios" in data and len(data["audios"]) > 0:
                import base64
                audio_base64 = data["audios"][0]
                audio_bytes = base64.b64decode(audio_base64)
                
                logger.info(f"✅ TTS Success: {len(audio_bytes)} bytes")
                
                # Cache the result
                tts_cache[cache_key] = audio_bytes
                
                return audio_bytes, None
            else:
                return None, "No audio in response"
        else:
            error_msg = response.text[:200]
            logger.error(f"❌ Sarvam API error {response.status_code}: {error_msg}")
            return None, f"TTS API error: {error_msg}"
            
    except requests.Timeout:
        logger.error("❌ Request timeout")
        return None, "TTS timeout"
    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        return None, str(e)[:200]


def text_to_speech_sync(
    text: str,
    api_key: str,
    speaker: str = "anushka",
    language_code: str = "en-IN",  # Default to English
    sector: str = "banking"
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Synchronous version (since REST API is already sync)
    """
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        text_to_speech_stream(text, api_key, speaker, language_code, sector)
    )
    loop.close()
    return result


# Pre-cached filler audio storage (key -> audio_bytes)
FILLER_PHRASES_CACHE = {}

# Filler phrases for masking latency during calls - keep them SHORT for speed
FILLER_PHRASES = [
    "One moment please...",
    "Let me check...",
    "Just a second...",
    "Looking into that...",
    "Checking that for you...",
]

# Pre-cache common phrases
COMMON_PHRASES = {
    "greeting": "Hello! How can I help you today?",
    "thinking": "Let me check that for you.",
    "thanks": "You're welcome!",
    "goodbye": "Thank you for using our service!",
    "repeat": "I'm sorry, could you please repeat that more clearly?",
    # Add fillers to common phrases
    "filler_1": "One moment please...",
    "filler_2": "Let me check...",
    "filler_3": "Just a second...",
    "filler_4": "Looking into that...",
    "filler_5": "Checking that for you...",
}

def get_precached_filler(index: int = 0) -> bytes:
    """Get a pre-cached filler phrase audio. Returns None if not cached."""
    filler_key = f"filler_{(index % 5) + 1}"
    cache_key = get_cache_key(COMMON_PHRASES.get(filler_key, "One moment please..."))
    return tts_cache.get(cache_key)

async def precache_common_phrases(api_key: str):
    """Pre-cache common phrases including fillers for instant playback"""
    logger.info("🔄 Pre-caching TTS phrases (including fillers)...")
    cached_count = 0
    for key, text in COMMON_PHRASES.items():
        try:
            audio, error = await text_to_speech_stream(text, api_key, "anushka", "en-IN", "banking")
            if audio and not error:
                logger.info(f"  ✅ Cached: {key} ({len(audio)} bytes)")
                cached_count += 1
            else:
                logger.warning(f"  ⚠️ Failed: {key} - {error}")
        except Exception as e:
            logger.warning(f"  ⚠️ Failed: {key} - {e}")
    logger.info(f"✅ Pre-cached {cached_count}/{len(COMMON_PHRASES)} phrases")


def clear_cache():
    """Clear cache"""
    global tts_cache
    count = len(tts_cache)
    tts_cache = {}
    logger.info(f"🗑️ Cleared {count} entries")
    return count


def get_cache_stats():
    """Get cache stats"""
    return {
        "cached_items": len(tts_cache),
        "total_size_bytes": sum(len(v) for v in tts_cache.values()),
        "total_size_mb": round(sum(len(v) for v in tts_cache.values()) / (1024 * 1024), 2)
    }

def preprocess_text(text: str) -> str:
    """Clean and normalize text for TTS"""
    import re
    
    # Replace abbreviations with regex for safety (word boundaries)
    replacements = [
        (r'\bp\.a\.', 'per annum'),
        (r'\bp\.a\b', 'per annum'),
        (r'%', ' percent'),
        (r'\bapprox\.', 'approximately'),
        (r'\bno\.', 'number'),
        (r'\bvs\.', 'versus'),
        (r'\betc\.', 'et cetera'),
        (r'\be\.g\.', 'for example'),
        (r'\bi\.e\.', 'that is'),
        (r'\bRs\.?', 'rupees'),
        (r'₹', 'rupees '),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Remove/replace symbols that TTS reads literally
    # Arrows and mathematical operators
    text = text.replace("→", " ")  # Right arrow
    text = text.replace("←", " ")  # Left arrow
    text = text.replace("↓", " ")  # Down arrow
    text = text.replace("↑", " ")  # Up arrow
    text = text.replace("➜", " ")  # Another arrow
    text = text.replace("▶", " ")  # Play button
    text = text.replace("►", " ")  # Another play
    text = text.replace(">", " ")   # Greater than - remove silently
    text = text.replace("<", " ")   # Less than - remove silently  
    text = text.replace(">>", " ")  # Double arrow
    text = text.replace("<<", " ")  # Double arrow
    text = text.replace(">=", " or more ")   # Greater than or equal
    text = text.replace("<=", " or less ")   # Less than or equal
    text = text.replace("=>", " then ")      # Arrow style
    text = text.replace("->", " to ")        # Arrow style
    
    # Remove markdown formatting that might confuse TTS
    text = text.replace("*", "")
    text = text.replace("#", "")
    text = text.replace("- ", ", ")  # Replace list bullets with commas for better flow
    text = text.replace("_", " ")    # Underscores
    text = text.replace("`", "")     # Backticks
    text = text.replace("\"", "")    # Quotes that might confuse
    
    # Remove emojis and special unicode characters that TTS can't handle
    text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
    text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # Misc symbols
    text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport
    text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # Flags
    text = re.sub(r'[\U00002702-\U000027B0]', '', text)  # Dingbats
    text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # Supplemental
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    return text
