"""
AI Tutor Service - Core tutoring functionality with LLM integration
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import json

from utils.logger import logger
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from ..repositories.user_repository import ChildProfileRepository
from ..repositories.curriculum_repository import CurriculumTopicRepository
from ..models.user_models import Subject, LearningStyle
from ..models.curriculum_models import DifficultyLevel
from .cambridge_alignment_service import CambridgeAlignmentService
from .curriculum_aligner import CurriculumAligner
from .personalization_engine import PersonalizationEngine


class ConversationContext:
    """Manages conversation context for multi-turn interactions"""
    
    def __init__(self, user_id: str, session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: List[Dict[str, Any]] = []
        self.learning_context: Dict[str, Any] = {}
        self.current_topic: Optional[str] = None
        self.difficulty_level: int = 1
        self.learning_style: str = "mixed"
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add a user message to the conversation"""
        message = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.last_updated = datetime.now(timezone.utc)
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add an assistant message to the conversation"""
        message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.last_updated = datetime.now(timezone.utc)
    
    def get_recent_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent messages formatted for LLM"""
        recent_messages = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    def update_learning_context(self, **kwargs):
        """Update learning context parameters"""
        self.learning_context.update(kwargs)
        if "current_topic" in kwargs:
            self.current_topic = kwargs["current_topic"]
        if "difficulty_level" in kwargs:
            self.difficulty_level = kwargs["difficulty_level"]
        if "learning_style" in kwargs:
            self.learning_style = kwargs["learning_style"]
        self.last_updated = datetime.now(timezone.utc)


class TutorService:
    """Core AI tutoring service for Cambridge curriculum with LLM integration"""
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.child_repo = ChildProfileRepository(db)
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.alignment_service = CambridgeAlignmentService(db)
        self.curriculum_aligner = CurriculumAligner(db)
        self.personalization_engine = PersonalizationEngine(db)
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.default_model = "gpt-4"  # Can be configured
        
        # Age-appropriate vocabulary mappings
        self.age_vocabulary = {
            5: {"level": "very_simple", "max_sentence_length": 8, "technical_terms": False},
            6: {"level": "very_simple", "max_sentence_length": 10, "technical_terms": False},
            7: {"level": "simple", "max_sentence_length": 12, "technical_terms": "basic"},
            8: {"level": "simple", "max_sentence_length": 15, "technical_terms": "basic"},
            9: {"level": "intermediate", "max_sentence_length": 18, "technical_terms": "moderate"},
            10: {"level": "intermediate", "max_sentence_length": 20, "technical_terms": "moderate"},
            11: {"level": "advanced", "max_sentence_length": 25, "technical_terms": "advanced"},
            12: {"level": "advanced", "max_sentence_length": 30, "technical_terms": "advanced"}
        }
        
    async def ask_question(self, user_id: str, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a question from a student and generate an appropriate response
        
        Args:
            user_id: ID of the user asking the question
            question: The question text
            context: Additional context (subject, grade level, session_id, etc.)
            
        Returns:
            Dictionary containing the tutor response
        """
        try:
            # Get or create conversation context
            session_id = context.get("session_id")
            conversation = await self._get_or_create_conversation(user_id, session_id)
            
            # Get child profile for personalization
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            if not child_profile:
                raise ValueError(f"Child profile not found for user {user_id}")
            
            # Add user message to conversation
            conversation.add_user_message(question, context)
            
            # Prepare context for LLM
            system_prompt = await self._build_system_prompt(child_profile, context)
            conversation_messages = conversation.get_recent_context(max_messages=20)
            
            # Build messages for LLM
            messages = [{"role": "system", "content": system_prompt}] + conversation_messages
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.default_model,
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse LLM response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                parsed_response = {
                    "content": llm_content,
                    "explanation_level": "age_appropriate",
                    "curriculum_alignment": [],
                    "visual_aids_suggested": [],
                    "follow_up_questions": [],
                    "confidence": 0.8
                }
            
            # Apply curriculum alignment if subject is specified
            aligned_content = parsed_response["content"]
            alignment_data = None
            if context.get("subject"):
                try:
                    subject = Subject(context["subject"].lower())
                    learning_style = LearningStyle(child_profile.get("learning_style", "mixed"))
                    
                    alignment_result = await self.curriculum_aligner.align_explanation(
                        content=parsed_response["content"],
                        subject=subject,
                        grade_level=child_profile["grade_level"],
                        learning_style=learning_style,
                        age=child_profile["age"],
                        topic_id=context.get("topic_id")
                    )
                    
                    aligned_content = alignment_result["aligned_content"]
                    alignment_data = alignment_result
                    
                    # Update curriculum alignment in response
                    parsed_response["curriculum_alignment"] = alignment_result.get("cambridge_codes", [])
                    
                except Exception as e:
                    logger.warning(f"Could not apply curriculum alignment: {str(e)}")
            
            # Apply personalization
            final_content = aligned_content
            personalization_data = None
            try:
                personalization_result = await self.personalization_engine.personalize_response(
                    content=aligned_content,
                    user_id=user_id,
                    context=context
                )
                final_content = personalization_result["personalized_content"]
                personalization_data = personalization_result
            except Exception as e:
                logger.warning(f"Could not apply personalization: {str(e)}")
            
            # Add assistant response to conversation
            conversation.add_assistant_message(final_content)
            
            # Build final response
            tutor_response = {
                "response_id": str(uuid.uuid4()),
                "session_id": conversation.session_id,
                "content": final_content,
                "explanation_level": parsed_response.get("explanation_level", "age_appropriate"),
                "curriculum_alignment": parsed_response.get("curriculum_alignment", []),
                "visual_aids_suggested": parsed_response.get("visual_aids_suggested", []),
                "follow_up_questions": parsed_response.get("follow_up_questions", []),
                "confidence_score": parsed_response.get("confidence", 0.8),
                "response_time": (datetime.now(timezone.utc) - conversation.last_updated).total_seconds(),
                "child_age": child_profile["age"],
                "child_grade": child_profile["grade_level"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # Add personalization and alignment metadata
                "personalization_applied": personalization_data is not None,
                "curriculum_aligned": alignment_data is not None
            }
            
            # Add detailed metadata if available
            if personalization_data:
                tutor_response["personalization_metadata"] = {
                    "adaptations_applied": personalization_data.get("adaptations_applied", []),
                    "difficulty_level": personalization_data.get("difficulty_level", 0),
                    "estimated_completion_time": personalization_data.get("estimated_completion_time", 0)
                }
            
            if alignment_data:
                tutor_response["alignment_metadata"] = {
                    "cambridge_codes": alignment_data.get("cambridge_codes", []),
                    "curriculum_alignment_score": alignment_data.get("curriculum_alignment_score", 0),
                    "learning_style_adaptations": alignment_data.get("learning_style_adaptations", [])
                }
            
            # Update conversation context based on response
            if parsed_response.get("detected_topic"):
                conversation.update_learning_context(
                    current_topic=parsed_response["detected_topic"],
                    last_interaction=datetime.now(timezone.utc).isoformat()
                )
            
            logger.info(f"Question processed for user {user_id} in {tutor_response['response_time']:.2f}s")
            return tutor_response
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            # Return a safe fallback response
            return {
                "response_id": str(uuid.uuid4()),
                "content": "I'm sorry, I'm having trouble understanding your question right now. Could you try asking it in a different way?",
                "explanation_level": "age_appropriate",
                "curriculum_alignment": [],
                "visual_aids_suggested": [],
                "follow_up_questions": ["Could you tell me more about what you're working on?"],
                "confidence_score": 0.1,
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def explain_concept(self, concept_id: str, difficulty_level: int, learning_style: str, 
                             user_id: str = None, age: int = 8) -> Dict[str, Any]:
        """
        Generate an explanation for a specific concept
        
        Args:
            concept_id: ID of the concept to explain
            difficulty_level: Difficulty level (1-5)
            learning_style: Learning style preference (visual, auditory, kinesthetic)
            user_id: Optional user ID for personalization
            age: Child's age for vocabulary adjustment
            
        Returns:
            Dictionary containing the explanation
        """
        try:
            # Get concept information if available
            concept_info = None
            if concept_id:
                try:
                    concept_info = await self.curriculum_repo.get_by_id(concept_id, "topic_id")
                except:
                    # If concept_id is not a topic_id, try it as a general concept identifier
                    pass
            
            # Build system prompt for concept explanation
            vocab_settings = self.age_vocabulary.get(age, self.age_vocabulary[8])
            
            system_prompt = f"""You are an expert tutor explaining concepts to a {age}-year-old child. 

EXPLANATION GUIDELINES:
- Use {vocab_settings['level']} vocabulary appropriate for age {age}
- Maximum {vocab_settings['max_sentence_length']} words per sentence
- Technical terms: {vocab_settings['technical_terms']}
- Learning style: {learning_style}
- Difficulty level: {difficulty_level}/5

RESPONSE FORMAT (JSON):
{{
    "content": "Clear, age-appropriate explanation",
    "key_points": ["Main concepts broken down"],
    "examples": ["Real-world examples"],
    "visual_aids": ["Suggested visual aids for {learning_style} learners"],
    "practice_activities": ["Hands-on activities"],
    "vocabulary": ["Key terms with simple definitions"],
    "confidence": 0.9
}}

For {learning_style} learners, focus on:
{self._get_learning_style_guidance(learning_style)}

Make the explanation engaging and build confidence!"""

            # Prepare messages for LLM
            concept_name = concept_info["title"] if concept_info else concept_id
            user_message = f"Please explain the concept '{concept_name}' at difficulty level {difficulty_level}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.default_model,
                temperature=0.6,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                parsed_response = {
                    "content": llm_content,
                    "key_points": [],
                    "examples": [],
                    "visual_aids": [],
                    "practice_activities": [],
                    "vocabulary": [],
                    "confidence": 0.7
                }
            
            explanation = {
                "explanation_id": str(uuid.uuid4()),
                "concept_id": concept_id,
                "concept_name": concept_name,
                "content": parsed_response["content"],
                "difficulty_level": difficulty_level,
                "learning_style": learning_style,
                "key_points": parsed_response.get("key_points", []),
                "examples": parsed_response.get("examples", []),
                "visual_aids": parsed_response.get("visual_aids", []),
                "practice_activities": parsed_response.get("practice_activities", []),
                "vocabulary": parsed_response.get("vocabulary", []),
                "confidence_score": parsed_response.get("confidence", 0.7),
                "age_targeted": age,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add curriculum alignment if concept found
            if concept_info:
                explanation["curriculum_alignment"] = {
                    "cambridge_code": concept_info.get("cambridge_code"),
                    "subject": concept_info.get("subject"),
                    "grade_level": concept_info.get("grade_level")
                }
            
            logger.info(f"Concept explanation generated for {concept_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating concept explanation: {str(e)}")
            raise
    
    async def generate_practice_problems(self, topic_id: str, count: int, difficulty: int) -> List[Dict[str, Any]]:
        """
        Generate practice problems for a specific topic
        
        Args:
            topic_id: ID of the topic
            count: Number of problems to generate
            difficulty: Difficulty level (1-5)
            
        Returns:
            List of practice problems
        """
        try:
            # TODO: Implement practice problem generation
            # This will be implemented in task 4.2
            
            problems = []
            for i in range(count):
                problem = {
                    "problem_id": str(uuid.uuid4()),
                    "topic_id": topic_id,
                    "question": f"Placeholder practice problem {i+1}",
                    "difficulty": difficulty,
                    "expected_answer": "Placeholder answer",
                    "hints": ["Placeholder hint"]
                }
                problems.append(problem)
            
            logger.info(f"Generated {count} practice problems for topic {topic_id}")
            return problems
            
        except Exception as e:
            logger.error(f"Error generating practice problems: {str(e)}")
            raise
    
    async def provide_feedback(self, answer: str, expected: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide feedback on a student's answer with encouragement and guidance
        
        Args:
            answer: Student's answer
            expected: Expected answer or solution approach
            context: Additional context (user_id, age, subject, difficulty, etc.)
            
        Returns:
            Dictionary containing comprehensive feedback
        """
        try:
            user_id = context.get("user_id")
            age = context.get("age", 8)
            subject = context.get("subject", "general")
            difficulty = context.get("difficulty", 1)
            
            # Get vocabulary settings for age
            vocab_settings = self.age_vocabulary.get(age, self.age_vocabulary[8])
            
            # Build feedback prompt
            system_prompt = f"""You are a supportive AI tutor providing feedback to a {age}-year-old child. Always be encouraging and constructive.

FEEDBACK GUIDELINES:
- Use {vocab_settings['level']} vocabulary for age {age}
- Maximum {vocab_settings['max_sentence_length']} words per sentence
- Always start with encouragement
- Focus on learning, not just being right or wrong
- Provide specific, actionable guidance
- Subject: {subject}, Difficulty: {difficulty}/5

RESPONSE FORMAT (JSON):
{{
    "is_correct": true/false,
    "correctness_score": 0.0-1.0,
    "main_feedback": "Primary encouraging feedback message",
    "explanation": "Why the answer is right/wrong and what to learn",
    "suggestions": ["Specific steps to improve or continue learning"],
    "encouragement": "Motivational message appropriate for age {age}",
    "hints": ["Gentle hints if answer was incorrect"],
    "next_steps": "What to try next or practice",
    "confidence": 0.9
}}

TONE: Always supportive, patient, and focused on growth mindset!"""

            user_message = f"""Student's answer: "{answer}"
Expected answer: "{expected}"
Please provide constructive feedback that helps the child learn."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.default_model,
                temperature=0.5,  # Lower temperature for more consistent feedback
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                # Fallback response
                parsed_response = {
                    "is_correct": self._simple_answer_check(answer, expected),
                    "correctness_score": 0.5,
                    "main_feedback": "Thank you for trying! Let's look at this together.",
                    "explanation": llm_content if llm_content else "Let's work through this step by step.",
                    "suggestions": ["Try thinking about it differently", "Ask for help if you need it"],
                    "encouragement": "You're doing great by trying!",
                    "hints": [],
                    "next_steps": "Keep practicing!",
                    "confidence": 0.6
                }
            
            feedback = {
                "feedback_id": str(uuid.uuid4()),
                "is_correct": parsed_response.get("is_correct", False),
                "correctness_score": parsed_response.get("correctness_score", 0.5),
                "main_feedback": parsed_response.get("main_feedback", "Good effort!"),
                "explanation": parsed_response.get("explanation", ""),
                "suggestions": parsed_response.get("suggestions", []),
                "encouragement": parsed_response.get("encouragement", "Keep trying!"),
                "hints": parsed_response.get("hints", []),
                "next_steps": parsed_response.get("next_steps", ""),
                "student_answer": answer,
                "expected_answer": expected,
                "age_targeted": age,
                "subject": subject,
                "difficulty_level": difficulty,
                "confidence_score": parsed_response.get("confidence", 0.8),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Update conversation context if user_id provided
            if user_id:
                try:
                    conversation = await self._get_or_create_conversation(user_id)
                    conversation.add_assistant_message(f"Feedback: {feedback['main_feedback']}")
                except:
                    # Don't fail feedback if conversation update fails
                    pass
            
            logger.info(f"Feedback generated for answer: {'correct' if feedback['is_correct'] else 'incorrect'}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            # Return encouraging fallback feedback
            return {
                "feedback_id": str(uuid.uuid4()),
                "is_correct": False,
                "correctness_score": 0.5,
                "main_feedback": "I'm having trouble right now, but you're doing great by trying!",
                "explanation": "Let's try again together.",
                "suggestions": ["Take your time", "Try a different approach"],
                "encouragement": "Every mistake is a chance to learn something new!",
                "hints": [],
                "next_steps": "Keep going, you've got this!",
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _simple_answer_check(self, answer: str, expected: str) -> bool:
        """Simple fallback answer checking"""
        if not answer or not expected:
            return False
        
        # Basic similarity check
        answer_clean = answer.lower().strip()
        expected_clean = expected.lower().strip()
        
        # Exact match
        if answer_clean == expected_clean:
            return True
        
        # Contains expected answer
        if expected_clean in answer_clean or answer_clean in expected_clean:
            return True
        
        # For numbers, try parsing and comparing
        try:
            answer_num = float(answer_clean.replace(',', ''))
            expected_num = float(expected_clean.replace(',', ''))
            return abs(answer_num - expected_num) < 0.01
        except:
            pass
        
        return False
    
    async def _get_or_create_conversation(self, user_id: str, session_id: str = None) -> ConversationContext:
        """Get existing conversation or create a new one"""
        conversation_key = session_id or f"{user_id}_default"
        
        if conversation_key in self.active_conversations:
            conversation = self.active_conversations[conversation_key]
            # Check if conversation is too old (older than 24 hours)
            if (datetime.now(timezone.utc) - conversation.last_updated).hours > 24:
                # Create new conversation if too old
                conversation = ConversationContext(user_id, session_id)
                self.active_conversations[conversation_key] = conversation
        else:
            conversation = ConversationContext(user_id, session_id)
            self.active_conversations[conversation_key] = conversation
        
        return conversation
    
    async def _build_system_prompt(self, child_profile: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build age-appropriate system prompt for the LLM"""
        age = child_profile["age"]
        grade_level = child_profile["grade_level"]
        learning_style = child_profile.get("learning_style", "mixed")
        preferred_subjects = child_profile.get("preferred_subjects", [])
        
        # Get age-appropriate vocabulary settings
        vocab_settings = self.age_vocabulary.get(age, self.age_vocabulary[8])  # Default to age 8
        
        # Build curriculum context
        subject_context = ""
        if context.get("subject"):
            subject_context = f"\n- Current subject focus: {context['subject']}"
        
        # Build learning style guidance
        style_guidance = {
            "visual": "Use visual descriptions, diagrams, and step-by-step visual explanations. Suggest drawing or creating visual aids.",
            "auditory": "Use verbal explanations, encourage reading aloud, and suggest musical or rhythmic learning techniques.",
            "kinesthetic": "Suggest hands-on activities, movement-based learning, and practical examples they can touch or manipulate.",
            "mixed": "Combine visual, auditory, and hands-on approaches to accommodate different learning preferences."
        }
        
        learning_guidance = style_guidance.get(learning_style, style_guidance["mixed"])
        
        # Build system prompt
        system_prompt = f"""You are a friendly AI tutor specialized in the Cambridge Primary curriculum for children aged {age} (Grade {grade_level}). Your role is to help with Mathematics, English as a Second Language (ESL), and Science.

CORE GUIDELINES:
- Use vocabulary appropriate for a {age}-year-old child
- Keep sentences to maximum {vocab_settings['max_sentence_length']} words
- Use {vocab_settings['level']} language level
- Technical terms: {vocab_settings['technical_terms']}
- Always be encouraging and patient
- Break complex concepts into simple steps
- Provide concrete examples from daily life

RESPONSE FORMAT (Always respond in valid JSON):
{{
    "content": "Your main explanation or answer",
    "explanation_level": "very_simple|simple|intermediate|advanced",
    "curriculum_alignment": ["3Ma1a", "2E3b"] (Cambridge curriculum codes if applicable),
    "visual_aids_suggested": ["Description of helpful visual aids"],
    "follow_up_questions": ["Engaging questions to continue learning"],
    "detected_topic": "topic_name" (if you can identify the subject/topic),
    "confidence": 0.9 (your confidence in the response, 0-1)
}}

LEARNING STYLE PREFERENCE:
{learning_guidance}

CHILD'S PROFILE:
- Age: {age} years old
- Grade Level: {grade_level}
- Learning Style: {learning_style}
- Preferred Subjects: {', '.join(preferred_subjects) if preferred_subjects else 'None specified'}{subject_context}

CAMBRIDGE CURRICULUM ALIGNMENT:
- Mathematics: Focus on Number, Geometry, Statistics, and Problem Solving
- ESL: Focus on Reading, Writing, Speaking, Listening, and Grammar
- Science: Focus on Scientific Enquiry, Biology, Chemistry, Physics, and Earth & Space

SAFETY & APPROPRIATENESS:
- Only provide educational content appropriate for primary school children
- If asked about non-educational topics, gently redirect to learning
- Never provide personal information or engage in inappropriate conversations
- Encourage parental involvement when appropriate

Remember: Your goal is to make learning fun, engaging, and appropriately challenging for this {age}-year-old child while maintaining alignment with Cambridge Primary curriculum standards."""
        
        return system_prompt
    
    async def get_conversation_history(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """Get conversation history for a user session"""
        try:
            conversation_key = session_id or f"{user_id}_default"
            
            if conversation_key in self.active_conversations:
                conversation = self.active_conversations[conversation_key]
                return {
                    "session_id": conversation.session_id,
                    "user_id": conversation.user_id,
                    "messages": conversation.messages,
                    "learning_context": conversation.learning_context,
                    "current_topic": conversation.current_topic,
                    "difficulty_level": conversation.difficulty_level,
                    "created_at": conversation.created_at.isoformat(),
                    "last_updated": conversation.last_updated.isoformat(),
                    "message_count": len(conversation.messages)
                }
            else:
                return {
                    "session_id": session_id,
                    "user_id": user_id,
                    "messages": [],
                    "learning_context": {},
                    "current_topic": None,
                    "difficulty_level": 1,
                    "message_count": 0
                }
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise
    
    async def clear_conversation(self, user_id: str, session_id: str = None) -> bool:
        """Clear conversation history for a user session"""
        try:
            conversation_key = session_id or f"{user_id}_default"
            
            if conversation_key in self.active_conversations:
                del self.active_conversations[conversation_key]
                logger.info(f"Cleared conversation for user {user_id}, session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            raise
    
    def _get_learning_style_guidance(self, learning_style: str) -> str:
        """Get specific guidance for learning style"""
        guidance = {
            "visual": "Use descriptive language, suggest diagrams and charts, mention colors and shapes, and encourage drawing or visual representations.",
            "auditory": "Use rhythm and patterns in explanations, suggest reading aloud, mention sounds and music, and encourage verbal repetition.",
            "kinesthetic": "Suggest physical activities, hands-on experiments, movement-based learning, and tangible examples they can manipulate.",
            "mixed": "Combine visual descriptions, verbal explanations, and hands-on activities to appeal to all learning preferences."
        }
        return guidance.get(learning_style, guidance["mixed"])