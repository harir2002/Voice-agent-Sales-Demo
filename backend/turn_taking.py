"""
Turn-Taking State Machine for Enterprise Voice Agent
=====================================================
Handles natural conversation flow, interruptions, and barge-in detection
"""

import time
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Callable

logger = logging.getLogger("voice_agent")


class TurnState(Enum):
    """States in the conversation turn-taking state machine"""
    IDLE = auto()               # Waiting for input
    USER_SPEAKING = auto()      # User is actively talking
    USER_PAUSING = auto()       # User paused briefly (may continue)
    PROCESSING = auto()         # Processing user input
    AGENT_SPEAKING = auto()     # Agent is playing audio
    AGENT_INTERRUPTED = auto()  # User interrupted agent
    HANDOFF_PENDING = auto()    # Escalating to human


@dataclass
class TurnContext:
    """Context for current turn state"""
    state: TurnState = TurnState.IDLE
    user_speech_start: Optional[float] = None
    agent_speech_start: Optional[float] = None
    last_voice_activity: float = field(default_factory=time.time)
    interruption_count: int = 0
    consecutive_silences: int = 0
    current_audio_buffer_size: int = 0
    total_user_speaking_time: float = 0
    total_agent_speaking_time: float = 0


class TurnTakingController:
    """
    Enterprise-grade turn-taking controller
    
    Features:
    - Adaptive VAD thresholds
    - Interruption handling with grace
    - Natural pause detection
    - Speaking time tracking
    """
    
    def __init__(self):
        self.context = TurnContext()
        
        # Configurable thresholds (tuned for Indian English)
        self.PAUSE_THRESHOLD_MS = 800       # Brief pause detection
        self.SILENCE_THRESHOLD_MS = 1500    # End of turn detection
        self.BARGE_IN_THRESHOLD_MS = 200    # Interruption sensitivity
        self.MIN_SPEECH_DURATION_MS = 300   # Minimum valid speech
        self.MAX_INTERRUPTIONS = 3          # Before asking to wait
        
        # Adaptive thresholds
        self.adaptive_silence_threshold = self.SILENCE_THRESHOLD_MS
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        
        logger.info("🎛️ TurnTakingController initialized")
    
    def _change_state(self, new_state: TurnState):
        """Change state and trigger callback"""
        old_state = self.context.state
        self.context.state = new_state
        
        if old_state != new_state:
            logger.info(f"🔄 Turn State: {old_state.name} → {new_state.name}")
            if self.on_state_change:
                self.on_state_change(old_state, new_state)
    
    def on_voice_detected(self, rms_energy: int, audio_chunk_size: int = 0) -> TurnState:
        """
        Called when voice activity is detected
        
        Args:
            rms_energy: RMS energy level of audio
            audio_chunk_size: Size of audio chunk received
            
        Returns:
            Current turn state
        """
        now = time.time()
        self.context.last_voice_activity = now
        self.context.consecutive_silences = 0
        self.context.current_audio_buffer_size += audio_chunk_size
        
        if self.context.state == TurnState.AGENT_SPEAKING:
            # User is interrupting the agent
            self._change_state(TurnState.AGENT_INTERRUPTED)
            self.context.interruption_count += 1
            
            # Track agent speaking time
            if self.context.agent_speech_start:
                self.context.total_agent_speaking_time += (now - self.context.agent_speech_start)
            
            logger.info(f"⚡ INTERRUPTION #{self.context.interruption_count} detected (RMS: {rms_energy})")
            return TurnState.AGENT_INTERRUPTED
            
        elif self.context.state in [TurnState.IDLE, TurnState.USER_PAUSING]:
            # User starting to speak or resuming after pause
            if self.context.state == TurnState.IDLE:
                self.context.user_speech_start = now
                self.context.current_audio_buffer_size = audio_chunk_size
            self._change_state(TurnState.USER_SPEAKING)
            
        elif self.context.state == TurnState.PROCESSING:
            # User speaking while we're processing - they're adding more input
            logger.debug("User adding input while processing")
            self._change_state(TurnState.USER_SPEAKING)
            
        return self.context.state
    
    def on_silence_detected(self, silence_duration_ms: int) -> TurnState:
        """
        Called when silence is detected
        
        Args:
            silence_duration_ms: Duration of silence in milliseconds
            
        Returns:
            Current turn state
        """
        self.context.consecutive_silences += 1
        
        if self.context.state == TurnState.USER_SPEAKING:
            # Check if user finished speaking
            if silence_duration_ms > self.adaptive_silence_threshold:
                # User finished speaking - time to process
                
                # Track speaking time
                if self.context.user_speech_start:
                    speaking_time = time.time() - self.context.user_speech_start
                    self.context.total_user_speaking_time += speaking_time
                    
                    # Adapt threshold based on user's speaking pattern
                    # If user speaks in short bursts, reduce threshold
                    if speaking_time < 2.0:
                        self.adaptive_silence_threshold = max(1000, self.SILENCE_THRESHOLD_MS - 200)
                    else:
                        self.adaptive_silence_threshold = self.SILENCE_THRESHOLD_MS
                
                self._change_state(TurnState.PROCESSING)
                logger.info(f"🎤 User finished speaking (silence: {silence_duration_ms}ms, buffer: {self.context.current_audio_buffer_size/1024:.1f}KB)")
                return TurnState.PROCESSING
                
            elif silence_duration_ms > self.PAUSE_THRESHOLD_MS:
                # User is pausing but may continue
                self._change_state(TurnState.USER_PAUSING)
                
        elif self.context.state == TurnState.AGENT_INTERRUPTED:
            # After interruption, wait for user to speak
            if silence_duration_ms > self.PAUSE_THRESHOLD_MS:
                # User interrupted but then went silent - they may be waiting
                self._change_state(TurnState.PROCESSING)
                
        return self.context.state
    
    def should_process_audio(self) -> bool:
        """Check if we should process accumulated audio"""
        return self.context.state == TurnState.PROCESSING
    
    def should_clear_audio_playback(self) -> bool:
        """Check if we should stop agent audio playback"""
        return self.context.state == TurnState.AGENT_INTERRUPTED
    
    def on_agent_start_speaking(self):
        """Called when agent starts TTS playback"""
        self._change_state(TurnState.AGENT_SPEAKING)
        self.context.agent_speech_start = time.time()
        logger.info("🔊 Agent started speaking")
    
    def on_agent_done_speaking(self):
        """Called when agent finishes TTS playback"""
        if self.context.agent_speech_start:
            self.context.total_agent_speaking_time += (time.time() - self.context.agent_speech_start)
        self._change_state(TurnState.IDLE)
        self.context.agent_speech_start = None
        logger.info("🔇 Agent finished speaking")
    
    def on_processing_complete(self):
        """Called when audio processing is complete (before TTS)"""
        # Reset audio buffer
        self.context.current_audio_buffer_size = 0
        self.context.user_speech_start = None
    
    def get_interruption_response(self) -> Optional[str]:
        """
        Get appropriate response after multiple interruptions
        
        Returns:
            Message to play, or None if should just process new input
        """
        if self.context.interruption_count >= self.MAX_INTERRUPTIONS:
            self.context.interruption_count = 0  # Reset counter
            return "I notice you have something important to say. Please go ahead, I'm listening carefully."
        return None
    
    def reset_for_new_call(self):
        """Reset state for a new call"""
        self.context = TurnContext()
        self.adaptive_silence_threshold = self.SILENCE_THRESHOLD_MS
        logger.info("🔄 TurnTakingController reset for new call")
    
    def get_stats(self) -> dict:
        """Get turn-taking statistics for the call"""
        return {
            "total_user_speaking_time_sec": round(self.context.total_user_speaking_time, 1),
            "total_agent_speaking_time_sec": round(self.context.total_agent_speaking_time, 1),
            "interruption_count": self.context.interruption_count,
            "current_state": self.context.state.name
        }
