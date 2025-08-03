"""
Speech Service - Handles speech recognition, synthesis, and pronunciation feedback
Task 6.1 implementation
"""
import asyncio
import io
import json
import time
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import base64
from datetime import datetime, timezone

from utils.logger import logger
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from ..repositories.user_repository import ChildProfileRepository
from ..models.speech_models import (
    SpeechRecognitionRequest,
    SpeechRecognitionResult,
    SpeechRecognitionEngine,
    PronunciationAssessment,
    PronunciationLevel,
    TextToSpeechRequest,
    TextToSpeechResult,
    SpeechSynthesisEngine,
    VoiceInteractionSession,
    SpeechProcessingConfig,
    AudioFormat,
    LanguageCode,
    SpeechQuality,
    WordConfidence
)
from ..models.user_models import Subject


class SpeechService:
    """
    Comprehensive speech processing service for voice interactions and ESL learning
    """
    
    def __init__(self, db: DBConnection, config: SpeechProcessingConfig = None):
        self.db = db
        self.config = config or SpeechProcessingConfig()
        self.child_repo = ChildProfileRepository(db)
        
        # Active voice sessions
        self.active_sessions: Dict[str, VoiceInteractionSession] = {}
        
        # Rate limiting tracking
        self.request_counts: Dict[str, Dict[str, int]] = {}
        
        # Engine configurations
        self.engine_configs = {
            SpeechRecognitionEngine.WHISPER: {
                "api_base": "https://api.openai.com/v1",
                "model": "whisper-1"
            },
            SpeechRecognitionEngine.GOOGLE_SPEECH: {
                "api_base": "https://speech.googleapis.com/v1",
                "model": "latest_long"
            },
            SpeechSynthesisEngine.OPENAI_TTS: {
                "api_base": "https://api.openai.com/v1",
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            }
        }
    
    async def recognize_speech(self, request: SpeechRecognitionRequest) -> SpeechRecognitionResult:
        """
        Convert speech audio to text with confidence scoring
        
        Args:
            request: Speech recognition request with audio data and settings
            
        Returns:
            Speech recognition result with transcript and confidence
        """
        start_time = time.time()
        
        try:
            # Validate request
            if not await self._validate_request_rate_limit(request.user_id):
                return SpeechRecognitionResult(
                    request_id=request.request_id,
                    user_id=request.user_id,
                    engine_used=request.engine,
                    success=False,
                    error_code="RATE_LIMIT_EXCEEDED",
                    error_message="Rate limit exceeded. Please try again later."
                )
            
            # Validate audio quality
            quality_score = await self._assess_audio_quality(request.audio_data, request.audio_format)
            
            if quality_score < self.config.min_audio_quality_score:
                return SpeechRecognitionResult(
                    request_id=request.request_id,
                    user_id=request.user_id,
                    engine_used=request.engine,
                    quality_score=quality_score,
                    success=False,
                    error_code="LOW_AUDIO_QUALITY",
                    error_message="Audio quality is too low for accurate recognition. Please try recording again in a quieter environment."
                )
            
            # Process speech based on engine
            if request.engine == SpeechRecognitionEngine.WHISPER:
                result = await self._recognize_with_whisper(request)
            elif request.engine == SpeechRecognitionEngine.GOOGLE_SPEECH:
                result = await self._recognize_with_google(request)
            else:
                # Fallback to Whisper
                result = await self._recognize_with_whisper(request)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time
            result.quality_score = quality_score
            
            # Update rate limiting
            await self._update_rate_limit_counter(request.user_id)
            
            logger.info(f"Speech recognition completed for user {request.user_id}: '{result.transcript}' (confidence: {result.confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return SpeechRecognitionResult(
                request_id=request.request_id,
                user_id=request.user_id,
                engine_used=request.engine,
                processing_time_ms=processing_time,
                success=False,
                error_code="PROCESSING_ERROR",
                error_message=f"Speech recognition failed: {str(e)}"
            )
    
    async def assess_pronunciation(self, 
                                 user_id: str,
                                 audio_data: bytes,
                                 target_text: str,
                                 audio_format: AudioFormat = AudioFormat.WAV,
                                 language_code: LanguageCode = LanguageCode.EN_US,
                                 subject: Subject = None,
                                 lesson_topic: str = None) -> PronunciationAssessment:
        """
        Assess pronunciation quality for ESL learning
        
        Args:
            user_id: Child's user ID
            audio_data: Audio recording of speech
            target_text: Text that should have been spoken
            audio_format: Format of audio data
            language_code: Language for pronunciation assessment
            subject: Subject context for assessment
            lesson_topic: Topic context for assessment
            
        Returns:
            Detailed pronunciation assessment with feedback
        """
        try:
            # Get child profile for personalized feedback
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            child_age = child_profile.get("age", 8) if child_profile else 8
            
            # First, get speech recognition
            recognition_request = SpeechRecognitionRequest(
                user_id=user_id,
                audio_data=audio_data,
                audio_format=audio_format,
                language_code=language_code,
                expected_words=target_text.lower().split()
            )
            
            recognition_result = await self.recognize_speech(recognition_request)
            
            if not recognition_result.success:
                return PronunciationAssessment(
                    user_id=user_id,
                    target_text=target_text,
                    overall_score=0.0,
                    pronunciation_level=PronunciationLevel.POOR,
                    feedback_message="Could not process audio. Please try recording again.",
                    speech_quality=SpeechQuality.INAUDIBLE,
                    subject=subject,
                    lesson_topic=lesson_topic,
                    engine_used=recognition_request.engine
                )
            
            spoken_text = recognition_result.transcript
            
            # Perform detailed pronunciation analysis
            assessment = await self._analyze_pronunciation(
                target_text=target_text,
                spoken_text=spoken_text,
                word_confidences=recognition_result.words,
                child_age=child_age,
                subject=subject
            )
            
            # Set basic fields
            assessment.user_id = user_id
            assessment.target_text = target_text
            assessment.spoken_text = spoken_text
            assessment.subject = subject
            assessment.lesson_topic = lesson_topic
            assessment.engine_used = recognition_result.engine_used
            assessment.processing_time_ms = recognition_result.processing_time_ms
            
            # Determine speech quality from recognition
            if recognition_result.quality_score >= 0.8:
                assessment.speech_quality = SpeechQuality.CLEAR
            elif recognition_result.quality_score >= 0.6:
                assessment.speech_quality = SpeechQuality.SLIGHTLY_UNCLEAR
            elif recognition_result.quality_score >= 0.4:
                assessment.speech_quality = SpeechQuality.UNCLEAR
            else:
                assessment.speech_quality = SpeechQuality.NOISY
            
            # Calculate pronunciation level
            assessment.pronunciation_level = assessment.calculate_pronunciation_level()
            
            # Generate age-appropriate feedback
            assessment.feedback_message = await self._generate_pronunciation_feedback(
                assessment, child_age, subject
            )
            
            # Generate improvement tips and practice suggestions
            assessment.improvement_tips = await self._generate_improvement_tips(assessment, child_age)
            assessment.practice_suggestions = await self._generate_practice_suggestions(assessment, subject)
            
            logger.info(f"Pronunciation assessment completed for user {user_id}: {assessment.pronunciation_level.value} ({assessment.overall_score:.2f})")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in pronunciation assessment: {str(e)}")
            
            return PronunciationAssessment(
                user_id=user_id,
                target_text=target_text,
                overall_score=0.0,
                pronunciation_level=PronunciationLevel.POOR,
                feedback_message="Sorry, we couldn't assess your pronunciation right now. Please try again.",
                speech_quality=SpeechQuality.UNCLEAR,
                subject=subject,
                lesson_topic=lesson_topic
            )
    
    async def synthesize_speech(self, request: TextToSpeechRequest) -> TextToSpeechResult:
        """
        Convert text to speech audio
        
        Args:
            request: Text-to-speech request with text and voice settings
            
        Returns:
            Generated audio data and metadata
        """
        start_time = time.time()
        
        try:
            # Validate text length
            if len(request.text) > self.config.max_text_length:
                return TextToSpeechResult(
                    request_id=request.request_id,
                    audio_data=b"",
                    audio_format=request.audio_format,
                    audio_duration_ms=0,
                    audio_size_bytes=0,
                    engine_used=request.engine,
                    success=False,
                    error_code="TEXT_TOO_LONG",
                    error_message=f"Text length exceeds maximum of {self.config.max_text_length} characters."
                )
            
            # Adapt text for child audience if age is provided
            adapted_text = request.text
            if request.child_age:
                adapted_text = await self._adapt_text_for_age(request.text, request.child_age, request.subject)
            
            # Synthesize speech based on engine
            if request.engine == SpeechSynthesisEngine.OPENAI_TTS:
                result = await self._synthesize_with_openai(request, adapted_text)
            else:
                # Fallback to OpenAI TTS
                result = await self._synthesize_with_openai(request, adapted_text)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time
            result.text_length = len(request.text)
            
            logger.info(f"Speech synthesis completed: {len(adapted_text)} characters -> {result.audio_size_bytes} bytes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return TextToSpeechResult(
                request_id=request.request_id,
                audio_data=b"",
                audio_format=request.audio_format,
                audio_duration_ms=0,
                audio_size_bytes=0,
                engine_used=request.engine,
                processing_time_ms=processing_time,
                success=False,
                error_code="SYNTHESIS_ERROR",
                error_message=f"Speech synthesis failed: {str(e)}"
            )
    
    async def start_voice_session(self, 
                                user_id: str,
                                subject: Subject = None,
                                lesson_topic: str = None,
                                interaction_type: str = "conversation") -> VoiceInteractionSession:
        """
        Start a new voice interaction session
        
        Args:
            user_id: Child's user ID
            subject: Subject context
            lesson_topic: Topic context
            interaction_type: Type of voice interaction
            
        Returns:
            New voice interaction session
        """
        try:
            session = VoiceInteractionSession(
                user_id=user_id,
                subject=subject,
                lesson_topic=lesson_topic,
                interaction_type=interaction_type
            )
            
            # Store active session
            self.active_sessions[session.session_id] = session
            
            logger.info(f"Started voice session {session.session_id} for user {user_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting voice session: {str(e)}")
            raise
    
    async def end_voice_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a voice interaction session and return summary
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Session summary with performance metrics
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            session.end_session()
            
            # Get session summary
            summary = session.get_session_summary()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Ended voice session {session_id}: {summary['total_interactions']} interactions, {summary['recognition_accuracy']:.1%} accuracy")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error ending voice session: {str(e)}")
            raise
    
    async def add_session_interaction(self, 
                                    session_id: str,
                                    interaction_type: str,
                                    data: Dict[str, Any]) -> None:
        """
        Add an interaction to an active voice session
        
        Args:
            session_id: Session ID
            interaction_type: Type of interaction
            data: Interaction data
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.add_interaction(interaction_type, data)
            
            # Update session metrics based on interaction
            if interaction_type == "speech_recognition":
                if data.get("success", False):
                    session.successful_recognitions += 1
                else:
                    session.failed_recognitions += 1
                
                if "duration_ms" in data:
                    session.total_speech_time_ms += data["duration_ms"]
            
            elif interaction_type == "pronunciation_assessment":
                if "score" in data:
                    session.pronunciation_scores.append(data["score"])
                
                if "words_practiced" in data:
                    session.words_practiced.extend(data["words_practiced"])
    
    # Private helper methods
    
    async def _recognize_with_whisper(self, request: SpeechRecognitionRequest) -> SpeechRecognitionResult:
        """Recognize speech using OpenAI Whisper API"""
        try:
            # Prepare audio file for Whisper API
            audio_file = io.BytesIO(request.audio_data)
            audio_file.name = f"audio.{request.audio_format.value}"
            
            # Make API call to OpenAI Whisper
            # Note: This is a simplified implementation - in production, you'd use the actual OpenAI client
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', audio_file, filename=audio_file.name)
                data.add_field('model', 'whisper-1')
                data.add_field('language', request.language_code.value[:2])
                data.add_field('response_format', 'verbose_json')
                
                headers = {
                    'Authorization': f'Bearer {self._get_api_key("openai")}'
                }
                
                async with session.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        # Extract word-level confidence if available
                        words = []
                        if 'segments' in result_data:
                            for segment in result_data['segments']:
                                if 'words' in segment:
                                    for word_info in segment['words']:
                                        words.append(WordConfidence(
                                            word=word_info.get('word', '').strip(),
                                            confidence=word_info.get('probability', 0.5),
                                            start_time=word_info.get('start', 0.0),
                                            end_time=word_info.get('end', 0.0)
                                        ))
                        
                        return SpeechRecognitionResult(
                            request_id=request.request_id,
                            user_id=request.user_id,
                            transcript=result_data.get('text', ''),
                            confidence=result_data.get('confidence', 0.5),
                            words=words,
                            engine_used=SpeechRecognitionEngine.WHISPER,
                            audio_duration_ms=int(result_data.get('duration', 0) * 1000),
                            context=request.context
                        )
                    else:
                        error_data = await response.json()
                        raise Exception(f"Whisper API error: {error_data}")
        
        except Exception as e:
            logger.error(f"Whisper recognition error: {str(e)}")
            return SpeechRecognitionResult(
                request_id=request.request_id,
                user_id=request.user_id,
                engine_used=SpeechRecognitionEngine.WHISPER,
                success=False,
                error_code="WHISPER_API_ERROR",
                error_message=str(e)
            )
    
    async def _recognize_with_google(self, request: SpeechRecognitionRequest) -> SpeechRecognitionResult:
        """Recognize speech using Google Speech-to-Text API"""
        # Placeholder implementation - would integrate with Google Cloud Speech API
        return SpeechRecognitionResult(
            request_id=request.request_id,
            user_id=request.user_id,
            transcript="",
            confidence=0.0,
            engine_used=SpeechRecognitionEngine.GOOGLE_SPEECH,
            success=False,
            error_code="NOT_IMPLEMENTED",
            error_message="Google Speech API integration not yet implemented"
        )
    
    async def _synthesize_with_openai(self, request: TextToSpeechRequest, text: str) -> TextToSpeechResult:
        """Synthesize speech using OpenAI TTS API"""
        try:
            # Select appropriate voice based on context
            voice = await self._select_voice_for_context(request)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "tts-1",
                    "input": text,
                    "voice": voice,
                    "response_format": request.audio_format.value,
                    "speed": request.speaking_rate
                }
                
                headers = {
                    'Authorization': f'Bearer {self._get_api_key("openai")}',
                    'Content-Type': 'application/json'
                }
                
                async with session.post(
                    'https://api.openai.com/v1/audio/speech',
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        
                        # Estimate audio duration (rough approximation)
                        words_per_minute = 150  # Average speaking rate
                        word_count = len(text.split())
                        duration_ms = int((word_count / words_per_minute) * 60 * 1000 * (1 / request.speaking_rate))
                        
                        return TextToSpeechResult(
                            request_id=request.request_id,
                            audio_data=audio_data,
                            audio_format=request.audio_format,
                            audio_duration_ms=duration_ms,
                            audio_size_bytes=len(audio_data),
                            engine_used=SpeechSynthesisEngine.OPENAI_TTS,
                            voice_used=voice,
                            quality_score=0.85
                        )
                    else:
                        error_data = await response.text()
                        raise Exception(f"OpenAI TTS API error: {error_data}")
        
        except Exception as e:
            logger.error(f"OpenAI TTS synthesis error: {str(e)}")
            return TextToSpeechResult(
                request_id=request.request_id,
                audio_data=b"",
                audio_format=request.audio_format,
                audio_duration_ms=0,
                audio_size_bytes=0,
                engine_used=SpeechSynthesisEngine.OPENAI_TTS,
                success=False,
                error_code="OPENAI_TTS_ERROR",
                error_message=str(e)
            )
    
    async def _analyze_pronunciation(self, 
                                   target_text: str,
                                   spoken_text: str,
                                   word_confidences: List[WordConfidence],
                                   child_age: int,
                                   subject: Subject = None) -> PronunciationAssessment:
        """Analyze pronunciation quality using AI"""
        try:
            # Basic text comparison
            target_words = target_text.lower().split()
            spoken_words = spoken_text.lower().split()
            
            # Calculate basic metrics
            completeness_score = min(len(spoken_words) / len(target_words), 1.0) if target_words else 0.0
            
            # Calculate word-level accuracy
            word_assessments = []
            missing_words = []
            extra_words = []
            
            # Simple word matching (in production, would use phonetic analysis)
            matched_words = 0
            for i, target_word in enumerate(target_words):
                if i < len(spoken_words):
                    spoken_word = spoken_words[i]
                    # Simple similarity check
                    similarity = self._calculate_word_similarity(target_word, spoken_word)
                    
                    word_assessment = {
                        "target_word": target_word,
                        "spoken_word": spoken_word,
                        "accuracy": similarity,
                        "confidence": word_confidences[i].confidence if i < len(word_confidences) else 0.5
                    }
                    word_assessments.append(word_assessment)
                    
                    if similarity >= 0.7:  # Threshold for "correct"
                        matched_words += 1
                else:
                    missing_words.append(target_word)
            
            # Check for extra words
            if len(spoken_words) > len(target_words):
                extra_words = spoken_words[len(target_words):]
            
            # Calculate overall score
            accuracy_score = matched_words / len(target_words) if target_words else 0.0
            fluency_score = completeness_score * 0.8 + (1.0 - len(extra_words) / max(len(spoken_words), 1)) * 0.2
            overall_score = (accuracy_score * 0.6 + fluency_score * 0.4)
            
            return PronunciationAssessment(
                user_id="",  # Will be set by caller
                target_text=target_text,
                spoken_text=spoken_text,
                overall_score=overall_score,
                fluency_score=fluency_score,
                completeness_score=completeness_score,
                word_assessments=word_assessments,
                missing_words=missing_words,
                extra_words=extra_words,
                difficulty_level=min(5, max(1, child_age - 4))  # Age-based difficulty
            )
            
        except Exception as e:
            logger.error(f"Error in pronunciation analysis: {str(e)}")
            return PronunciationAssessment(
                user_id="",
                target_text=target_text,
                spoken_text=spoken_text,
                overall_score=0.0
            )
    
    async def _generate_pronunciation_feedback(self, 
                                             assessment: PronunciationAssessment,
                                             child_age: int,
                                             subject: Subject = None) -> str:
        """Generate age-appropriate pronunciation feedback using AI"""
        try:
            # Build context for AI feedback generation
            context = {
                "child_age": child_age,
                "overall_score": assessment.overall_score,
                "pronunciation_level": assessment.pronunciation_level.value,
                "missing_words": assessment.missing_words,
                "extra_words": assessment.extra_words,
                "subject": subject.value if subject else "general",
                "target_text": assessment.target_text,
                "spoken_text": assessment.spoken_text
            }
            
            system_prompt = f"""You are a supportive ESL tutor providing pronunciation feedback to a {child_age}-year-old child.

FEEDBACK GUIDELINES:
- Use encouraging, positive language appropriate for a {child_age}-year-old
- Focus on what they did well first
- Give specific, actionable suggestions for improvement
- Keep feedback brief and clear (2-3 sentences max)
- Use simple vocabulary suitable for the child's age

CONTEXT:
- Target text: "{assessment.target_text}"
- What child said: "{assessment.spoken_text}"
- Pronunciation score: {assessment.overall_score:.1%}
- Subject context: {subject.value if subject else "general"}

Provide encouraging feedback that helps the child improve their pronunciation."""

            user_message = f"Generate feedback for this pronunciation attempt: {json.dumps(context)}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=150
            )
            
            feedback = response.choices[0].message.content.strip()
            return feedback or assessment.generate_feedback()
            
        except Exception as e:
            logger.warning(f"AI feedback generation failed: {str(e)}")
            return assessment.generate_feedback()
    
    async def _generate_improvement_tips(self, assessment: PronunciationAssessment, child_age: int) -> List[str]:
        """Generate improvement tips based on pronunciation analysis"""
        tips = []
        
        if assessment.overall_score < 0.6:
            tips.append("Practice speaking slowly and clearly")
            tips.append("Try breaking words into smaller parts")
        
        if assessment.missing_words:
            tips.append("Make sure to say all the words")
            tips.append("Take your time with each word")
        
        if assessment.extra_words:
            tips.append("Listen carefully and only say what you hear")
        
        if assessment.fluency_score < 0.5:
            tips.append("Practice reading the text aloud several times")
            tips.append("Try to speak at a steady pace")
        
        # Age-appropriate tips
        if child_age <= 7:
            tips.append("Remember to breathe while speaking")
            tips.append("Use your clear speaking voice")
        else:
            tips.append("Focus on clear consonant sounds")
            tips.append("Pay attention to word stress and rhythm")
        
        return tips[:3]  # Return top 3 tips
    
    async def _generate_practice_suggestions(self, assessment: PronunciationAssessment, subject: Subject = None) -> List[str]:
        """Generate subject-specific practice suggestions"""
        suggestions = []
        
        if subject == Subject.MATHEMATICS:
            suggestions.extend([
                "Practice saying math terms clearly: 'addition', 'subtraction', 'equals'",
                "Count aloud from 1 to 20 to practice number pronunciation"
            ])
        elif subject == Subject.SCIENCE:
            suggestions.extend([
                "Practice science vocabulary words slowly",
                "Record yourself saying new science terms and listen back"
            ])
        elif subject == Subject.ESL:
            suggestions.extend([
                "Practice common English words daily",
                "Listen to English stories and repeat what you hear"
            ])
        
        # General suggestions
        suggestions.extend([
            "Read your favorite book aloud for 5 minutes daily",
            "Practice tongue twisters to improve clarity",
            "Record yourself reading and listen to improve"
        ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def _adapt_text_for_age(self, text: str, child_age: int, subject: Subject = None) -> str:
        """Adapt text to be age-appropriate for speech synthesis"""
        try:
            # If text is already simple enough, return as-is
            if len(text.split()) <= 10 and child_age >= 8:
                return text
            
            system_prompt = f"""Adapt this text to be appropriate for a {child_age}-year-old child's listening comprehension.

ADAPTATION RULES:
- Use simple, clear vocabulary suitable for age {child_age}
- Keep sentences short and easy to follow
- Maintain the educational content but make it accessible
- Use everyday words instead of complex terms when possible
- Keep the same meaning but make it easier to understand

Subject context: {subject.value if subject else "general"}"""

            user_message = f"Please adapt this text: {text}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.3,
                max_tokens=200
            )
            
            adapted_text = response.choices[0].message.content.strip()
            return adapted_text or text
            
        except Exception as e:
            logger.warning(f"Text adaptation failed: {str(e)}")
            return text
    
    async def _select_voice_for_context(self, request: TextToSpeechRequest) -> str:
        """Select appropriate voice based on context and child age"""
        # Default voices for children
        child_friendly_voices = ["nova", "shimmer", "alloy"]
        
        if request.child_age and request.child_age <= 8:
            # Younger children might prefer softer voices
            return "nova"
        elif request.gender == "female":
            return "shimmer"
        elif request.gender == "male":
            return "onyx"
        else:
            return "alloy"  # Neutral default
    
    async def _assess_audio_quality(self, audio_data: bytes, audio_format: AudioFormat) -> float:
        """Assess audio quality for speech recognition"""
        try:
            # Basic audio quality assessment
            # In production, this would include noise analysis, volume checks, etc.
            
            # Check audio size as basic quality indicator
            if len(audio_data) < 1000:  # Too small
                return 0.1
            elif len(audio_data) > 10 * 1024 * 1024:  # Too large might indicate noise
                return 0.3
            else:
                # Assume reasonable quality for mid-range file sizes
                return 0.7
                
        except Exception as e:
            logger.warning(f"Audio quality assessment failed: {str(e)}")
            return 0.5  # Default moderate quality
    
    async def _validate_request_rate_limit(self, user_id: str) -> bool:
        """Validate request doesn't exceed rate limits"""
        try:
            current_time = datetime.now(timezone.utc)
            current_minute = current_time.replace(second=0, microsecond=0)
            current_hour = current_time.replace(minute=0, second=0, microsecond=0)
            
            if user_id not in self.request_counts:
                self.request_counts[user_id] = {}
            
            user_counts = self.request_counts[user_id]
            
            # Check minute limit
            minute_key = current_minute.isoformat()
            minute_count = user_counts.get(minute_key, 0)
            
            if minute_count >= self.config.max_requests_per_minute:
                return False
            
            # Check hour limit
            hour_key = current_hour.isoformat()
            hour_count = sum(
                count for key, count in user_counts.items()
                if key.startswith(hour_key[:13])  # Same hour
            )
            
            if hour_count >= self.config.max_requests_per_hour:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Rate limit validation failed: {str(e)}")
            return True  # Allow on error
    
    async def _update_rate_limit_counter(self, user_id: str) -> None:
        """Update rate limit counters"""
        try:
            current_time = datetime.now(timezone.utc)
            current_minute = current_time.replace(second=0, microsecond=0)
            minute_key = current_minute.isoformat()
            
            if user_id not in self.request_counts:
                self.request_counts[user_id] = {}
            
            self.request_counts[user_id][minute_key] = self.request_counts[user_id].get(minute_key, 0) + 1
            
            # Clean old entries (keep last 2 hours)
            cutoff_time = current_time - timedelta(hours=2)
            user_counts = self.request_counts[user_id]
            
            keys_to_remove = [
                key for key in user_counts.keys()
                if datetime.fromisoformat(key) < cutoff_time
            ]
            
            for key in keys_to_remove:
                del user_counts[key]
                
        except Exception as e:
            logger.warning(f"Rate limit counter update failed: {str(e)}")
    
    def _calculate_word_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words"""
        # Simple Levenshtein distance-based similarity
        if not word1 or not word2:
            return 0.0
        
        if word1 == word2:
            return 1.0
        
        # Calculate edit distance
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        edit_distance = dp[m][n]
        max_len = max(m, n)
        
        return 1.0 - (edit_distance / max_len) if max_len > 0 else 0.0
    
    def _get_api_key(self, service: str) -> str:
        """Get API key for external service"""
        # In production, these would come from environment variables or secure storage
        import os
        
        if service == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        elif service == "google":
            return os.getenv("GOOGLE_CLOUD_API_KEY", "")
        elif service == "azure":
            return os.getenv("AZURE_SPEECH_KEY", "")
        
        return ""