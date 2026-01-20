"""
Voice Naturalness Module for Enterprise Voice Agent
====================================================
Implements human-like speech behaviors including fillers, pauses, and acknowledgements
"""

import random
import time
import logging
from typing import Optional, Tuple, Dict, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("voice_agent")


class FillerContext(Enum):
    """Context for when to use different types of fillers"""
    THINKING = "thinking"           # Processing a complex query
    SEARCHING = "searching"         # Looking up information (RAG)
    ACKNOWLEDGING = "acknowledging" # Confirming user input
    TRANSITIONING = "transitioning" # Moving to new topic
    EMPATHIZING = "empathizing"     # Responding to negative sentiment
    CLARIFYING = "clarifying"       # Asking for clarification


@dataclass
class FillerPhrase:
    """A filler phrase with timing information"""
    text: str
    pause_before_ms: int = 0
    pause_after_ms: int = 200
    sentiment_appropriate: List[str] = None  # None = all sentiments
    
    def __post_init__(self):
        if self.sentiment_appropriate is None:
            self.sentiment_appropriate = ["positive", "neutral", "negative"]


# Context-aware filler phrases library
FILLER_LIBRARY: Dict[FillerContext, List[FillerPhrase]] = {
    FillerContext.THINKING: [
        FillerPhrase("Let me think about that...", pause_before_ms=100, pause_after_ms=400),
        FillerPhrase("Hmm, let me see...", pause_before_ms=0, pause_after_ms=300),
        FillerPhrase("Okay, so...", pause_before_ms=0, pause_after_ms=200),
        FillerPhrase("Right, let me check...", pause_before_ms=0, pause_after_ms=300),
    ],
    FillerContext.SEARCHING: [
        FillerPhrase("Let me quickly look that up for you...", pause_after_ms=200),
        FillerPhrase("One moment while I check...", pause_after_ms=250),
        FillerPhrase("Just pulling up the details...", pause_after_ms=200),
        FillerPhrase("Let me find that information...", pause_after_ms=250),
    ],
    FillerContext.ACKNOWLEDGING: [
        FillerPhrase("I see...", pause_after_ms=150),
        FillerPhrase("Okay...", pause_after_ms=100),
        FillerPhrase("Right...", pause_after_ms=100),
        FillerPhrase("Got it...", pause_after_ms=150),
        FillerPhrase("Understood...", pause_after_ms=150),
    ],
    FillerContext.TRANSITIONING: [
        FillerPhrase("So...", pause_after_ms=150),
        FillerPhrase("Now...", pause_after_ms=100),
        FillerPhrase("Alright, so...", pause_after_ms=200),
        FillerPhrase("Moving on...", pause_after_ms=150),
    ],
    FillerContext.EMPATHIZING: [
        FillerPhrase("I understand your concern...", pause_after_ms=300, 
                     sentiment_appropriate=["negative"]),
        FillerPhrase("I'm sorry to hear that...", pause_after_ms=300,
                     sentiment_appropriate=["negative"]),
        FillerPhrase("I can see why that would be frustrating...", pause_after_ms=300,
                     sentiment_appropriate=["negative"]),
        FillerPhrase("Let me help you with that right away...", pause_after_ms=200,
                     sentiment_appropriate=["negative"]),
    ],
    FillerContext.CLARIFYING: [
        FillerPhrase("Just to make sure I understood correctly...", pause_after_ms=200),
        FillerPhrase("Let me confirm...", pause_after_ms=150),
        FillerPhrase("So you're asking about...", pause_after_ms=200),
    ]
}

# Sector-specific acknowledgements
SECTOR_ACKNOWLEDGEMENTS = {
    "banking": [
        "I can help you with that banking query...",
        "Let me check your account details...",
    ],
    "financial": [
        "Let me look at your investment options...",
        "I can help with that financial query...",
    ],
    "insurance": [
        "Let me check your policy details...",
        "I can help with that insurance query...",
    ],
    "healthcare_appt": [
        "Let me check the available appointments...",
        "I can help you schedule that...",
    ],
    "healthcare_patient": [
        "Let me pull up your records...",
        "I can help with your healthcare query...",
    ],
    "bpo": [
        "Let me look into that for you...",
        "I can help resolve this issue...",
    ]
}


class NaturalSpeechEnhancer:
    """
    Enhances AI responses with natural speech patterns
    
    Features:
    - Context-aware filler selection
    - Sentiment-appropriate responses
    - Natural pause injection
    - Sector-specific acknowledgements
    - Cooldown to prevent repetitive fillers
    """
    
    def __init__(self):
        self.last_filler_time = 0
        self.filler_cooldown_ms = 4000  # Don't repeat fillers too often
        self.last_filler_context: Optional[FillerContext] = None
        self.used_fillers: List[str] = []  # Track recently used fillers
        
        logger.info("🗣️ NaturalSpeechEnhancer initialized")
    
    def get_contextual_filler(
        self,
        context: FillerContext,
        sentiment: str = "neutral",
        sector: str = "banking",
        latency_hint_ms: int = 0
    ) -> Tuple[str, int, int]:
        """
        Get a context-appropriate filler phrase
        
        Args:
            context: The context for the filler
            sentiment: User's detected sentiment
            sector: Business sector
            latency_hint_ms: Expected processing delay
            
        Returns:
            Tuple of (filler_text, pause_before_ms, pause_after_ms)
        """
        now = time.time() * 1000
        
        # Check cooldown
        if now - self.last_filler_time < self.filler_cooldown_ms:
            # Use sector-specific acknowledgement instead
            acks = SECTOR_ACKNOWLEDGEMENTS.get(sector, ["Let me check that..."])
            filler_text = random.choice(acks)
            return filler_text, 0, 200
        
        # Get fillers for this context
        fillers = FILLER_LIBRARY.get(context, FILLER_LIBRARY[FillerContext.THINKING])
        
        # Filter by sentiment appropriateness
        appropriate_fillers = [
            f for f in fillers 
            if sentiment in f.sentiment_appropriate
        ]
        
        if not appropriate_fillers:
            appropriate_fillers = fillers
        
        # Avoid recently used fillers
        available_fillers = [
            f for f in appropriate_fillers 
            if f.text not in self.used_fillers[-3:]
        ]
        
        if not available_fillers:
            available_fillers = appropriate_fillers
        
        # Select filler
        filler = random.choice(available_fillers)
        
        # Track usage
        self.last_filler_time = now
        self.last_filler_context = context
        self.used_fillers.append(filler.text)
        if len(self.used_fillers) > 10:
            self.used_fillers = self.used_fillers[-5:]
        
        # Adjust pauses based on expected latency
        pause_after = filler.pause_after_ms
        if latency_hint_ms > 2000:
            pause_after = min(pause_after + 200, 600)
        
        logger.info(f"🎯 Filler selected: '{filler.text}' (context: {context.name})")
        
        return filler.text, filler.pause_before_ms, pause_after
    
    def get_empathy_prefix(self, sentiment: str) -> Optional[str]:
        """
        Get an empathy prefix for negative sentiment
        
        Returns:
            Empathy phrase or None if sentiment is not negative
        """
        if sentiment == "negative":
            empathy_phrases = [
                "I understand this is frustrating. ",
                "I'm sorry you're experiencing this. ",
                "I can see this is important to you. ",
            ]
            return random.choice(empathy_phrases)
        return None
    
    def inject_natural_pauses(self, response_text: str) -> str:
        """
        Inject subtle pauses into response for natural speech rhythm
        
        Args:
            response_text: Original response text
            
        Returns:
            Text with pause markers (using ellipsis)
        """
        # Don't modify if already has pauses
        if "..." in response_text:
            return response_text
        
        text = response_text
        
        # Add slight pause after first sentence for longer responses
        sentences = text.split(". ")
        if len(sentences) > 2:
            sentences[0] = sentences[0] + "..."
            text = ". ".join(sentences)
        
        # Add pause before amounts/numbers for emphasis
        import re
        text = re.sub(r"(₹|Rs\.?|rupees)\s*(\d)", r"\1 \2", text)
        
        return text
    
    def enhance_response(
        self,
        response_text: str,
        sentiment: str = "neutral",
        add_acknowledgement: bool = False
    ) -> str:
        """
        Enhance a response with natural speech patterns
        
        Args:
            response_text: Original response
            sentiment: User's sentiment
            add_acknowledgement: Whether to add acknowledgement prefix
            
        Returns:
            Enhanced response text
        """
        enhanced = response_text
        
        # Add empathy for negative sentiment
        empathy = self.get_empathy_prefix(sentiment)
        if empathy:
            enhanced = empathy + enhanced
        
        # Add acknowledgement if requested
        if add_acknowledgement and not empathy:
            acks = ["Sure. ", "Of course. ", "Certainly. ", "Absolutely. "]
            enhanced = random.choice(acks) + enhanced
        
        # Inject natural pauses
        enhanced = self.inject_natural_pauses(enhanced)
        
        return enhanced
    
    def get_interruption_acknowledgement(self) -> str:
        """Get acknowledgement phrase after being interrupted"""
        phrases = [
            "Yes, please go ahead.",
            "I'm listening.",
            "Please continue.",
            "Go ahead, I'm here.",
        ]
        return random.choice(phrases)
    
    def get_clarification_request(self, partial_understanding: bool = False) -> str:
        """Get a natural clarification request"""
        if partial_understanding:
            phrases = [
                "I think I understood part of that. Could you please repeat the last bit?",
                "I caught some of that. Could you say it again a bit slower?",
            ]
        else:
            phrases = [
                "I'm sorry, I didn't quite catch that. Could you please repeat?",
                "I'm having trouble hearing you. Could you speak a bit louder?",
                "Could you please repeat that more slowly?",
            ]
        return random.choice(phrases)
    
    def reset(self):
        """Reset for new call"""
        self.last_filler_time = 0
        self.last_filler_context = None
        self.used_fillers = []


# Singleton instance
speech_enhancer = NaturalSpeechEnhancer()


def get_filler(
    context: str = "searching",
    sentiment: str = "neutral", 
    sector: str = "banking"
) -> Tuple[str, int, int]:
    """
    Convenience function to get a contextual filler
    
    Returns:
        Tuple of (filler_text, pause_before_ms, pause_after_ms)
    """
    context_map = {
        "thinking": FillerContext.THINKING,
        "searching": FillerContext.SEARCHING,
        "acknowledging": FillerContext.ACKNOWLEDGING,
        "transitioning": FillerContext.TRANSITIONING,
        "empathizing": FillerContext.EMPATHIZING,
        "clarifying": FillerContext.CLARIFYING,
    }
    ctx = context_map.get(context, FillerContext.SEARCHING)
    return speech_enhancer.get_contextual_filler(ctx, sentiment, sector)
