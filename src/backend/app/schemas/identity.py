"""
Pydantic schemas for Identity endpoints
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from enum import Enum


class CommunicationStyle(str, Enum):
    formal = "formal"
    casual = "casual"
    friendly = "friendly"
    direct = "direct"
    humorous = "humorous"


class ResponseLength(str, Enum):
    short = "short"      # ~75 words
    medium = "medium"    # ~150 words
    detailed = "detailed"  # ~300 words


# Response-length label → avg word count
RESPONSE_LENGTH_MAP = {
    ResponseLength.short: 75,
    ResponseLength.medium: 150,
    ResponseLength.detailed: 300,
}


class OnboardingRequest(BaseModel):
    """Onboarding questionnaire — 6 questions that seed the twin's identity"""
    role: str  # Q1: What do you do? (role / domain)
    communication_style: CommunicationStyle  # Q2: Communication style
    topics_avoided: List[str]  # Q3: Topics NOT to talk about publicly
    response_length: ResponseLength  # Q4: Typical response length
    audience_tone: str  # Q5: Tone used with fans/followers
    three_words: List[str]  # Q6: 3 words that describe you

    @field_validator("topics_avoided")
    @classmethod
    def at_least_one_avoided(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v if t.strip()]
        if not cleaned:
            raise ValueError("At least one avoided topic is required")
        return cleaned

    @field_validator("three_words")
    @classmethod
    def exactly_three_words(cls, v: List[str]) -> List[str]:
        cleaned = [w.strip() for w in v if w.strip()]
        if len(cleaned) != 3:
            raise ValueError("Exactly 3 words are required")
        return cleaned


class OnboardingResponse(BaseModel):
    """Result of completing the onboarding questionnaire"""
    twin_id: str
    domain: str
    tone: str
    avg_response_length: int
    vocabulary_description: str
    communication_style: str
    topics_avoided: List[str]
    profile_version: int


class TopicRequest(BaseModel):
    """Request to add a topic"""
    topic: str
    context: Optional[str] = None

    @field_validator("topic")
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Topic cannot be empty")
        return v


class TopicResponse(BaseModel):
    """Single topic response"""
    id: str
    topic: str
    topic_type: str
    context: Optional[str]
    frequency: int


class IdentityProfileResponse(BaseModel):
    """Full identity profile"""
    vocabulary_description: Optional[str]
    communication_style: Optional[str]
    topics_known: List[str]
    topics_avoided: List[str]
    profile_complete: bool  # True if onboarding has been completed


class UpdateIdentityRequest(BaseModel):
    """Patch identity profile fields"""
    vocabulary_description: Optional[str] = None
    communication_style: Optional[str] = None
    topics_known: Optional[List[str]] = None
    topics_avoided: Optional[List[str]] = None


class IdentityConfidenceResponse(BaseModel):
    """Confidence score stub — how well the twin knows the user"""
    score: float           # 0.0 – 1.0
    label: str             # "low" | "medium" | "high"
    fields_complete: int   # number of profile fields filled
    total_fields: int      # total profile fields scored
    message: str           # human-readable status


class VoiceConsentRequest(BaseModel):
    """Grant or revoke voice clone consent."""

    granted: bool


class VoiceConsentResponse(BaseModel):
    """Voice consent state for the current user."""

    consent_type: str
    granted: bool
    granted_at: Optional[str] = None
    expires_at: Optional[str] = None


class VoiceEnrollmentRequest(BaseModel):
    """Voice profile enrollment payload."""

    voice_provider: str = "mock"
    voice_model_id: Optional[str] = None
    voice_sample_url: Optional[str] = None

    @field_validator("voice_provider")
    @classmethod
    def validate_voice_provider(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in {"mock", "elevenlabs"}:
            raise ValueError("voice_provider must be 'mock' or 'elevenlabs'")
        return normalized


class VoiceEnrollmentResponse(BaseModel):
    """Voice profile enrollment status."""

    enrolled: bool
    voice_provider: Optional[str] = None
    voice_model_id: Optional[str] = None
    voice_sample_url: Optional[str] = None
    consent_granted: bool
