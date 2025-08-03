"""
Tutor API Router - AI tutoring interactions and explanations
Task 10.1 implementation - Requirements: 1.3, 2.3
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime, timezone
import json

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.tutor_service import TutorService
from ..services.curriculum_aligner import CurriculumAligner
from ..services.personalization_engine import PersonalizationEngine
from ..services.content_service import ContentService
from ..models.user_models import Subject

router = APIRouter(prefix="/ai", tags=["AI Tutor"])

# Pydantic models for API requests/responses
class TutorQuestionRequest(BaseModel):
    """Request model for asking tutor questions"""
    question: str = Field(min_length=1, max_length=1000, description="The question to ask the AI tutor")
    subject: Optional[Subject] = Field(None, description="Subject area for contextualized responses")
    grade_level: Optional[int] = Field(None, ge=1, le=12, description="Grade level for age-appropriate responses")
    learning_style: Optional[str] = Field(None, description="Preferred learning style (visual, auditory, kinesthetic)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for the question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Question cannot be empty')
        return v.strip()

class ConceptExplanationRequest(BaseModel):
    """Request model for concept explanations"""
    concept_id: Optional[str] = Field(None, description="Specific concept ID from curriculum")
    concept_name: str = Field(min_length=1, max_length=200, description="Name of the concept to explain")
    difficulty_level: int = Field(ge=1, le=5, description="Difficulty level (1=beginner, 5=advanced)")
    learning_style: str = Field(default="visual", description="Preferred learning style")
    age: Optional[int] = Field(None, ge=5, le=12, description="Child's age for appropriate explanation")

class PracticeProblemsRequest(BaseModel):
    """Request model for generating practice problems"""
    topic_id: str = Field(description="Curriculum topic ID")
    count: int = Field(ge=1, le=10, description="Number of problems to generate")
    difficulty: int = Field(ge=1, le=5, description="Difficulty level")
    problem_type: Optional[str] = Field(None, description="Type of problems (multiple_choice, open_ended, etc.)")

class FeedbackRequest(BaseModel):
    """Request model for answer feedback"""
    answer: str = Field(min_length=1, description="Student's answer")
    expected_answer: Optional[str] = Field(None, description="Expected answer for comparison")
    question_context: Dict[str, Any] = Field(description="Context about the original question")
    assessment_type: str = Field(default="formative", description="Type of assessment")

class TutorResponse(BaseModel):
    """Response model for tutor interactions"""
    response_id: str = Field(description="Unique response identifier")
    content: str = Field(description="Main response content")
    explanation_level: str = Field(description="Level of explanation provided")
    curriculum_alignment: Optional[str] = Field(None, description="Cambridge curriculum alignment")
    visual_aids: List[str] = Field(default_factory=list, description="URLs or descriptions of visual aids")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence in the response")
    personalization_notes: Optional[str] = Field(None, description="Notes about personalization applied")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConceptExplanation(BaseModel):
    """Response model for concept explanations"""
    explanation_id: str = Field(description="Unique explanation identifier")
    concept_name: str = Field(description="Name of the explained concept")
    explanation: str = Field(description="Detailed explanation content")
    examples: List[str] = Field(default_factory=list, description="Practical examples")
    visual_elements: List[Dict[str, str]] = Field(default_factory=list, description="Visual aids and diagrams")
    difficulty_level: int = Field(description="Difficulty level of explanation")
    prerequisite_concepts: List[str] = Field(default_factory=list, description="Required prior knowledge")
    next_concepts: List[str] = Field(default_factory=list, description="What to learn next")
    curriculum_alignment: Optional[str] = Field(None, description="Cambridge curriculum code")

class PracticeProblem(BaseModel):
    """Model for individual practice problems"""
    problem_id: str = Field(description="Unique problem identifier")
    question: str = Field(description="Problem question")
    problem_type: str = Field(description="Type of problem")
    difficulty: int = Field(description="Difficulty level")
    expected_answer: str = Field(description="Correct answer")
    solution_steps: List[str] = Field(default_factory=list, description="Step-by-step solution")
    hints: List[str] = Field(default_factory=list, description="Helpful hints")
    curriculum_alignment: Optional[str] = Field(None, description="Cambridge curriculum code")

class PracticeProblemsResponse(BaseModel):
    """Response model for practice problems"""
    problems: List[PracticeProblem] = Field(description="Generated practice problems")
    topic_id: str = Field(description="Topic these problems relate to")
    total_count: int = Field(description="Total number of problems generated")
    difficulty_distribution: Dict[str, int] = Field(default_factory=dict, description="Count by difficulty level")

class FeedbackResponse(BaseModel):
    """Response model for answer feedback"""
    feedback_id: str = Field(description="Unique feedback identifier")
    correctness_score: float = Field(ge=0.0, le=1.0, description="How correct the answer is")
    feedback_content: str = Field(description="Detailed feedback text")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    encouragement: str = Field(description="Encouraging message")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Specific areas to work on")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next learning steps")

# Dependency to get initialized services
async def get_tutor_service() -> TutorService:
    """Get initialized tutor service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return TutorService(db)

async def get_content_service() -> ContentService:
    """Get initialized content service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return ContentService(db)

# API Endpoints
@router.post("/ask", response_model=TutorResponse)
async def ask_tutor_question(
    request: TutorQuestionRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    Ask the AI tutor a question and get a curriculum-aligned response
    Requirement 1.3: Respond within 3 seconds with contextually relevant information
    """
    try:
        logger.info(f"Processing tutor question for user {user_id}: {request.question[:50]}...")
        
        # Prepare context for the tutor service
        context = request.context.copy()
        context.update({
            "user_id": user_id,
            "subject": request.subject.value if request.subject else None,
            "grade_level": request.grade_level,
            "learning_style": request.learning_style,
            "session_id": request.session_id
        })
        
        # Call the tutor service
        tutor_response = await tutor_service.ask_question(
            user_id=user_id,
            question=request.question,
            context=context
        )
        
        # Convert service response to API response
        response = TutorResponse(
            response_id=tutor_response.get("response_id", str(uuid.uuid4())),
            content=tutor_response.get("content", ""),
            explanation_level=tutor_response.get("explanation_level", "age_appropriate"),
            curriculum_alignment=tutor_response.get("curriculum_alignment"),
            visual_aids=tutor_response.get("visual_aids", []),
            follow_up_questions=tutor_response.get("follow_up_questions", []),
            confidence_score=tutor_response.get("confidence_score", 0.8),
            personalization_notes=tutor_response.get("personalization_notes"),
            session_id=tutor_response.get("session_id")
        )
        
        logger.info(f"Tutor question processed successfully for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing tutor question for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process tutor question")

@router.post("/explain", response_model=ConceptExplanation)
async def explain_concept(
    request: ConceptExplanationRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    Get a detailed explanation of a specific concept
    Requirement 1.4: Break down concepts into simpler, prerequisite steps
    """
    try:
        logger.info(f"Generating concept explanation for user {user_id}: {request.concept_name}")
        
        # Call the tutor service for concept explanation
        explanation_data = await tutor_service.explain_concept(
            concept_id=request.concept_id,
            concept_name=request.concept_name,
            difficulty_level=request.difficulty_level,
            learning_style=request.learning_style,
            age=request.age,
            user_id=user_id
        )
        
        # Convert to API response
        explanation = ConceptExplanation(
            explanation_id=explanation_data.get("explanation_id", str(uuid.uuid4())),
            concept_name=request.concept_name,
            explanation=explanation_data.get("explanation", ""),
            examples=explanation_data.get("examples", []),
            visual_elements=explanation_data.get("visual_elements", []),
            difficulty_level=request.difficulty_level,
            prerequisite_concepts=explanation_data.get("prerequisite_concepts", []),
            next_concepts=explanation_data.get("next_concepts", []),
            curriculum_alignment=explanation_data.get("curriculum_alignment")
        )
        
        logger.info(f"Concept explanation generated successfully for user {user_id}")
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating concept explanation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate concept explanation")

@router.post("/practice", response_model=PracticeProblemsResponse)
async def generate_practice_problems(
    request: PracticeProblemsRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    Generate practice problems for a specific topic
    Requirement 1.2: Offer alternative explanations using different teaching approaches
    """
    try:
        logger.info(f"Generating practice problems for user {user_id}: topic {request.topic_id}")
        
        # Call the tutor service for practice problem generation
        problems_data = await tutor_service.generate_practice_problems(
            topic_id=request.topic_id,
            count=request.count,
            difficulty=request.difficulty,
            problem_type=request.problem_type,
            user_id=user_id
        )
        
        # Convert to API response
        problems = []
        for problem_data in problems_data.get("problems", []):
            problem = PracticeProblem(
                problem_id=problem_data.get("problem_id", str(uuid.uuid4())),
                question=problem_data.get("question", ""),
                problem_type=problem_data.get("problem_type", "open_ended"),
                difficulty=problem_data.get("difficulty", request.difficulty),
                expected_answer=problem_data.get("expected_answer", ""),
                solution_steps=problem_data.get("solution_steps", []),
                hints=problem_data.get("hints", []),
                curriculum_alignment=problem_data.get("curriculum_alignment")
            )
            problems.append(problem)
        
        response = PracticeProblemsResponse(
            problems=problems,
            topic_id=request.topic_id,
            total_count=len(problems),
            difficulty_distribution=problems_data.get("difficulty_distribution", {})
        )
        
        logger.info(f"Practice problems generated successfully for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating practice problems for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate practice problems")

@router.post("/feedback", response_model=FeedbackResponse)
async def provide_answer_feedback(
    request: FeedbackRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    Provide feedback on a student's answer
    Requirement 1.5: Use vocabulary appropriate for the child's age group
    """
    try:
        logger.info(f"Providing answer feedback for user {user_id}")
        
        # Call the tutor service for feedback
        feedback_data = await tutor_service.provide_feedback(
            answer=request.answer,
            expected=request.expected_answer,
            context=request.question_context,
            assessment_type=request.assessment_type,
            user_id=user_id
        )
        
        # Convert to API response
        feedback = FeedbackResponse(
            feedback_id=feedback_data.get("feedback_id", str(uuid.uuid4())),
            correctness_score=feedback_data.get("correctness_score", 0.5),
            feedback_content=feedback_data.get("feedback_content", ""),
            suggestions=feedback_data.get("suggestions", []),
            encouragement=feedback_data.get("encouragement", "Keep up the good work!"),
            areas_for_improvement=feedback_data.get("areas_for_improvement", []),
            next_steps=feedback_data.get("next_steps", [])
        )
        
        logger.info(f"Answer feedback provided successfully for user {user_id}")
        return feedback
        
    except Exception as e:
        logger.error(f"Error providing answer feedback for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to provide answer feedback")

@router.get("/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    Get conversation context for a tutoring session
    Requirement 2.3: Maintain session continuity and current learning context
    """
    try:
        logger.info(f"Retrieving session context for user {user_id}, session {session_id}")
        
        # Get session context from tutor service
        context_data = await tutor_service.get_session_context(session_id, user_id)
        
        logger.info(f"Session context retrieved successfully for user {user_id}")
        return {
            "session_id": session_id,
            "context": context_data,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving session context for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session context")

@router.delete("/sessions/{session_id}")
async def end_tutoring_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    tutor_service: TutorService = Depends(get_tutor_service)
):
    """
    End a tutoring session and clean up resources
    """
    try:
        logger.info(f"Ending tutoring session for user {user_id}, session {session_id}")
        
        # End session in tutor service
        await tutor_service.end_session(session_id, user_id)
        
        logger.info(f"Tutoring session ended successfully for user {user_id}")
        return {
            "message": "Session ended successfully",
            "session_id": session_id,
            "ended_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error ending tutoring session for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end tutoring session")

@router.get("/health")
async def tutor_health_check():
    """Health check endpoint for AI tutor service"""
    return {
        "status": "ok",
        "service": "ai_tutor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": [
            "question_answering",
            "concept_explanation", 
            "practice_generation",
            "answer_feedback",
            "session_management"
        ]
    }