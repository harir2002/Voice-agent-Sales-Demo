"""
Robust Speech-to-Text (STT) Module
Enhanced audio preprocessing and transcription for clear speech capture

Features:
- Audio preprocessing and normalization
- Multi-model fallback (whisper-large-v3 → whisper-large-v3-turbo)
- Sector-specific prompting for better domain accuracy
- Voice Activity Detection (VAD) for cleaner audio
- Retry strategies with different parameters
- Quality validation and filtering
"""

import io
import os
import wave
import struct
import time
import audioop
import logging
import tempfile
from typing import Optional, Tuple, List
from functools import lru_cache

# Setup logging
logger = logging.getLogger("voice_agent")

# ==================== AUDIO ENHANCEMENT CONSTANTS ====================

# Audio quality parameters
TARGET_SAMPLE_RATE = 16000  # Whisper optimal sample rate
MIN_AUDIO_DURATION_MS = 500  # Minimum audio duration for transcription
MAX_AUDIO_DURATION_MS = 30000  # Maximum optimal chunk (30 seconds)
SILENCE_THRESHOLD_RMS = 100  # RMS threshold for silence detection (lowered from 200)
VOICE_THRESHOLD_RMS = 150  # RMS threshold for voice detection (lowered from 400 for sensitivity)

# Domain-specific prompts for better transcription accuracy
SECTOR_PROMPTS = {
    "banking": "Banking, account, balance, loan, EMI, credit card, debit card, savings, FD, NEFT, RTGS, UPI, ATM, branch, interest rate, cheque, passbook, statement",
    "financial": "Investment, mutual fund, SIP, stock, portfolio, returns, NAV, equity, debt fund, tax saving, ELSS, NPS, PPF, demat, trading, cryptocurrency, fintech, UPI",
    "insurance": "Insurance, policy, premium, claim, coverage, health insurance, life insurance, term plan, endowment, cashless, hospitalization, nominee, sum assured, maturity",
    "bpo": "Support, ticket, complaint, issue, resolution, escalation, refund, order, delivery, tracking, cancellation, subscription, billing, payment",
    "healthcare_appt": "Appointment, doctor, consultation, OPD, schedule, reschedule, cancel, timing, availability, specialist, cardiologist, dermatologist, clinic",
    "healthcare_patient": "Patient, medical record, prescription, lab report, test result, medication, diagnosis, treatment, health history, vaccination, allergy"
}

# Common Hindi/Hinglish terms for better recognition
COMMON_INDIAN_TERMS = "kya, hai, mera, kaise, chahiye, kitna, karna, karun, batao, loan, account, balance, paisa, rupees, lakh, crore, aadhar, PAN"

# ==================== AUDIO PREPROCESSING ====================

def preprocess_audio(audio_bytes: bytes, source_sample_rate: int = 8000) -> Tuple[bytes, bool]:
    """
    Preprocess audio for optimal STT performance
    
    Steps:
    1. Resample to 16kHz (Whisper optimal)
    2. Normalize volume
    3. Apply simple noise reduction
    4. Convert to proper WAV format
    
    Returns: (processed_audio_bytes, success)
    """
    try:
        logger.info("🔧 Audio Preprocessing Started")
        
        # Read input WAV
        input_buffer = io.BytesIO(audio_bytes)
        
        try:
            with wave.open(input_buffer, 'rb') as wav_in:
                channels = wav_in.getnchannels()
                sample_width = wav_in.getsampwidth()
                framerate = wav_in.getframerate()
                raw_data = wav_in.readframes(wav_in.getnframes())
        except wave.Error:
            # If not a valid WAV, treat as raw PCM data
            logger.warning("Not a valid WAV file, treating as raw PCM")
            raw_data = audio_bytes
            channels = 1
            sample_width = 2
            framerate = source_sample_rate
        
        logger.info(f"   📊 Input: {channels}ch, {framerate}Hz, {sample_width*8}bit, {len(raw_data)/1024:.1f}KB")
        
        # Step 1: Convert to mono if stereo
        if channels == 2:
            raw_data = audioop.tomono(raw_data, sample_width, 0.5, 0.5)
            logger.info("   ✅ Converted to mono")
        
        # Step 2: Resample to 16kHz if needed
        if framerate != TARGET_SAMPLE_RATE:
            raw_data, _ = audioop.ratecv(raw_data, sample_width, 1, framerate, TARGET_SAMPLE_RATE, None)
            logger.info(f"   ✅ Resampled: {framerate}Hz → {TARGET_SAMPLE_RATE}Hz")
        
        # Step 3: Normalize volume (increase if too quiet)
        try:
            rms = audioop.rms(raw_data, sample_width)
            target_rms = 3000  # Target RMS for good audio level
            if rms > 0 and rms < target_rms:
                # Calculate gain factor, cap at 5x to avoid distortion
                gain = min(target_rms / rms, 5.0)
                # Apply gain
                raw_data = audioop.mul(raw_data, sample_width, gain)
                logger.info(f"   ✅ Volume normalized: RMS {rms} → {int(rms * gain)} (gain: {gain:.2f}x)")
            else:
                logger.info(f"   ℹ️ Volume OK: RMS = {rms}")
        except Exception as e:
            logger.warning(f"   ⚠️ Volume normalization skipped: {e}")
        
        # Step 4: Apply simple high-pass filter to remove low frequency noise
        # This helps remove background hum and DC offset
        try:
            raw_data = audioop.bias(raw_data, sample_width, 0)  # Remove DC bias
            logger.info("   ✅ DC bias removed")
        except Exception:
            pass
        
        # Step 5: Create output WAV
        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)  # 16-bit
            wav_out.setframerate(TARGET_SAMPLE_RATE)
            wav_out.writeframes(raw_data)
        
        processed_audio = output_buffer.getvalue()
        logger.info(f"   ✅ Output: 1ch, {TARGET_SAMPLE_RATE}Hz, 16bit, {len(processed_audio)/1024:.1f}KB")
        
        return processed_audio, True
        
    except Exception as e:
        logger.error(f"   ❌ Audio preprocessing failed: {e}")
        return audio_bytes, False


def detect_voice_activity(audio_bytes: bytes, chunk_size_ms: int = 100) -> Tuple[bytes, float]:
    """
    Detect voice activity and trim silence from audio
    
    Returns: (trimmed_audio, voice_ratio)
    - voice_ratio: 0.0 to 1.0 indicating how much of the audio contains voice
    """
    try:
        input_buffer = io.BytesIO(audio_bytes)
        
        with wave.open(input_buffer, 'rb') as wav_in:
            framerate = wav_in.getframerate()
            sample_width = wav_in.getsampwidth()
            raw_data = wav_in.readframes(wav_in.getnframes())
        
        # Calculate chunk size in samples
        chunk_samples = int(framerate * chunk_size_ms / 1000)
        chunk_bytes = chunk_samples * sample_width
        
        # Analyze chunks
        voice_chunks = []
        total_chunks = 0
        voice_chunk_count = 0
        
        # Find voice segments
        for i in range(0, len(raw_data), chunk_bytes):
            chunk = raw_data[i:i + chunk_bytes]
            if len(chunk) < chunk_bytes // 2:
                continue
                
            total_chunks += 1
            rms = audioop.rms(chunk, sample_width)
            
            if rms > VOICE_THRESHOLD_RMS:
                voice_chunks.append(chunk)
                voice_chunk_count += 1
            elif voice_chunks:
                # Include some silence after voice for natural ending
                voice_chunks.append(chunk)
        
        voice_ratio = voice_chunk_count / total_chunks if total_chunks > 0 else 0
        
        if not voice_chunks:
            logger.warning("   ⚠️ No voice activity detected")
            return audio_bytes, 0.0
        
        # Reconstruct trimmed audio
        trimmed_data = b''.join(voice_chunks)
        
        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(framerate)
            wav_out.writeframes(trimmed_data)
        
        trimmed_audio = output_buffer.getvalue()
        
        logger.info(f"   🎯 VAD: {voice_chunk_count}/{total_chunks} chunks contain voice ({voice_ratio*100:.1f}%)")
        logger.info(f"   📉 Audio trimmed: {len(audio_bytes)/1024:.1f}KB → {len(trimmed_audio)/1024:.1f}KB")
        
        return trimmed_audio, voice_ratio
        
    except Exception as e:
        logger.warning(f"   ⚠️ VAD failed: {e}")
        return audio_bytes, 0.5  # Assume 50% voice if VAD fails


def calculate_audio_quality_score(audio_bytes: bytes) -> Tuple[float, dict]:
    """
    Calculate audio quality score (0-100) with detailed metrics
    """
    metrics = {
        "duration_ms": 0,
        "avg_rms": 0,
        "max_rms": 0,
        "snr_estimate": 0,
        "dynamic_range": 0,
        "clipping_ratio": 0
    }
    
    try:
        input_buffer = io.BytesIO(audio_bytes)
        
        with wave.open(input_buffer, 'rb') as wav_in:
            framerate = wav_in.getframerate()
            sample_width = wav_in.getsampwidth()
            nframes = wav_in.getnframes()
            raw_data = wav_in.readframes(nframes)
        
        # Duration
        metrics["duration_ms"] = (nframes / framerate) * 1000
        
        # Analyze audio levels
        if len(raw_data) > 0:
            metrics["avg_rms"] = audioop.rms(raw_data, sample_width)
            metrics["max_rms"] = audioop.max(raw_data, sample_width)
            
            # Dynamic range (difference between max and avg)
            if metrics["avg_rms"] > 0:
                metrics["dynamic_range"] = metrics["max_rms"] / metrics["avg_rms"]
            
            # Estimate clipping (samples at max value)
            max_value = (2 ** (sample_width * 8 - 1)) - 1
            clip_threshold = max_value * 0.95
            
            # Count clipped samples
            clipped = 0
            for i in range(0, len(raw_data), sample_width):
                if sample_width == 2:
                    sample = abs(struct.unpack('<h', raw_data[i:i+2])[0]) if i+2 <= len(raw_data) else 0
                    if sample > clip_threshold:
                        clipped += 1
            
            total_samples = len(raw_data) // sample_width
            metrics["clipping_ratio"] = clipped / total_samples if total_samples > 0 else 0
        
        # Calculate overall score (0-100)
        score = 100
        
        # Duration penalty (too short or too long)
        if metrics["duration_ms"] < 500:
            score -= 30  # Too short
        elif metrics["duration_ms"] > 30000:
            score -= 10  # Too long
        
        # Volume penalty (too quiet or too loud)
        if metrics["avg_rms"] < 100:
            score -= 40  # Too quiet
        elif metrics["avg_rms"] < 500:
            score -= 20
        elif metrics["avg_rms"] > 10000:
            score -= 15  # Too loud
        
        # Clipping penalty
        if metrics["clipping_ratio"] > 0.1:
            score -= 30  # Severe clipping
        elif metrics["clipping_ratio"] > 0.01:
            score -= 15  # Moderate clipping
        
        score = max(0, min(100, score))
        
        return score, metrics
        
    except Exception as e:
        logger.warning(f"Audio quality check failed: {e}")
        return 50.0, metrics


# ==================== ROBUST TRANSCRIPTION ====================

def transcribe_with_retry(
    audio_bytes: bytes,
    groq_client,
    sector: str = "banking",
    max_retries: int = 3
) -> Tuple[Optional[str], Optional[str], dict]:
    """
    Robust transcription with preprocessing and retry strategies
    
    Returns: (transcription, error, metadata)
    """
    if not groq_client:
        return None, "Groq client not initialized", {}
    
    logger.info("=" * 60)
    logger.info("🎙️ ROBUST STT - Starting Advanced Transcription")
    logger.info("=" * 60)
    
    metadata = {
        "attempts": 0,
        "processing_time_ms": 0,
        "model_used": None,
        "audio_quality_score": 0,
        "preprocessed": False,
        "voice_ratio": 0
    }
    
    start_time = time.time()
    
    # Step 1: Audio Quality Assessment
    logger.info("📊 Step 1: Audio Quality Assessment")
    quality_score, quality_metrics = calculate_audio_quality_score(audio_bytes)
    metadata["audio_quality_score"] = quality_score
    logger.info(f"   📈 Quality Score: {quality_score:.0f}/100")
    logger.info(f"   📏 Duration: {quality_metrics['duration_ms']:.0f}ms")
    logger.info(f"   🔊 Avg RMS: {quality_metrics['avg_rms']}")
    
    if quality_score < 30:
        logger.warning("   ⚠️ Very poor audio quality detected")
    
    # Step 2: Audio Preprocessing
    logger.info("🔧 Step 2: Audio Preprocessing")
    processed_audio, preprocessed = preprocess_audio(audio_bytes)
    metadata["preprocessed"] = preprocessed
    
    # Step 3: Voice Activity Detection
    logger.info("🎯 Step 3: Voice Activity Detection")
    trimmed_audio, voice_ratio = detect_voice_activity(processed_audio)
    metadata["voice_ratio"] = voice_ratio
    
    if voice_ratio < 0.1:
        logger.warning("   ⚠️ Very little voice detected - using original audio to preserve speech")
    
    # IMPORTANT: Don't trim audio - use processed audio to preserve all speech
    # VAD trimming can cut off important speech segments
    final_audio = processed_audio  # Always use full processed audio
    
    # Step 4: Prepare sector-specific prompt
    sector_prompt = SECTOR_PROMPTS.get(sector, "") + ", " + COMMON_INDIAN_TERMS
    
    # Step 5: Try transcription with multiple strategies
    logger.info("🎤 Step 4: Transcription (Multi-Strategy)")
    
    # Define transcription strategies - simplified for better reliability
    strategies = [
        {
            "name": "Primary (Large-V3 + Prompt)",
            "model": "whisper-large-v3",
            "temperature": 0.0,
            "prompt": sector_prompt,
            "language": None  # Auto-detect
        },
        {
            "name": "Fallback 1 (No Prompt - Pure Recognition)",
            "model": "whisper-large-v3",
            "temperature": 0.0,
            "prompt": None,  # No prompt for pure recognition
            "language": None
        },
        {
            "name": "Fallback 2 (Large-V3 Turbo)",
            "model": "whisper-large-v3-turbo",
            "temperature": 0.0,
            "prompt": None,
            "language": None
        },
        {
            "name": "Fallback 3 (English Forced)",
            "model": "whisper-large-v3",
            "temperature": 0.0,
            "prompt": "English with Indian accent",
            "language": "en"  # Force English
        }
    ]
    
    temp_file = None
    transcription = None
    last_error = None
    
    try:
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.write(final_audio)
        temp_file.close()
        
        for strategy in strategies[:max_retries + 1]:
            metadata["attempts"] += 1
            logger.info(f"   🔄 Attempt {metadata['attempts']}: {strategy['name']}")
            
            try:
                with open(temp_file.name, "rb") as audio_file:
                    # Build transcription request
                    request_params = {
                        "file": (temp_file.name, audio_file.read()),
                        "model": strategy["model"],
                        "response_format": "text",
                        "temperature": strategy["temperature"]
                    }
                    
                    # Add optional parameters
                    if strategy["prompt"]:
                        request_params["prompt"] = strategy["prompt"]
                    if strategy["language"]:
                        request_params["language"] = strategy["language"]
                    
                    # Make API call
                    result = groq_client.audio.transcriptions.create(**request_params)
                
                # Validate result
                if result and len(result.strip()) > 0:
                    transcription = result.strip()
                    metadata["model_used"] = strategy["model"]
                    
                    # Quality validation
                    if is_valid_transcription(transcription):
                        logger.info(f"   ✅ Success with {strategy['name']}")
                        logger.info(f"   📝 Result: '{transcription[:80]}...'")
                        break
                    else:
                        logger.warning(f"   ⚠️ Transcription failed quality check, trying next strategy")
                        transcription = None
                        continue
                else:
                    logger.warning(f"   ⚠️ Empty result from {strategy['name']}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"   ❌ Strategy failed: {last_error[:100]}")
                time.sleep(0.5)  # Brief pause before retry
    
    finally:
        # Cleanup temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except:
                pass
    
    # Calculate processing time
    metadata["processing_time_ms"] = (time.time() - start_time) * 1000
    
    # Final logging
    logger.info("=" * 60)
    if transcription:
        logger.info(f"✅ ROBUST STT Complete - '{transcription[:60]}...'")
        logger.info(f"   ⏱️ Total Time: {metadata['processing_time_ms']:.0f}ms")
        logger.info(f"   🔄 Attempts: {metadata['attempts']}")
        logger.info(f"   📊 Quality Score: {metadata['audio_quality_score']:.0f}")
        return transcription, None, metadata
    else:
        logger.error("❌ ROBUST STT Failed - All strategies exhausted")
        return None, last_error or "Transcription failed after all retries", metadata


def is_valid_transcription(transcription: str) -> bool:
    """
    Validate if transcription appears to be valid speech
    More lenient validation to avoid rejecting valid speech
    """
    if not transcription:
        return False
    
    text = transcription.strip().lower()
    
    # Too short (single character)
    if len(text) < 2:
        return False
    
    # Known gibberish patterns from Whisper - only reject clear artifacts
    gibberish_patterns = [
        "[음악]",
        "[music]",
        "(music)",
        "[inaudible]",
        "[Musik]",
        "[Musique]",
        "thank you for watching",
        "thanks for watching",
        "subscribe to my channel",
        "please subscribe",
        "[silence]",
        "you"
    ]
    
    # Only reject if the entire text is just the pattern
    for pattern in gibberish_patterns:
        if text == pattern or text.strip() == pattern:
            logger.warning(f"   ⚠️ Gibberish detected: '{pattern}'")
            return False
    
    return True


def clean_transcription(transcription: str) -> str:
    """
    Clean and normalize transcription text
    """
    if not transcription:
        return ""
    
    text = transcription.strip()
    
    # Remove common Whisper artifacts
    artifacts = [
        "(upbeat music)",
        "(music)",
        "[Music]",
        "...",
        "♪",
        "♫"
    ]
    
    for artifact in artifacts:
        text = text.replace(artifact, "")
    
    # Remove multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    # Trim again
    text = text.strip()
    
    return text


# ==================== TWILIO-SPECIFIC HELPERS ====================

def convert_twilio_audio(mulaw_data: bytes, sample_rate: int = 8000) -> Tuple[bytes, bool]:
    """
    Convert Twilio's mulaw audio format to WAV suitable for Whisper
    Enhanced with better error handling and logging
    """
    try:
        if not mulaw_data or len(mulaw_data) < 100:
            return None, False
        
        # Convert mulaw to linear PCM
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Create WAV in memory
        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(sample_rate)
            wav_out.writeframes(pcm_data)
        
        wav_data = output_buffer.getvalue()
        
        logger.debug(f"   📞 Twilio audio converted: {len(mulaw_data)}B mulaw → {len(wav_data)}B WAV")
        
        return wav_data, True
        
    except Exception as e:
        logger.error(f"   ❌ Twilio audio conversion failed: {e}")
        return None, False


# ==================== MAIN ENTRY POINT ====================

def robust_transcribe_audio(
    audio_bytes: bytes,
    groq_client,
    sector: str = "banking",
    source_format: str = "wav"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Main entry point for robust audio transcription
    
    Args:
        audio_bytes: Audio data (WAV or mulaw format)
        groq_client: Initialized Groq client
        sector: Business sector for context prompting
        source_format: "wav" or "mulaw"
    
    Returns:
        (transcription_text, error_message)
    """
    # Handle mulaw (Twilio) format
    if source_format == "mulaw":
        wav_audio, success = convert_twilio_audio(audio_bytes)
        if not success:
            return None, "Failed to convert Twilio audio"
        audio_bytes = wav_audio
    
    # Perform robust transcription
    transcription, error, metadata = transcribe_with_retry(
        audio_bytes=audio_bytes,
        groq_client=groq_client,
        sector=sector,
        max_retries=3
    )
    
    # Clean transcription if successful
    if transcription:
        transcription = clean_transcription(transcription)
    
    return transcription, error


# ==================== UTILITY FUNCTIONS ====================

def get_supported_sectors() -> List[str]:
    """Get list of supported sectors for prompting"""
    return list(SECTOR_PROMPTS.keys())


def add_custom_sector_prompt(sector: str, prompt: str):
    """Add or update a sector-specific prompt"""
    SECTOR_PROMPTS[sector] = prompt
    logger.info(f"Added/updated sector prompt for: {sector}")
