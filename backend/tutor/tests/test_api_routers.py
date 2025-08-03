"""
Integration tests for API routers - Task 10.1 and 10.2 implementation
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone

from services.supabase import DBConnection
from ..api import router as tutor_router, initialize


class TestAPIRouters:
    """Integration tests for all API routers"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with tutor router"""
        app = FastAPI()
        app.include_router(tutor_router, prefix="/tutor")
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = AsyncMock(spec=DBConnection)
        return db
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token"}
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_db):
        """Setup global mocks"""
        # Initialize with mock database
        initialize(mock_db)
        
        # Mock authentication
        with patch('utils.auth_utils.get_current_user_id_from_jwt', return_value="test_user_123"):
            yield

    def test_tutor_health_check(self, client):
        """Test tutor service health check"""
        response = client.get("/tutor/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "cambridge_ai_tutor"
        assert "components" in data
        assert "capabilities" in data
        
        # Check all components are active
        components = data["components"]
        expected_components = [
            "ai_tutor", "progress_tracking", "content_management",
            "synchronization", "parent_guidance", "translation",
            "gamification", "speech", "authentication", "websocket"
        ]
        
        for component in expected_components:
            assert component in components
            assert components[component] == "active"

    def test_ai_tutor_endpoints(self, client, auth_headers):
        """Test AI tutor endpoints"""
        # Test ask question endpoint
        with patch('backend.tutor.services.tutor_service.TutorService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.ask_question.return_value = {
                "response_id": "test_response_123",
                "content": "This is a test response",
                "explanation_level": "age_appropriate",
                "confidence_score": 0.9
            }
            
            question_data = {
                "question": "What is 2 + 2?",
                "subject": "mathematics",
                "grade_level": 3
            }
            
            response = client.post(
                "/tutor/ai/ask",
                json=question_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "This is a test response"
            assert data["confidence_score"] == 0.9

    def test_progress_tracking_endpoints(self, client, auth_headers):
        """Test progress tracking endpoints"""
        # Test activity tracking
        with patch('backend.tutor.services.activity_tracking_service.ActivityTrackingService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.track_learning_activity.return_value = {
                "activity_id": "activity_123",
                "performance_impact": "positive"
            }
            
            activity_data = {
                "activity_type": "question_answered",
                "subject": "mathematics",
                "performance_score": 0.85,
                "time_spent_minutes": 10
            }
            
            response = client.post(
                "/tutor/progress/activity",
                json=activity_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["activity_id"] == "activity_123"

    def test_content_management_endpoints(self, client, auth_headers):
        """Test content management endpoints"""
        # Test content search
        with patch('backend.tutor.services.content_service.ContentService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.search_content.return_value = {
                "results": [
                    {
                        "content_id": "content_123",
                        "title": "Test Content",
                        "subject": "mathematics",
                        "grade_level": 3
                    }
                ],
                "total_count": 1
            }
            
            search_data = {
                "query": "addition",
                "subject": "mathematics",
                "grade_level": 3,
                "max_results": 10
            }
            
            response = client.post(
                "/tutor/content/search",
                json=search_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 1
            assert data["results"][0]["title"] == "Test Content"

    def test_synchronization_endpoints(self, client, auth_headers):
        """Test synchronization endpoints"""
        # Test device sync
        with patch('backend.tutor.services.sync_service.SyncService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.sync_user_data.return_value = {
                "sync_id": "sync_123",
                "status": "completed",
                "conflicts_resolved": 0,
                "operations_processed": 5
            }
            
            sync_data = {
                "device_id": "device_123",
                "device_info": {
                    "platform": "web",
                    "version": "1.0.0"
                },
                "include_offline_queue": True
            }
            
            response = client.post(
                "/tutor/sync/sync",
                json=sync_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["sync_id"] == "sync_123"
            assert data["sync_status"] == "completed"

    def test_parent_guidance_endpoints(self, client, auth_headers):
        """Test parent guidance endpoints"""
        # Test FAQ search
        with patch('backend.tutor.services.parent_guidance_service.ParentGuidanceService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.search_faq.return_value = [
                {
                    "faq_id": "faq_123",
                    "question": "How to help with math?",
                    "answer": "Use visual aids and real examples",
                    "category": "learning_support"
                }
            ]
            
            search_data = {
                "query": "help with math",
                "category": "learning_support",
                "max_results": 5
            }
            
            response = client.post(
                "/tutor/guidance/faq/search",
                json=search_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["question"] == "How to help with math?"

    def test_translation_endpoints(self, client, auth_headers):
        """Test translation endpoints"""
        # Test content translation
        with patch('backend.tutor.services.translation_service.TranslationService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.translate_content.return_value = {
                "request_id": "trans_123",
                "translated_content": "Su hijo ha progresado bien",
                "confidence_score": 0.95,
                "cultural_adaptations": ["Formal tone for Spanish parents"]
            }
            
            translation_data = {
                "content": "Your child has progressed well",
                "target_language": "es",
                "content_type": "progress_report"
            }
            
            response = client.post(
                "/tutor/translation/translate",
                json=translation_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["translated_content"] == "Su hijo ha progresado bien"
            assert data["confidence_score"] == 0.95

    def test_gamification_endpoints(self, client, auth_headers):
        """Test gamification endpoints"""
        # Test achievement tracking
        with patch('backend.tutor.services.gamification_service.GamificationService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.track_achievement.return_value = {
                "achievement_id": "achievement_123",
                "points_earned": 10,
                "badges_unlocked": ["first_question"]
            }
            
            achievement_data = {
                "achievement_type": "question_answered",
                "activity_data": {
                    "subject": "mathematics",
                    "correct": True
                }
            }
            
            response = client.post(
                "/tutor/gamification/achievements",
                json=achievement_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["points_earned"] == 10

    def test_authentication_endpoints(self, client, auth_headers):
        """Test authentication endpoints"""
        # Test parental consent verification
        with patch('backend.tutor.services.safety_service.SafetyService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.verify_parental_consent.return_value = True
            
            consent_data = {
                "child_id": "child_123",
                "consent_type": "data_collection",
                "action": "create_profile"
            }
            
            response = client.post(
                "/tutor/auth/consent/verify",
                json=consent_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["consent_verified"] is True

    def test_error_handling(self, client, auth_headers):
        """Test error handling across endpoints"""
        # Test with invalid authentication
        response = client.post("/tutor/ai/ask", json={"question": "test"})
        assert response.status_code == 422  # Validation error without auth

    def test_endpoint_validation(self, client, auth_headers):
        """Test request validation across endpoints"""
        # Test invalid question request
        invalid_data = {
            "question": "",  # Empty question should fail validation
            "grade_level": 15  # Invalid grade level
        }
        
        response = client.post(
            "/tutor/ai/ask",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error


class TestWebSocketEndpoints:
    """Tests for WebSocket functionality - Task 10.2"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with WebSocket router"""
        app = FastAPI()
        app.include_router(tutor_router, prefix="/tutor")
        return app
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return AsyncMock(spec=DBConnection)
    
    @pytest.fixture(autouse=True)
    def setup_websocket_mocks(self, mock_db):
        """Setup WebSocket mocks"""
        initialize(mock_db)
        
        # Mock WebSocket authentication
        with patch('backend.tutor.api_routers.websocket_router.get_user_from_websocket_token', 
                  return_value="test_user_123"):
            yield

    def test_websocket_tutoring_connection(self, app):
        """Test WebSocket tutoring endpoint connection"""
        with TestClient(app) as client:
            # Mock connection manager
            with patch('backend.tutor.api_routers.websocket_router.connection_manager') as mock_manager:
                mock_manager.register_connection.return_value = True
                mock_manager.unregister_connection.return_value = None
                
                # Test WebSocket connection
                with client.websocket_connect("/tutor/ws/tutoring?token=test_token&device_id=test_device") as websocket:
                    # Should receive welcome message
                    data = websocket.receive_json()
                    assert data["message_type"] == "user_joined"
                    assert "Connected to tutoring session" in data["data"]["message"]
                    
                    # Send test message
                    test_message = {
                        "message_type": "tutor_question",
                        "type": "question",
                        "question": "What is 2 + 2?",
                        "question_id": "test_q_123"
                    }
                    websocket.send_json(test_message)
                    
                    # Should receive processing acknowledgment
                    ack_data = websocket.receive_json()
                    assert ack_data["message_type"] == "tutor_response"
                    assert ack_data["data"]["status"] == "processing"

    def test_websocket_progress_connection(self, app):
        """Test WebSocket progress monitoring endpoint"""
        with TestClient(app) as client:
            with patch('backend.tutor.api_routers.websocket_router.connection_manager') as mock_manager:
                mock_manager.register_connection.return_value = True
                
                # Mock progress service
                with patch('backend.tutor.services.progress_reporting_service.ProgressReportingService') as mock_service:
                    mock_instance = AsyncMock()
                    mock_service.return_value = mock_instance
                    mock_instance.get_real_time_progress.return_value = {
                        "daily_activities": 5,
                        "current_streak": 3,
                        "subjects_practiced": ["mathematics"]
                    }
                    
                    with client.websocket_connect("/tutor/ws/progress?token=test_token&device_id=test_device") as websocket:
                        # Should receive welcome with current progress
                        data = websocket.receive_json()
                        assert data["message_type"] == "progress_update"
                        assert "current_progress" in data["data"]

    def test_websocket_message_handling(self, app):
        """Test WebSocket message type handling"""
        with TestClient(app) as client:
            with patch('backend.tutor.api_routers.websocket_router.connection_manager') as mock_manager:
                mock_manager.register_connection.return_value = True
                
                with client.websocket_connect("/tutor/ws/tutoring?token=test_token&device_id=test_device") as websocket:
                    # Skip welcome message
                    websocket.receive_json()
                    
                    # Test heartbeat
                    heartbeat_message = {
                        "message_type": "heartbeat"
                    }
                    websocket.send_json(heartbeat_message)
                    
                    response = websocket.receive_json()
                    assert response["message_type"] == "heartbeat"
                    assert response["data"]["status"] == "alive"
                    
                    # Test unknown message type
                    unknown_message = {
                        "message_type": "unknown_type"
                    }
                    websocket.send_json(unknown_message)
                    
                    error_response = websocket.receive_json()
                    assert error_response["message_type"] == "error"
                    assert "Unknown message type" in error_response["data"]["error"]

    def test_websocket_authentication_failure(self, app):
        """Test WebSocket authentication failure"""
        with patch('backend.tutor.api_routers.websocket_router.get_user_from_websocket_token', 
                  return_value=None):
            
            with TestClient(app) as client:
                # Should close connection with auth failure
                with pytest.raises(Exception):  # WebSocket will raise exception on close
                    with client.websocket_connect("/tutor/ws/tutoring?token=invalid_token&device_id=test_device"):
                        pass

    def test_websocket_sync_operations(self, app):
        """Test WebSocket synchronization operations"""
        with TestClient(app) as client:
            with patch('backend.tutor.api_routers.websocket_router.connection_manager') as mock_manager:
                mock_manager.register_connection.return_value = True
                
                with patch('backend.tutor.api_routers.websocket_router.realtime_updater') as mock_updater:
                    mock_updater.process_real_time_sync.return_value = {
                        "sync_status": "completed",
                        "operations_synced": 3
                    }
                    
                    with client.websocket_connect("/tutor/ws/tutoring?token=test_token&device_id=test_device") as websocket:
                        # Skip welcome message
                        websocket.receive_json()
                        
                        # Send sync operation
                        sync_message = {
                            "message_type": "device_sync",
                            "type": "device_sync",
                            "device_id": "test_device",
                            "sync_data": {
                                "user_preferences": {"theme": "dark"},
                                "progress_data": {"last_activity": "2025-01-03"}
                            }
                        }
                        websocket.send_json(sync_message)
                        
                        # Should receive sync confirmation
                        response = websocket.receive_json()
                        assert response["message_type"] == "device_sync"
                        assert response["data"]["status"] == "synced"


class TestAPIIntegration:
    """Integration tests between different API components"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app"""
        app = FastAPI()
        app.include_router(tutor_router, prefix="/tutor")
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token"}
    
    @pytest.fixture(autouse=True)
    def setup_integration_mocks(self):
        """Setup integration test mocks"""
        mock_db = AsyncMock(spec=DBConnection)
        initialize(mock_db)
        
        with patch('utils.auth_utils.get_current_user_id_from_jwt', return_value="test_user_123"):
            yield

    def test_full_tutoring_workflow(self, client, auth_headers):
        """Test complete tutoring workflow across multiple endpoints"""
        # 1. Ask a question
        with patch('backend.tutor.services.tutor_service.TutorService') as mock_tutor:
            mock_tutor_instance = AsyncMock()
            mock_tutor.return_value = mock_tutor_instance
            mock_tutor_instance.ask_question.return_value = {
                "response_id": "response_123",
                "content": "2 + 2 equals 4",
                "confidence_score": 0.95
            }
            
            question_response = client.post(
                "/tutor/ai/ask",
                json={
                    "question": "What is 2 + 2?",
                    "subject": "mathematics",
                    "grade_level": 3
                },
                headers=auth_headers
            )
            assert question_response.status_code == 200
        
        # 2. Track the activity
        with patch('backend.tutor.services.activity_tracking_service.ActivityTrackingService') as mock_activity:
            mock_activity_instance = AsyncMock()
            mock_activity.return_value = mock_activity_instance
            mock_activity_instance.track_learning_activity.return_value = {
                "activity_id": "activity_123",
                "performance_impact": "positive"
            }
            
            activity_response = client.post(
                "/tutor/progress/activity",
                json={
                    "activity_type": "question_answered",
                    "subject": "mathematics",
                    "performance_score": 0.95
                },
                headers=auth_headers
            )
            assert activity_response.status_code == 200
        
        # 3. Generate progress report
        with patch('backend.tutor.services.progress_reporting_service.ProgressReportingService') as mock_progress:
            mock_progress_instance = AsyncMock()
            mock_progress.return_value = mock_progress_instance
            mock_progress_instance.generate_progress_report.return_value = MagicMock(
                report_id="report_123",
                child_id="test_user_123",
                child_name="Test Child",
                child_age=8,
                child_grade=3,
                timeframe="weekly",
                generated_at=datetime.now(timezone.utc),
                overall_progress_score=0.85,
                total_activities_completed=10,
                learning_streak_days=5,
                subjects_practiced=["mathematics"],
                subject_progress={},
                weekly_activity=[],
                achievements=[],
                areas_for_focus=[],
                parent_summary="Great progress!",
                next_steps=[]
            )
            mock_progress_instance.generate_parent_insights.return_value = []
            
            progress_response = client.post(
                "/tutor/progress/reports",
                json={
                    "child_id": "test_user_123",
                    "timeframe": "weekly",
                    "include_insights": True
                },
                headers=auth_headers
            )
            assert progress_response.status_code == 200

    def test_cross_platform_sync_workflow(self, client, auth_headers):
        """Test cross-platform synchronization workflow"""
        # 1. Register device
        with patch('backend.tutor.services.sync_service.SyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            mock_sync_instance.register_device.return_value = {
                "device_token": "token_123"
            }
            
            register_response = client.post(
                "/tutor/sync/devices/register",
                json={
                    "device_id": "device_123",
                    "device_type": "web",
                    "platform_info": {"browser": "chrome", "version": "96"}
                },
                headers=auth_headers
            )
            assert register_response.status_code == 200
        
        # 2. Sync data
        with patch('backend.tutor.services.sync_service.SyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            mock_sync_instance.sync_user_data.return_value = {
                "sync_id": "sync_123",
                "status": "completed",
                "conflicts_resolved": 0,
                "operations_processed": 5
            }
            
            sync_response = client.post(
                "/tutor/sync/sync",
                json={
                    "device_id": "device_123",
                    "device_info": {"platform": "web"},
                    "include_offline_queue": True
                },
                headers=auth_headers
            )
            assert sync_response.status_code == 200

    def test_multilingual_parent_support_workflow(self, client, auth_headers):
        """Test multilingual parent support workflow"""
        # 1. Search FAQ
        with patch('backend.tutor.services.parent_guidance_service.ParentGuidanceService') as mock_guidance:
            mock_guidance_instance = AsyncMock()
            mock_guidance.return_value = mock_guidance_instance
            mock_guidance_instance.search_faq.return_value = [
                MagicMock(
                    faq_id="faq_123",
                    question="How to help with math?",
                    answer="Use visual aids",
                    category="learning_support"
                )
            ]
            
            faq_response = client.post(
                "/tutor/guidance/faq/search",
                json={
                    "query": "help with math",
                    "category": "learning_support"
                },
                headers=auth_headers
            )
            assert faq_response.status_code == 200
        
        # 2. Translate content
        with patch('backend.tutor.services.translation_service.TranslationService') as mock_translation:
            mock_translation_instance = AsyncMock()
            mock_translation.return_value = mock_translation_instance
            mock_translation_instance.translate_content.return_value = MagicMock(
                request_id="trans_123",
                translated_content="Utiliza ayudas visuales",
                confidence_score=0.95,
                cultural_adaptations=["Formal tone"]
            )
            
            translation_response = client.post(
                "/tutor/translation/translate",
                json={
                    "content": "Use visual aids",
                    "target_language": "es",
                    "content_type": "guidance"
                },
                headers=auth_headers
            )
            assert translation_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])