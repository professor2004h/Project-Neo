"""
Speech processing and voice interaction models for Cambridge AI Tutor
Task 6.1 implementation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

from .user_models import Subject


class SpeechRecognitionEngine(str, Enum):
    """Speech recognition engine enumeration"""
    WHISPER = "whisper"
    GOOGLE_SPEECH = "google_speech"
    AZURE_SPEECH = "azure_speech"
    AWS_TRANSCRIBE = "aws_transcribe"


class SpeechSynthesisEngine(str, Enum):
    """Speech synthesis engine enumeration"""
    OPENAI_TTS = "openai_tts"
    GOOGLE_TTS = "google_tts"
    AZURE_TTS = "azure_tts"
    AWS_POLLY = "aws_polly"


class AudioFormat(str, Enum):
    """Audio format enumeration"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    M4A = "m4a"


class PronunciationLevel(str, Enum):
    """Pronunciation accuracy level enumeration"""
    EXCELLENT = "excellent"     # 90-100%
    GOOD = "good"              # 80-89%
    FAIR = "fair"              # 70-79%
    NEEDS_IMPROVEMENT = "needs_improvement"  # 60-69%
    POOR = "poor"              # <60%


class SpeechQuality(str, Enum):
    """Speech quality assessment enumeration"""
    CLEAR = "clear"
    SLIGHTLY_UNCLEAR = "slightly_unclear"
    UNCLEAR = "unclear"
    NOISY = "noisy"
    INAUDIBLE = "inaudible"


class LanguageCode(str, Enum):
    """Supported language codes for speech processing"""
    EN_US = "en-US"  # English (US)
    EN_GB = "en-GB"  # English (UK) 
    EN_AU = "en-AU"  # English (Australia)
    ES_ES = "es-ES"  # Spanish (Spain)
    ES_MX = "es-MX"  # Spanish (Mexico)
    FR_FR = "fr-FR"  # French (France)
    DE_DE = "de-DE"  # German (Germany)
    IT_IT = "it-IT"  # Italian (Italy)
    PT_BR = "pt-BR"  # Portuguese (Brazil)
    ZH_CN = "zh-CN"  # Chinese (Simplified)


class SpeechRecognitionRequest(BaseModel):
    """Request model for speech recognition"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    audio_data: bytes = Field(description="Audio data in bytes")
    audio_format: AudioFormat = AudioFormat.WAV
    language_code: LanguageCode = LanguageCode.EN_US
    engine: SpeechRecognitionEngine = SpeechRecognitionEngine.WHISPER
    context: Dict[str, Any] = Field(default_factory=dict)
    expected_words: Optional[List[str]] = None  # For pronunciation assessment
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.7)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')


class WordConfidence(BaseModel):
    """Individual word confidence and timing information"""
    word: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    start_time: float = Field(ge=0.0, description="Start time in seconds")
    end_time: float = Field(ge=0.0, description="End time in seconds")
    pronunciation_score: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    phoneme_scores: Dict[str, float] = Field(default_factory=dict)


class SpeechRecognitionResult(BaseModel):
    """Result model for speech recognition"""
    request_id: str
    user_id: str
    transcript: str = Field(default="")
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    language_detected: Optional[LanguageCode] = None
    words: List[WordConfidence] = Field(default_factory=list)
    
    # Processing details
    engine_used: SpeechRecognitionEngine
    processing_time_ms: int = Field(ge=0, default=0)
    audio_duration_ms: int = Field(ge=0, default=0)
    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Error handling
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = Field(default_factory=dict)


class PronunciationAssessment(BaseModel):
    """Pronunciation assessment for ESL learning"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    target_text: str = Field(min_length=1, description="Text that should have been spoken")
    spoken_text: str = Field(default="", description="Actual transcribed text")
    
    # Overall scores
    overall_score: float = Field(ge=0.0, le=1.0, default=0.0)
    pronunciation_level: PronunciationLevel = PronunciationLevel.POOR
    fluency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    completeness_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Detailed assessment
    word_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    phoneme_errors: List[str] = Field(default_factory=list)
    missing_words: List[str] = Field(default_factory=list)
    extra_words: List[str] = Field(default_factory=list)
    
    # Feedback and suggestions
    feedback_message: str = Field(default="")
    improvement_tips: List[str] = Field(default_factory=list)
    practice_suggestions: List[str] = Field(default_factory=list)
    
    # Audio quality
    speech_quality: SpeechQuality = SpeechQuality.UNCLEAR
    background_noise_level: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Context
    subject: Optional[Subject] = None
    lesson_topic: Optional[str] = None
    difficulty_level: int = Field(ge=1, le=5, default=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_used: SpeechRecognitionEngine = SpeechRecognitionEngine.WHISPER
    processing_time_ms: int = Field(ge=0, default=0)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def calculate_pronunciation_level(self) -> PronunciationLevel:
        """Calculate pronunciation level based on overall score"""
        if self.overall_score >= 0.9:
            return PronunciationLevel.EXCELLENT
        elif self.overall_score >= 0.8:
            return PronunciationLevel.GOOD
        elif self.overall_score >= 0.7:
            return PronunciationLevel.FAIR
        elif self.overall_score >= 0.6:
            return PronunciationLevel.NEEDS_IMPROVEMENT
        else:
            return PronunciationLevel.POOR
    
    def generate_feedback(self) -> str:
        """Generate personalized feedback message"""
        level = self.calculate_pronunciation_level()
        
        if level == PronunciationLevel.EXCELLENT:
            return "Excellent pronunciation! Your speech is clear and accurate."
        elif level == PronunciationLevel.GOOD:
            return "Good pronunciation! Minor improvements could make your speech even clearer."
        elif level == PronunciationLevel.FAIR:
            return "Fair pronunciation. Focus on the highlighted areas for improvement."
        elif level == PronunciationLevel.NEEDS_IMPROVEMENT:
            return "Your pronunciation needs some work. Practice the suggested exercises."
        else:
            return "Let's work on pronunciation together. Start with the basic sounds."


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    text: str = Field(min_length=1, max_length=5000)
    language_code: LanguageCode = LanguageCode.EN_US
    voice_name: Optional[str] = None
    gender: Optional[str] = Field(default="neutral", pattern="^(male|female|neutral)$")
    speaking_rate: float = Field(ge=0.25, le=4.0, default=1.0)
    pitch: float = Field(ge=-20.0, le=20.0, default=0.0)
    volume_gain_db: float = Field(ge=-96.0, le=16.0, default=0.0)
    
    # Audio output settings
    audio_format: AudioFormat = AudioFormat.MP3
    sample_rate: int = Field(ge=8000, le=48000, default=22050)
    
    # Engine settings
    engine: SpeechSynthesisEngine = SpeechSynthesisEngine.OPENAI_TTS
    
    # Context for educational content
    context: Dict[str, Any] = Field(default_factory=dict)
    subject: Optional[Subject] = None
    child_age: Optional[int] = Field(ge=5, le=12, default=None)


class TextToSpeechResult(BaseModel):
    """Result model for text-to-speech synthesis"""
    request_id: str
    audio_data: bytes = Field(description="Generated audio data")
    audio_format: AudioFormat
    audio_duration_ms: int = Field(ge=0)
    audio_size_bytes: int = Field(ge=0)
    
    # Processing details
    engine_used: SpeechSynthesisEngine
    voice_used: str = Field(default="")
    processing_time_ms: int = Field(ge=0, default=0)
    
    # Quality metrics
    quality_score: float = Field(ge=0.0, le=1.0, default=0.8)
    
    # Error handling
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    text_length: int = Field(ge=0, default=0)


class VoiceInteractionSession(BaseModel):
    """Voice interaction session for conversation tracking"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    
    # Session context
    subject: Optional[Subject] = None
    lesson_topic: Optional[str] = None
    interaction_type: str = Field(default="conversation")  # conversation, pronunciation, reading
    
    # Interactions in this session
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance tracking
    total_speech_time_ms: int = Field(ge=0, default=0)
    successful_recognitions: int = Field(ge=0, default=0)
    failed_recognitions: int = Field(ge=0, default=0)
    average_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # ESL specific metrics
    pronunciation_scores: List[float] = Field(default_factory=list)
    words_practiced: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    
    # Engagement metrics
    engagement_level: float = Field(ge=0.0, le=1.0, default=0.5)
    interruptions: int = Field(ge=0, default=0)
    help_requests: int = Field(ge=0, default=0)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def add_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """Add an interaction to the session"""
        interaction = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": interaction_type,
            "data": data
        }
        self.interactions.append(interaction)
    
    def end_session(self) -> None:
        """End the voice interaction session"""
        self.ended_at = datetime.now(timezone.utc)
        
        # Calculate session metrics
        if self.interactions:
            confidence_scores = []
            for interaction in self.interactions:
                if interaction["type"] == "speech_recognition" and "confidence" in interaction["data"]:
                    confidence_scores.append(interaction["data"]["confidence"])
            
            if confidence_scores:
                self.average_confidence = sum(confidence_scores) / len(confidence_scores)
    
    def get_session_duration_ms(self) -> int:
        """Get session duration in milliseconds"""
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds() * 1000)
        else:
            return int((datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the voice interaction session"""
        duration_ms = self.get_session_duration_ms()
        total_interactions = len(self.interactions)
        recognition_accuracy = (self.successful_recognitions / (self.successful_recognitions + self.failed_recognitions)) if (self.successful_recognitions + self.failed_recognitions) > 0 else 0.0
        
        avg_pronunciation = sum(self.pronunciation_scores) / len(self.pronunciation_scores) if self.pronunciation_scores else 0.0
        
        return {
            "session_id": self.session_id,
            "duration_ms": duration_ms,
            "total_interactions": total_interactions,
            "recognition_accuracy": recognition_accuracy,
            "average_confidence": self.average_confidence,
            "average_pronunciation_score": avg_pronunciation,
            "words_practiced_count": len(set(self.words_practiced)),
            "engagement_level": self.engagement_level,
            "subject": self.subject.value if self.subject else None,
            "lesson_topic": self.lesson_topic,
            "improvement_areas": self.improvement_areas
        }


class SpeechProcessingConfig(BaseModel):
    """Configuration for speech processing engines and settings"""
    # Default engines
    default_recognition_engine: SpeechRecognitionEngine = SpeechRecognitionEngine.WHISPER
    default_synthesis_engine: SpeechSynthesisEngine = SpeechSynthesisEngine.OPENAI_TTS
    
    # Recognition settings
    recognition_confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.7)
    max_audio_duration_seconds: int = Field(ge=1, le=300, default=60)
    supported_audio_formats: List[AudioFormat] = Field(default_factory=lambda: [AudioFormat.WAV, AudioFormat.MP3, AudioFormat.WEBM])
    
    # Synthesis settings
    default_speaking_rate: float = Field(ge=0.5, le=2.0, default=1.0)
    default_voice_gender: str = "neutral"
    max_text_length: int = Field(ge=100, le=5000, default=1000)
    
    # Language settings
    supported_languages: List[LanguageCode] = Field(default_factory=lambda: [LanguageCode.EN_US, LanguageCode.EN_GB, LanguageCode.ES_ES])
    default_language: LanguageCode = LanguageCode.EN_US
    
    # Quality settings
    min_audio_quality_score: float = Field(ge=0.0, le=1.0, default=0.3)
    pronunciation_assessment_enabled: bool = True
    noise_reduction_enabled: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = Field(ge=1, le=1000, default=60)
    max_requests_per_hour: int = Field(ge=10, le=10000, default=500)
    
    # Storage settings
    store_audio_recordings: bool = False
    audio_retention_days: int = Field(ge=1, le=365, default=30)
    
    # ESL specific settings
    enable_phoneme_analysis: bool = True
    enable_fluency_assessment: bool = True
    provide_pronunciation_feedback: bool = True