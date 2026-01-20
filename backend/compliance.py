"""
Enterprise Compliance Module for Voice Agent
=============================================
Handles PII protection, consent management, and audit logging
"""

import re
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("voice_agent")


class PIIType(Enum):
    """Types of PII that can be detected"""
    AADHAAR = "aadhaar"
    PAN = "pan"
    PHONE = "phone"
    EMAIL = "email"
    ACCOUNT = "account"
    CVV = "cvv"
    OTP = "otp"
    DOB = "dob"
    PIN = "pin"


@dataclass
class PIIDetection:
    """Result of PII detection"""
    pii_type: PIIType
    original_value: str
    masked_value: str
    position: Tuple[int, int]


@dataclass 
class ComplianceAuditEntry:
    """Audit log entry for compliance"""
    timestamp: str
    call_sid: str
    event_type: str
    details: Dict
    pii_detected: List[str] = field(default_factory=list)


class ComplianceEngine:
    """
    Enterprise compliance engine for voice calls
    
    Features:
    - PII detection and masking for Indian context
    - Call recording consent management
    - Regulated content validation
    - Audit logging
    """
    
    # PII patterns for Indian context with masking templates
    PII_PATTERNS = {
        PIIType.AADHAAR: {
            "pattern": r"\b(\d{4})\s?(\d{4})\s?(\d{4})\b",
            "mask": "XXXX-XXXX-{last4}",
            "description": "Aadhaar Number"
        },
        PIIType.PAN: {
            "pattern": r"\b([A-Z]{5})(\d{4})([A-Z])\b",
            "mask": "XXXXX{digits}X",
            "description": "PAN Card"
        },
        PIIType.PHONE: {
            "pattern": r"\b([6-9])(\d{5})(\d{4})\b",
            "mask": "{first}XXXXX{last4}",
            "description": "Phone Number"
        },
        PIIType.EMAIL: {
            "pattern": r"\b([\w.-]+)@([\w.-]+\.\w+)\b",
            "mask": "****@{domain}",
            "description": "Email Address"
        },
        PIIType.ACCOUNT: {
            "pattern": r"\b(\d{4})(\d{5,10})(\d{4})\b",
            "mask": "{first4}XXXXXXXX{last4}",
            "description": "Account Number"
        },
        PIIType.CVV: {
            "pattern": r"\b[Cc][Vv][Vv]\s*:?\s*(\d{3})\b",
            "mask": "CVV: XXX",
            "description": "CVV"
        },
        PIIType.OTP: {
            "pattern": r"\b[Oo][Tt][Pp]\s*:?\s*(\d{4,6})\b",
            "mask": "OTP: XXXX",
            "description": "OTP"
        },
        PIIType.DOB: {
            "pattern": r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
            "mask": "XX/XX/XXXX",
            "description": "Date of Birth"
        },
        PIIType.PIN: {
            "pattern": r"\b[Pp][Ii][Nn]\s*:?\s*(\d{4,6})\b",
            "mask": "PIN: XXXX",
            "description": "PIN"
        }
    }
    
    # Sector-specific consent scripts
    CONSENT_SCRIPTS = {
        "banking": {
            "recording": "This call is being recorded for quality and training purposes as per RBI guidelines.",
            "data_usage": "Your personal information will be handled as per our privacy policy.",
        },
        "financial": {
            "recording": "This call may be recorded for quality assurance and regulatory compliance.",
            "data_usage": "Your investment information is protected under SEBI guidelines.",
        },
        "insurance": {
            "recording": "This call is being recorded as per IRDAI regulations for your protection.",
            "data_usage": "Your policy information is handled as per regulatory requirements.",
        },
        "healthcare_appt": {
            "recording": "This call may be recorded for quality purposes.",
            "data_usage": "Your health information is protected under applicable privacy laws.",
        },
        "healthcare_patient": {
            "recording": "This call may be recorded for quality and medical record purposes.",
            "data_usage": "Your medical information is confidential and protected.",
        },
        "bpo": {
            "recording": "This call may be recorded for quality and training purposes.",
            "data_usage": "Your information is handled as per our privacy policy.",
        }
    }
    
    # Phrases that indicate hallucination/uncertainty
    HALLUCINATION_INDICATORS = [
        "i think", "i believe", "probably", "might be",
        "i'm not sure but", "as far as i know", "i guess",
        "it could be", "maybe", "possibly", "i assume"
    ]
    
    # Unauthorized commitment phrases
    COMMITMENT_PHRASES = [
        "i guarantee", "i promise", "definitely will",
        "100%", "absolutely certain", "guaranteed",
        "for sure", "without a doubt"
    ]
    
    def __init__(self):
        self.audit_log: List[ComplianceAuditEntry] = []
        self.consent_given: Dict[str, bool] = {}  # call_sid -> consent status
        logger.info("🛡️ ComplianceEngine initialized")
    
    def detect_pii(self, text: str) -> List[PIIDetection]:
        """
        Detect PII in text
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of PII detections
        """
        detections = []
        
        for pii_type, config in self.PII_PATTERNS.items():
            pattern = config["pattern"]
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                original = match.group(0)
                masked = self._mask_pii(original, pii_type, match.groups())
                
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    original_value=original,
                    masked_value=masked,
                    position=(match.start(), match.end())
                ))
        
        if detections:
            logger.warning(f"⚠️ PII Detected: {[d.pii_type.value for d in detections]}")
        
        return detections
    
    def _mask_pii(self, original: str, pii_type: PIIType, groups: tuple) -> str:
        """Create masked version of PII"""
        config = self.PII_PATTERNS[pii_type]
        mask_template = config["mask"]
        
        try:
            if pii_type == PIIType.AADHAAR:
                return f"XXXX-XXXX-{groups[2]}"
            elif pii_type == PIIType.PAN:
                return f"XXXXX{groups[1]}X"
            elif pii_type == PIIType.PHONE:
                return f"{groups[0]}XXXXX{groups[2]}"
            elif pii_type == PIIType.EMAIL:
                return f"****@{groups[1]}"
            elif pii_type == PIIType.ACCOUNT:
                return f"{groups[0]}XXXXXXXX{groups[2]}"
            else:
                return mask_template
        except:
            return "XXXXXX"
    
    def mask_pii_in_text(self, text: str, for_logging: bool = True) -> str:
        """
        Mask all PII in text
        
        Args:
            text: Original text
            for_logging: If True, masks for logs; if False, for display
            
        Returns:
            Text with PII masked
        """
        detections = self.detect_pii(text)
        masked_text = text
        
        # Sort by position descending to replace from end
        detections.sort(key=lambda d: d.position[0], reverse=True)
        
        for detection in detections:
            start, end = detection.position
            masked_text = masked_text[:start] + detection.masked_value + masked_text[end:]
        
        return masked_text
    
    def get_consent_script(self, sector: str) -> str:
        """Get consent script for sector"""
        scripts = self.CONSENT_SCRIPTS.get(sector, self.CONSENT_SCRIPTS["bpo"])
        return scripts["recording"]
    
    def record_consent(self, call_sid: str, consent_given: bool):
        """Record consent status for a call"""
        self.consent_given[call_sid] = consent_given
        
        self._log_audit(
            call_sid=call_sid,
            event_type="CONSENT_RECORDED",
            details={"consent_given": consent_given}
        )
        
        logger.info(f"📋 Consent recorded for {call_sid}: {consent_given}")
    
    def check_consent(self, call_sid: str) -> bool:
        """Check if consent was given for a call"""
        return self.consent_given.get(call_sid, False)
    
    def validate_response(self, response: str, sector: str) -> Dict:
        """
        Validate agent response for compliance
        
        Args:
            response: Agent's response text
            sector: Business sector
            
        Returns:
            Validation result with issues if any
        """
        issues = []
        warnings = []
        
        response_lower = response.lower()
        
        # Check for hallucination indicators
        for phrase in self.HALLUCINATION_INDICATORS:
            if phrase in response_lower:
                warnings.append(f"UNCERTAINTY_LANGUAGE: '{phrase}'")
        
        # Check for unauthorized commitments
        for phrase in self.COMMITMENT_PHRASES:
            if phrase in response_lower:
                issues.append(f"UNAUTHORIZED_COMMITMENT: '{phrase}'")
        
        # Check for PII in response (agent should not repeat PII)
        pii_detections = self.detect_pii(response)
        for detection in pii_detections:
            if detection.pii_type in [PIIType.CVV, PIIType.OTP, PIIType.PIN]:
                issues.append(f"SENSITIVE_PII_IN_RESPONSE: {detection.pii_type.value}")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"⚠️ Response validation failed: {issues}")
        
        return {
            "valid": is_valid,
            "issues": issues,
            "warnings": warnings,
            "requires_review": len(issues) > 0 or len(warnings) > 2
        }
    
    def sanitize_for_logging(self, call_sid: str, turn_type: str, text: str) -> str:
        """
        Sanitize text for safe logging (PII masked)
        
        Args:
            call_sid: Call identifier
            turn_type: "user" or "agent"
            text: Original text
            
        Returns:
            Sanitized text safe for logging
        """
        # Mask PII
        masked_text = self.mask_pii_in_text(text)
        
        # Log the sanitization if PII was found
        if masked_text != text:
            self._log_audit(
                call_sid=call_sid,
                event_type="PII_MASKED",
                details={
                    "turn_type": turn_type,
                    "original_length": len(text),
                    "masked_length": len(masked_text)
                },
                pii_detected=["REDACTED"]
            )
        
        return masked_text
    
    def _log_audit(
        self, 
        call_sid: str, 
        event_type: str, 
        details: Dict,
        pii_detected: List[str] = None
    ):
        """Add entry to audit log"""
        entry = ComplianceAuditEntry(
            timestamp=datetime.now().isoformat(),
            call_sid=call_sid,
            event_type=event_type,
            details=details,
            pii_detected=pii_detected or []
        )
        self.audit_log.append(entry)
        
        # Keep only last 1000 entries in memory
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-500:]
    
    def get_audit_log(self, call_sid: Optional[str] = None) -> List[Dict]:
        """Get audit log entries, optionally filtered by call"""
        entries = self.audit_log
        if call_sid:
            entries = [e for e in entries if e.call_sid == call_sid]
        return [
            {
                "timestamp": e.timestamp,
                "call_sid": e.call_sid,
                "event_type": e.event_type,
                "details": e.details
            }
            for e in entries
        ]
    
    def cleanup_call(self, call_sid: str):
        """Cleanup consent record after call ends"""
        if call_sid in self.consent_given:
            del self.consent_given[call_sid]


# Singleton instance
compliance_engine = ComplianceEngine()


# Convenience functions
def mask_pii(text: str) -> str:
    """Mask PII in text for safe logging"""
    return compliance_engine.mask_pii_in_text(text)


def get_consent_script(sector: str) -> str:
    """Get consent script for sector"""
    return compliance_engine.get_consent_script(sector)


def validate_response(response: str, sector: str) -> Dict:
    """Validate agent response for compliance"""
    return compliance_engine.validate_response(response, sector)


def sanitize_log(call_sid: str, turn_type: str, text: str) -> str:
    """Sanitize text for safe logging"""
    return compliance_engine.sanitize_for_logging(call_sid, turn_type, text)
