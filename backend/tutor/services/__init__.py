# Tutor Services Module

# Import only the services that don't have dependency issues for testing
try:
    from .content_service import ContentService
    from .tutor_service import TutorService
    from .cambridge_alignment_service import CambridgeAlignmentService
    from .curriculum_aligner import CurriculumAligner
    from .personalization_engine import PersonalizationEngine
    from .activity_tracking_service import ActivityTrackingService
    from .progress_reporting_service import ProgressReportingService
    from .speech_service import SpeechService
    from .gamification_service import GamificationService
    from .adaptive_gamification_service import AdaptiveGamificationService
    from .sync_service import SyncService
    from .realtime_sync_service import RealtimeSyncService
    from .data_versioning_service import DataVersioningService
    __all__ = [
        "ContentService",
        "TutorService", 
        "CambridgeAlignmentService",
        "CurriculumAligner",
        "PersonalizationEngine",
        "ActivityTrackingService",
        "ProgressReportingService",
        "SpeechService",
        "GamificationService",
        "AdaptiveGamificationService",
        "SyncService",
        "RealtimeSyncService",
        "DataVersioningService"
    ]
except ImportError:
    # For testing environments where some dependencies might not be available
    __all__ = []