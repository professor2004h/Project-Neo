"""
Unit tests for Speech Service and Speech Models - Task 6.1
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
import json
import io

from tutor.services.speech_service import SpeechService
from tutor.models.speech_models import (
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
from tutor.models.user_models import Subject


class TestSpeechModels:
    """Test cases for Speech Models"""
    
    def test_speech_recognition_request_creation(self):
        """Test creating a speech recognition request"""
        audio_data = b"fake_audio_data"
        
        request = SpeechRecognitionRequest(
            user_id="child-123",
            audio_data=audio_data,
            audio_format=AudioFormat.WAV,
            language_code=LanguageCode.EN_US,
            engine=SpeechRecognitionEngine.WHISPER
        )
        
        assert request.user_id == "child-123"
        assert request.audio_data == audio_data
        assert request.audio_format == AudioFormat.WAV
        assert request.language_code == LanguageCode.EN_US
        assert request.engine == SpeechRecognitionEngine.WHISPER
        assert request.confidence_threshold == 0.7
        assert request.request_id is not None
    
    def test_word_confidence_creation(self):
        """Test creating word confidence data"""
        word_conf = WordConfidence(
            word="hello",
            confidence=0.95,
            start_time=1.0,
            end_time=1.5,
            pronunciation_score=0.9
        )
        
        assert word_conf.word == "hello"
        assert word_conf.confidence == 0.95
        assert word_conf.start_time == 1.0
        assert word_conf.end_time == 1.5
        assert word_conf.pronunciation_score == 0.9
    
    def test_speech_recognition_result_creation(self):
        """Test creating speech recognition result"""
        words = [
            WordConfidence(word="hello", confidence=0.9, start_time=0.0, end_time=0.5),
            WordConfidence(word="world", confidence=0.85, start_time=0.6, end_time=1.2)
        ]
        
        result = SpeechRecognitionResult(
            request_id="req-123",
            user_id="child-123",
            transcript="hello world",
            confidence=0.88,
            words=words,
            engine_used=SpeechRecognitionEngine.WHISPER,
            processing_time_ms=1500,
            audio_duration_ms=2000
        )
        
        assert result.request_id == "req-123"
        assert result.user_id == "child-123"
        assert result.transcript == "hello world"
        assert result.confidence == 0.88
        assert len(result.words) == 2
        assert result.engine_used == SpeechRecognitionEngine.WHISPER
        assert result.success is True
    
    def test_pronunciation_assessment_creation(self):
        """Test creating pronunciation assessment"""
        assessment = PronunciationAssessment(
            user_id="child-123",
            target_text="Hello world",
            spoken_text="Hello world",
            overall_score=0.9,
            subject=Subject.ESL,
            lesson_topic="Greetings"
        )
        
        assert assessment.user_id == "child-123"
        assert assessment.target_text == "Hello world"
        assert assessment.spoken_text == "Hello world"
        assert assessment.overall_score == 0.9
        assert assessment.subject == Subject.ESL
        assert assessment.lesson_topic == "Greetings"
        assert assessment.assessment_id is not None
    
    def test_pronunciation_level_calculation(self):
        """Test pronunciation level calculation"""
        assessment = PronunciationAssessment(
            user_id="child-123",
            target_text="test",
            overall_score=0.95
        )
        
        level = assessment.calculate_pronunciation_level()
        assert level == PronunciationLevel.EXCELLENT
        
        assessment.overall_score = 0.85
        level = assessment.calculate_pronunciation_level()
        assert level == PronunciationLevel.GOOD
        
        assessment.overall_score = 0.75
        level = assessment.calculate_pronunciation_level()
        assert level == PronunciationLevel.FAIR
        
        assessment.overall_score = 0.65
        level = assessment.calculate_pronunciation_level()
        assert level == PronunciationLevel.NEEDS_IMPROVEMENT
        
        assessment.overall_score = 0.4
        level = assessment.calculate_pronunciation_level()
        assert level == PronunciationLevel.POOR
    
    def test_pronunciation_feedback_generation(self):
        """Test pronunciation feedback generation"""
        assessment = PronunciationAssessment(
            user_id="child-123",
            target_text="test",
            overall_score=0.95
        )
        
        feedback = assessment.generate_feedback()
        assert "Excellent" in feedback
        
        assessment.overall_score = 0.4
        feedback = assessment.generate_feedback()
        assert "work" in feedback or "practice" in feedback
    
    def test_text_to_speech_request_creation(self):
        """Test creating text-to-speech request"""
        request = TextToSpeechRequest(
            text="Hello, how are you today?",
            language_code=LanguageCode.EN_US,
            engine=SpeechSynthesisEngine.OPENAI_TTS,
            child_age=8,
            subject=Subject.ESL
        )
        
        assert request.text == "Hello, how are you today?"
        assert request.language_code == LanguageCode.EN_US
        assert request.engine == SpeechSynthesisEngine.OPENAI_TTS
        assert request.child_age == 8
        assert request.subject == Subject.ESL
        assert request.speaking_rate == 1.0
        assert request.request_id is not None
    
    def test_voice_interaction_session(self):
        """Test voice interaction session management"""
        session = VoiceInteractionSession(
            user_id="child-123",
            subject=Subject.MATHEMATICS,
            lesson_topic="Addition",
            interaction_type="pronunciation"
        )
        
        assert session.user_id == "child-123"
        assert session.subject == Subject.MATHEMATICS
        assert session.lesson_topic == "Addition"
        assert session.interaction_type == "pronunciation"
        assert session.started_at is not None
        assert session.ended_at is None
        assert len(session.interactions) == 0
        
        # Add interaction
        session.add_interaction("speech_recognition", {
            "transcript": "hello",
            "confidence": 0.9
        })
        
        assert len(session.interactions) == 1
        interaction = session.interactions[0]
        assert interaction["type"] == "speech_recognition"
        assert interaction["data"]["transcript"] == "hello"
        
        # End session
        session.end_session()
        assert session.ended_at is not None
        
        # Get session summary
        summary = session.get_session_summary()
        assert summary["session_id"] == session.session_id
        assert summary["total_interactions"] == 1
        assert "duration_ms" in summary
    
    def test_speech_processing_config(self):
        """Test speech processing configuration"""
        config = SpeechProcessingConfig(
            recognition_confidence_threshold=0.8,
            max_audio_duration_seconds=120,
            max_requests_per_minute=30
        )
        
        assert config.recognition_confidence_threshold == 0.8
        assert config.max_audio_duration_seconds == 120
        assert config.max_requests_per_minute == 30
        assert config.default_recognition_engine == SpeechRecognitionEngine.WHISPER
        assert config.pronunciation_assessment_enabled is True


class TestSpeechService:
    """Test cases for SpeechService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_child_repo(self):
        """Mock child repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def speech_config(self):
        """Test speech processing configuration"""
        return SpeechProcessingConfig(
            recognition_confidence_threshold=0.7,
            max_requests_per_minute=10,
            max_requests_per_hour=100
        )
    
    @pytest.fixture
    def speech_service(self, mock_db, speech_config):
        """Create speech service with mocked dependencies"""
        with patch('tutor.services.speech_service.ChildProfileRepository') as mock_child_repo_class:
            service = SpeechService(mock_db, speech_config)
            service.child_repo = mock_child_repo_class.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_recognize_speech_success(self, speech_service):
        """Test successful speech recognition"""
        # Mock API response
        mock_response_data = {
            "text": "Hello world",
            "confidence": 0.9,
            "duration": 2.0,
            "segments": [
                {
                    "words": [
                        {"word": "Hello", "probability": 0.95, "start": 0.0, "end": 0.5},
                        {"word": "world", "probability": 0.85, "start": 0.6, "end": 1.2}
                    ]
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Mock API key
            with patch.object(speech_service, '_get_api_key', return_value="fake_key"):
                request = SpeechRecognitionRequest(
                    user_id="child-123",
                    audio_data=b"fake_audio_data",
                    audio_format=AudioFormat.WAV,
                    engine=SpeechRecognitionEngine.WHISPER
                )
                
                result = await speech_service.recognize_speech(request)
                
                assert result.success is True
                assert result.transcript == "Hello world"
                assert result.confidence == 0.9
                assert len(result.words) == 2
                assert result.words[0].word == "Hello"
                assert result.words[0].confidence == 0.95
                assert result.engine_used == SpeechRecognitionEngine.WHISPER
    
    @pytest.mark.asyncio
    async def test_recognize_speech_low_quality(self, speech_service):
        """Test speech recognition with low audio quality"""
        request = SpeechRecognitionRequest(
            user_id="child-123",
            audio_data=b"low_quality",  # Very small audio data
            audio_format=AudioFormat.WAV
        )
        
        result = await speech_service.recognize_speech(request)
        
        assert result.success is False
        assert result.error_code == "LOW_AUDIO_QUALITY"
        assert "audio quality" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_assess_pronunciation_success(self, speech_service):
        """Test successful pronunciation assessment"""
        # Mock child profile
        speech_service.child_repo.get_by_id.return_value = {
            "child_id": "child-123",
            "age": 8,
            "name": "Alice"
        }
        
        # Mock speech recognition
        mock_recognition_result = SpeechRecognitionResult(
            request_id="req-123",
            user_id="child-123",
            transcript="Hello world",
            confidence=0.9,
            words=[
                WordConfidence(word="Hello", confidence=0.95, start_time=0.0, end_time=0.5),
                WordConfidence(word="world", confidence=0.85, start_time=0.6, end_time=1.2)
            ],
            engine_used=SpeechRecognitionEngine.WHISPER,
            quality_score=0.8
        )
        
        with patch.object(speech_service, 'recognize_speech', return_value=mock_recognition_result):
            # Mock AI feedback generation
            with patch('tutor.services.speech_service.make_llm_api_call') as mock_llm:
                mock_llm_response = Mock()
                mock_llm_response.choices = [Mock()]
                mock_llm_response.choices[0].message.content = "Great job! Your pronunciation is very clear."
                mock_llm.return_value = mock_llm_response
                
                assessment = await speech_service.assess_pronunciation(
                    user_id="child-123",
                    audio_data=b"fake_audio",
                    target_text="Hello world",
                    subject=Subject.ESL
                )
                
                assert assessment.user_id == "child-123"
                assert assessment.target_text == "Hello world"
                assert assessment.spoken_text == "Hello world"
                assert assessment.overall_score > 0.0
                assert assessment.subject == Subject.ESL
                assert assessment.speech_quality == SpeechQuality.CLEAR
                assert "Great job" in assessment.feedback_message
    
    @pytest.mark.asyncio
    async def test_assess_pronunciation_recognition_failure(self, speech_service):
        """Test pronunciation assessment when speech recognition fails"""
        # Mock failed recognition
        failed_recognition = SpeechRecognitionResult(
            request_id="req-123",
            user_id="child-123",
            engine_used=SpeechRecognitionEngine.WHISPER,
            success=False,
            error_code="API_ERROR"
        )
        
        with patch.object(speech_service, 'recognize_speech', return_value=failed_recognition):
            assessment = await speech_service.assess_pronunciation(
                user_id="child-123",
                audio_data=b"fake_audio",
                target_text="Hello world"
            )
            
            assert assessment.overall_score == 0.0
            assert assessment.pronunciation_level == PronunciationLevel.POOR
            assert "Could not process" in assessment.feedback_message
            assert assessment.speech_quality == SpeechQuality.INAUDIBLE
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, speech_service):
        """Test successful speech synthesis"""
        fake_audio_data = b"fake_synthesized_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=fake_audio_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with patch.object(speech_service, '_get_api_key', return_value="fake_key"):
                request = TextToSpeechRequest(
                    text="Hello, how are you today?",
                    engine=SpeechSynthesisEngine.OPENAI_TTS,
                    child_age=8
                )
                
                result = await speech_service.synthesize_speech(request)
                
                assert result.success is True
                assert result.audio_data == fake_audio_data
                assert result.audio_size_bytes == len(fake_audio_data)
                assert result.engine_used == SpeechSynthesisEngine.OPENAI_TTS
                assert result.voice_used in ["nova", "shimmer", "alloy"]  # Age-appropriate voice
                assert result.audio_duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_text_too_long(self, speech_service):
        """Test speech synthesis with text that's too long"""
        long_text = "A" * 6000  # Exceeds default max length
        
        request = TextToSpeechRequest(
            text=long_text,
            engine=SpeechSynthesisEngine.OPENAI_TTS
        )
        
        result = await speech_service.synthesize_speech(request)
        
        assert result.success is False
        assert result.error_code == "TEXT_TOO_LONG"
        assert "exceeds maximum" in result.error_message
    
    @pytest.mark.asyncio
    async def test_voice_session_management(self, speech_service):
        """Test voice interaction session management"""
        # Start session
        session = await speech_service.start_voice_session(
            user_id="child-123",
            subject=Subject.MATHEMATICS,
            lesson_topic="Addition",
            interaction_type="pronunciation"
        )
        
        assert session.user_id == "child-123"
        assert session.subject == Subject.MATHEMATICS
        assert session.lesson_topic == "Addition"
        assert session.interaction_type == "pronunciation"
        assert session.session_id in speech_service.active_sessions
        
        # Add interaction
        await speech_service.add_session_interaction(
            session.session_id,
            "speech_recognition",
            {
                "success": True,
                "transcript": "two plus two",
                "confidence": 0.9,
                "duration_ms": 2000
            }
        )
        
        session_obj = speech_service.active_sessions[session.session_id]
        assert session_obj.successful_recognitions == 1
        assert session_obj.total_speech_time_ms == 2000
        assert len(session_obj.interactions) == 1
        
        # Add pronunciation assessment
        await speech_service.add_session_interaction(
            session.session_id,
            "pronunciation_assessment",
            {
                "score": 0.85,
                "words_practiced": ["two", "plus", "four"]
            }
        )
        
        assert len(session_obj.pronunciation_scores) == 1
        assert session_obj.pronunciation_scores[0] == 0.85
        assert len(session_obj.words_practiced) == 3
        
        # End session
        summary = await speech_service.end_voice_session(session.session_id)
        
        assert summary["session_id"] == session.session_id
        assert summary["total_interactions"] == 2
        assert summary["recognition_accuracy"] == 1.0  # 1 successful, 0 failed
        assert summary["average_pronunciation_score"] == 0.85
        assert summary["words_practiced_count"] == 3
        assert session.session_id not in speech_service.active_sessions
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, speech_service):
        """Test rate limiting functionality"""
        user_id = "child-123"
        
        # Should allow first request
        allowed = await speech_service._validate_request_rate_limit(user_id)
        assert allowed is True
        
        # Update counter multiple times to simulate rate limit
        for _ in range(speech_service.config.max_requests_per_minute):
            await speech_service._update_rate_limit_counter(user_id)
        
        # Should now be rate limited
        allowed = await speech_service._validate_request_rate_limit(user_id)
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_audio_quality_assessment(self, speech_service):
        """Test audio quality assessment"""
        # Very small audio (poor quality)
        small_audio = b"tiny"
        quality = await speech_service._assess_audio_quality(small_audio, AudioFormat.WAV)
        assert quality <= 0.2
        
        # Normal sized audio (reasonable quality)
        normal_audio = b"A" * 5000
        quality = await speech_service._assess_audio_quality(normal_audio, AudioFormat.WAV)
        assert quality >= 0.5
        
        # Very large audio (potentially noisy)
        large_audio = b"A" * (15 * 1024 * 1024)  # 15MB
        quality = await speech_service._assess_audio_quality(large_audio, AudioFormat.WAV)
        assert quality <= 0.4
    
    def test_word_similarity_calculation(self, speech_service):
        """Test word similarity calculation"""
        # Identical words
        similarity = speech_service._calculate_word_similarity("hello", "hello")
        assert similarity == 1.0
        
        # Very different words
        similarity = speech_service._calculate_word_similarity("hello", "xyz")
        assert similarity < 0.5
        
        # Similar words
        similarity = speech_service._calculate_word_similarity("hello", "helo")
        assert similarity > 0.7
        
        # Empty words
        similarity = speech_service._calculate_word_similarity("", "hello")
        assert similarity == 0.0
    
    @pytest.mark.asyncio
    async def test_text_adaptation_for_age(self, speech_service):
        """Test text adaptation for different ages"""
        original_text = "The mathematical equation demonstrates multiplicative properties."
        
        with patch('tutor.services.speech_service.make_llm_api_call') as mock_llm:
            mock_llm_response = Mock()
            mock_llm_response.choices = [Mock()]
            mock_llm_response.choices[0].message.content = "This math problem shows how we multiply numbers."
            mock_llm.return_value = mock_llm_response
            
            adapted_text = await speech_service._adapt_text_for_age(
                original_text, 
                child_age=6, 
                subject=Subject.MATHEMATICS
            )
            
            assert adapted_text == "This math problem shows how we multiply numbers."
            
            # Verify LLM was called with appropriate context
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            messages = call_args[1]["messages"]
            
            assert any("6-year-old" in msg["content"] for msg in messages)
            assert any("mathematics" in msg["content"].lower() for msg in messages)
    
    @pytest.mark.asyncio
    async def test_voice_selection_for_context(self, speech_service):
        """Test voice selection based on context"""
        # Young child
        request = TextToSpeechRequest(text="Hello", child_age=6)
        voice = await speech_service._select_voice_for_context(request)
        assert voice == "nova"  # Soft voice for young children
        
        # Female preference
        request = TextToSpeechRequest(text="Hello", gender="female")
        voice = await speech_service._select_voice_for_context(request)
        assert voice == "shimmer"
        
        # Male preference
        request = TextToSpeechRequest(text="Hello", gender="male")
        voice = await speech_service._select_voice_for_context(request)
        assert voice == "onyx"
        
        # Default neutral
        request = TextToSpeechRequest(text="Hello")
        voice = await speech_service._select_voice_for_context(request)
        assert voice == "alloy"
    
    @pytest.mark.asyncio
    async def test_improvement_tips_generation(self, speech_service):
        """Test improvement tips generation"""
        # Poor pronunciation assessment
        assessment = PronunciationAssessment(
            user_id="child-123",
            target_text="hello world",
            overall_score=0.4,
            missing_words=["world"],
            fluency_score=0.3
        )
        
        tips = await speech_service._generate_improvement_tips(assessment, child_age=7)
        
        assert len(tips) <= 3
        assert any("slowly" in tip.lower() for tip in tips)
        assert any("words" in tip.lower() for tip in tips)
        assert any("breathe" in tip.lower() or "voice" in tip.lower() for tip in tips)  # Age-appropriate for 7-year-old
    
    @pytest.mark.asyncio
    async def test_practice_suggestions_generation(self, speech_service):
        """Test practice suggestions generation"""
        assessment = PronunciationAssessment(
            user_id="child-123",
            target_text="hello world",
            overall_score=0.7
        )
        
        # Mathematics subject
        suggestions = await speech_service._generate_practice_suggestions(assessment, Subject.MATHEMATICS)
        assert len(suggestions) <= 3
        assert any("math" in suggestion.lower() for suggestion in suggestions)
        
        # Science subject
        suggestions = await speech_service._generate_practice_suggestions(assessment, Subject.SCIENCE)
        assert len(suggestions) <= 3
        assert any("science" in suggestion.lower() for suggestion in suggestions)
        
        # ESL subject
        suggestions = await speech_service._generate_practice_suggestions(assessment, Subject.ESL)
        assert len(suggestions) <= 3
        assert any("english" in suggestion.lower() for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_pronunciation_analysis(self, speech_service):
        """Test pronunciation analysis logic"""
        word_confidences = [
            WordConfidence(word="hello", confidence=0.9, start_time=0.0, end_time=0.5),
            WordConfidence(word="world", confidence=0.8, start_time=0.6, end_time=1.2)
        ]
        
        assessment = await speech_service._analyze_pronunciation(
            target_text="hello world",
            spoken_text="hello world",
            word_confidences=word_confidences,
            child_age=8,
            subject=Subject.ESL
        )
        
        assert assessment.target_text == "hello world"
        assert assessment.spoken_text == "hello world"
        assert assessment.overall_score > 0.8  # Perfect match should score high
        assert assessment.completeness_score == 1.0  # All words spoken
        assert len(assessment.word_assessments) == 2
        assert len(assessment.missing_words) == 0
        assert len(assessment.extra_words) == 0
        
        # Test with missing word
        assessment = await speech_service._analyze_pronunciation(
            target_text="hello beautiful world",
            spoken_text="hello world",
            word_confidences=word_confidences,
            child_age=8
        )
        
        assert assessment.completeness_score < 1.0
        assert "beautiful" in assessment.missing_words
        assert assessment.overall_score < 0.8  # Should be lower due to missing word
    
    @pytest.mark.asyncio
    async def test_error_handling_in_speech_recognition(self, speech_service):
        """Test error handling in speech recognition"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Simulate API error
            mock_post.side_effect = Exception("API connection failed")
            
            with patch.object(speech_service, '_get_api_key', return_value="fake_key"):
                request = SpeechRecognitionRequest(
                    user_id="child-123",
                    audio_data=b"fake_audio_data",
                    audio_format=AudioFormat.WAV
                )
                
                result = await speech_service.recognize_speech(request)
                
                assert result.success is False
                assert result.error_code == "PROCESSING_ERROR"
                assert "Speech recognition failed" in result.error_message
                assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_in_speech_synthesis(self, speech_service):
        """Test error handling in speech synthesis"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Simulate API error
            mock_post.side_effect = Exception("Synthesis API failed")
            
            with patch.object(speech_service, '_get_api_key', return_value="fake_key"):
                request = TextToSpeechRequest(
                    text="Hello world",
                    engine=SpeechSynthesisEngine.OPENAI_TTS
                )
                
                result = await speech_service.synthesize_speech(request)
                
                assert result.success is False
                assert result.error_code == "SYNTHESIS_ERROR"
                assert "Speech synthesis failed" in result.error_message
                assert len(result.audio_data) == 0
    
    @pytest.mark.asyncio
    async def test_session_not_found_error(self, speech_service):
        """Test error handling when session is not found"""
        with pytest.raises(ValueError) as exc_info:
            await speech_service.end_voice_session("nonexistent-session")
        
        assert "Session" in str(exc_info.value)
        assert "not found" in str(exc_info.value)