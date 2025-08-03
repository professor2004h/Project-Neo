"""
CurriculumAligner - Ensures Cambridge standards compliance in AI responses
Task 4.2 implementation
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import json
import re

from utils.logger import logger
from services.llm import make_llm_api_call
from ..repositories.curriculum_repository import CurriculumTopicRepository, LearningObjectiveRepository
from ..models.user_models import Subject, LearningStyle
from ..models.curriculum_models import DifficultyLevel
from .cambridge_alignment_service import CambridgeAlignmentService


class CurriculumAligner:
    """
    Ensures AI tutor responses align with Cambridge Primary curriculum standards
    and adapts explanations for different learning styles and ages
    """
    
    def __init__(self, db):
        self.db = db
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.objectives_repo = LearningObjectiveRepository(db)
        self.alignment_service = CambridgeAlignmentService(db)
        
        # Cambridge curriculum progression mapping
        self.curriculum_progression = {
            Subject.MATHEMATICS: {
                1: ["Number recognition 1-20", "Basic counting", "Simple addition/subtraction to 10"],
                2: ["Number to 100", "Addition/subtraction to 20", "Basic shapes", "Simple measurement"],
                3: ["Number to 1000", "Multiplication tables 2,5,10", "Fractions halves/quarters", "Time"],
                4: ["Number to 10000", "All multiplication tables", "Decimal notation", "Area/perimeter"],
                5: ["Large numbers", "Fractions operations", "Percentages", "Volume", "Data handling"],
                6: ["Advanced calculations", "Ratio/proportion", "Coordinates", "Advanced geometry"]
            },
            Subject.ESL: {
                1: ["Basic vocabulary", "Simple sentences", "Listening skills", "Letter sounds"],
                2: ["Common words", "Present tense", "Reading simple texts", "Basic grammar"],
                3: ["Past tense", "Longer texts", "Writing sentences", "Pronunciation"],
                4: ["Future tense", "Complex sentences", "Story writing", "Discussion skills"],
                5: ["Advanced grammar", "Report writing", "Presentations", "Literature analysis"],
                6: ["Formal writing", "Debates", "Critical thinking", "Advanced vocabulary"]
            },
            Subject.SCIENCE: {
                1: ["Living/non-living", "Body parts", "Weather", "Materials"],
                2: ["Animal groups", "Plant growth", "Forces", "Healthy living"],
                3: ["Food chains", "Rocks/soils", "Light/shadow", "Magnets"],
                4: ["States of matter", "Sound", "Electricity", "Habitats"],
                5: ["Life cycles", "Earth/space", "Properties of materials", "Forces"],
                6: ["Classification", "Evolution", "Circuits", "Environmental science"]
            }
        }
        
        # Learning style adaptation strategies
        self.style_adaptations = {
            LearningStyle.VISUAL: {
                "techniques": ["diagrams", "charts", "color-coding", "visual metaphors", "drawings"],
                "language": ["imagine", "picture", "see", "look at", "visualize"],
                "tools": ["mind maps", "flowcharts", "infographics", "illustrated examples"]
            },
            LearningStyle.AUDITORY: {
                "techniques": ["verbal explanations", "rhythms", "songs", "discussions", "repetition"],
                "language": ["listen", "hear", "sounds like", "rhythm", "tune"],
                "tools": ["rhymes", "verbal instructions", "audio examples", "talking through"]
            },
            LearningStyle.KINESTHETIC: {
                "techniques": ["hands-on activities", "movement", "touch", "manipulation", "practice"],
                "language": ["feel", "touch", "move", "hands-on", "try it"],
                "tools": ["physical objects", "experiments", "role-play", "building"]
            },
            LearningStyle.MIXED: {
                "techniques": ["multi-sensory", "varied approaches", "flexible methods", "combined strategies"],
                "language": ["experience", "explore", "discover", "understand", "learn"],
                "tools": ["combination of visual, audio, and physical methods"]
            }
        }
    
    async def align_explanation(self, 
                              content: str,
                              subject: Subject,
                              grade_level: int,
                              learning_style: LearningStyle,
                              age: int,
                              topic_id: str = None) -> Dict[str, Any]:
        """
        Align content explanation with Cambridge curriculum standards
        
        Args:
            content: Original explanation content
            subject: Subject area
            grade_level: Cambridge grade level (1-6)
            learning_style: Preferred learning style
            age: Child's age
            topic_id: Optional specific topic ID
            
        Returns:
            Dictionary containing aligned explanation
        """
        try:
            # Get curriculum context
            curriculum_context = await self._get_curriculum_context(subject, grade_level, topic_id)
            
            # Get learning style adaptations
            style_context = self._get_learning_style_context(learning_style)
            
            # Build alignment prompt
            system_prompt = self._build_alignment_prompt(
                subject, grade_level, learning_style, age, curriculum_context, style_context
            )
            
            user_message = f"""Please align this explanation with Cambridge Primary curriculum standards:

Original content: "{content}"

Requirements:
- Subject: {subject.value}
- Grade level: {grade_level}
- Learning style: {learning_style.value}
- Age: {age}

Ensure the explanation meets Cambridge standards and is adapted for the specified learning style."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.3,  # Lower temperature for more consistent alignment
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                parsed_response = {
                    "aligned_content": llm_content,
                    "cambridge_codes": [],
                    "curriculum_alignment_score": 0.7,
                    "learning_style_adaptations": [],
                    "prerequisite_concepts": [],
                    "next_steps": []
                }
            
            # Validate alignment
            validation_result = await self._validate_alignment(
                parsed_response, subject, grade_level, topic_id
            )
            
            aligned_explanation = {
                "explanation_id": f"aligned_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "original_content": content,
                "aligned_content": parsed_response.get("aligned_content", content),
                "subject": subject.value,
                "grade_level": grade_level,
                "learning_style": learning_style.value,
                "age_targeted": age,
                "cambridge_codes": parsed_response.get("cambridge_codes", []),
                "curriculum_alignment_score": parsed_response.get("curriculum_alignment_score", 0.0),
                "learning_style_adaptations": parsed_response.get("learning_style_adaptations", []),
                "prerequisite_concepts": parsed_response.get("prerequisite_concepts", []),
                "next_steps": parsed_response.get("next_steps", []),
                "vocabulary_level": parsed_response.get("vocabulary_level", "appropriate"),
                "complexity_score": parsed_response.get("complexity_score", 0.5),
                "validation_result": validation_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Explanation aligned for {subject.value} grade {grade_level}: {validation_result['alignment_score']:.2f}")
            return aligned_explanation
            
        except Exception as e:
            logger.error(f"Error aligning explanation: {str(e)}")
            # Return original content with basic structure
            return {
                "explanation_id": f"fallback_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "original_content": content,
                "aligned_content": content,
                "subject": subject.value,
                "grade_level": grade_level,
                "learning_style": learning_style.value,
                "age_targeted": age,
                "cambridge_codes": [],
                "curriculum_alignment_score": 0.5,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def break_down_complex_concept(self,
                                       concept: str,
                                       subject: Subject,
                                       grade_level: int,
                                       learning_style: LearningStyle,
                                       age: int) -> Dict[str, Any]:
        """
        Break down complex concepts into simpler, age-appropriate steps
        
        Args:
            concept: Complex concept to break down
            subject: Subject area
            grade_level: Target grade level
            learning_style: Preferred learning style
            age: Child's age
            
        Returns:
            Dictionary containing step-by-step breakdown
        """
        try:
            # Get prerequisite knowledge for grade level
            prerequisites = self._get_prerequisite_knowledge(subject, grade_level)
            
            # Get learning style strategies
            style_strategies = self.style_adaptations[learning_style]
            
            # Build breakdown prompt
            system_prompt = f"""You are an expert teacher breaking down complex concepts for {age}-year-old children in Grade {grade_level}.

BREAKDOWN GUIDELINES:
- Subject: {subject.value}
- Learning style: {learning_style.value} (use {', '.join(style_strategies['techniques'])})
- Prerequisites available: {', '.join(prerequisites)}
- Use {style_strategies['language'][0]}, {style_strategies['language'][1]} language
- Tools to suggest: {', '.join(style_strategies['tools'])}

RESPONSE FORMAT (JSON):
{{
    "breakdown_steps": [
        {{
            "step_number": 1,
            "title": "Step title",
            "explanation": "Simple explanation",
            "example": "Concrete example",
            "activity": "Hands-on activity suggestion",
            "prerequisite": "What child needs to know first"
        }}
    ],
    "learning_sequence": ["Step 1", "Step 2", "Step 3"],
    "visual_aids": ["Specific visual aids for {learning_style.value} learners"],
    "practice_activities": ["Age-appropriate practice suggestions"],
    "assessment_questions": ["Simple questions to check understanding"],
    "common_misconceptions": ["What children often get wrong"],
    "parent_tips": ["How parents can help at home"]
}}

Break complex concepts into 3-5 simple steps maximum."""

            user_message = f"Please break down this concept for understanding: '{concept}'"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                # Fallback breakdown
                parsed_response = {
                    "breakdown_steps": [
                        {
                            "step_number": 1,
                            "title": "Understanding the basics",
                            "explanation": f"Let's start with the simple parts of {concept}",
                            "example": "We'll use everyday examples",
                            "activity": "Try it yourself with simple materials",
                            "prerequisite": "Basic counting and recognition"
                        }
                    ],
                    "learning_sequence": ["Start simple", "Add details", "Practice together"],
                    "visual_aids": ["Use pictures and drawings"],
                    "practice_activities": ["Hands-on practice"],
                    "assessment_questions": [f"Can you explain {concept} in your own words?"]
                }
            
            breakdown_result = {
                "breakdown_id": f"breakdown_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "original_concept": concept,
                "subject": subject.value,
                "grade_level": grade_level,
                "learning_style": learning_style.value,
                "age_targeted": age,
                "breakdown_steps": parsed_response.get("breakdown_steps", []),
                "learning_sequence": parsed_response.get("learning_sequence", []),
                "visual_aids": parsed_response.get("visual_aids", []),
                "practice_activities": parsed_response.get("practice_activities", []),
                "assessment_questions": parsed_response.get("assessment_questions", []),
                "common_misconceptions": parsed_response.get("common_misconceptions", []),
                "parent_tips": parsed_response.get("parent_tips", []),
                "total_steps": len(parsed_response.get("breakdown_steps", [])),
                "estimated_time_minutes": len(parsed_response.get("breakdown_steps", [])) * 10,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Complex concept broken down: {concept} -> {breakdown_result['total_steps']} steps")
            return breakdown_result
            
        except Exception as e:
            logger.error(f"Error breaking down concept: {str(e)}")
            raise
    
    async def adapt_for_learning_style(self,
                                     content: str,
                                     learning_style: LearningStyle,
                                     subject: Subject,
                                     age: int) -> Dict[str, Any]:
        """
        Adapt explanation for specific learning style
        
        Args:
            content: Original content
            learning_style: Target learning style
            subject: Subject area
            age: Child's age
            
        Returns:
            Dictionary containing adapted content
        """
        try:
            style_strategies = self.style_adaptations[learning_style]
            
            system_prompt = f"""You are adapting educational content for {learning_style.value} learners aged {age}.

ADAPTATION STRATEGIES FOR {learning_style.value.upper()} LEARNERS:
- Primary techniques: {', '.join(style_strategies['techniques'])}
- Use language like: {', '.join(style_strategies['language'])}
- Suggest tools: {', '.join(style_strategies['tools'])}

RESPONSE FORMAT (JSON):
{{
    "adapted_content": "Content rewritten for {learning_style.value} learners",
    "learning_activities": ["Specific activities for {learning_style.value} style"],
    "materials_needed": ["Physical materials or tools needed"],
    "step_by_step_instructions": ["How to teach this concept using {learning_style.value} methods"],
    "engagement_techniques": ["Ways to keep {learning_style.value} learners engaged"],
    "assessment_methods": ["How to check understanding for {learning_style.value} learners"]
}}

Subject: {subject.value}
Make it engaging and appropriate for {learning_style.value} learning preferences!"""

            user_message = f"Please adapt this content for {learning_style.value} learners: '{content}'"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.5,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            parsed_response = json.loads(llm_content)
            
            adapted_result = {
                "adaptation_id": f"adapted_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "original_content": content,
                "adapted_content": parsed_response.get("adapted_content", content),
                "learning_style": learning_style.value,
                "subject": subject.value,
                "age_targeted": age,
                "learning_activities": parsed_response.get("learning_activities", []),
                "materials_needed": parsed_response.get("materials_needed", []),
                "step_by_step_instructions": parsed_response.get("step_by_step_instructions", []),
                "engagement_techniques": parsed_response.get("engagement_techniques", []),
                "assessment_methods": parsed_response.get("assessment_methods", []),
                "adaptation_strategies_used": style_strategies['techniques'],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Content adapted for {learning_style.value} learning style")
            return adapted_result
            
        except Exception as e:
            logger.error(f"Error adapting for learning style: {str(e)}")
            raise
    
    async def _get_curriculum_context(self, subject: Subject, grade_level: int, topic_id: str = None) -> Dict[str, Any]:
        """Get relevant curriculum context for alignment"""
        context = {
            "grade_objectives": self.curriculum_progression.get(subject, {}).get(grade_level, []),
            "prerequisite_grade": self.curriculum_progression.get(subject, {}).get(grade_level - 1, []) if grade_level > 1 else [],
            "next_grade": self.curriculum_progression.get(subject, {}).get(grade_level + 1, []) if grade_level < 6 else []
        }
        
        # Add specific topic information if available
        if topic_id:
            try:
                topic_info = await self.curriculum_repo.get_by_id(topic_id, "topic_id")
                if topic_info:
                    context["topic"] = {
                        "title": topic_info["title"],
                        "cambridge_code": topic_info["cambridge_code"],
                        "learning_objectives": topic_info.get("learning_objectives", [])
                    }
                    
                    # Get learning objectives
                    objectives = await self.objectives_repo.get_by_topic_id(topic_id)
                    context["detailed_objectives"] = [obj["description"] for obj in objectives]
            except:
                pass
        
        return context
    
    def _get_learning_style_context(self, learning_style: LearningStyle) -> Dict[str, Any]:
        """Get learning style adaptation context"""
        return self.style_adaptations.get(learning_style, self.style_adaptations[LearningStyle.MIXED])
    
    def _build_alignment_prompt(self, subject: Subject, grade_level: int, learning_style: LearningStyle, 
                              age: int, curriculum_context: Dict, style_context: Dict) -> str:
        """Build comprehensive alignment prompt for LLM"""
        return f"""You are a Cambridge Primary curriculum expert aligning educational content.

CAMBRIDGE STANDARDS FOR {subject.value.upper()} GRADE {grade_level}:
Current grade objectives: {', '.join(curriculum_context['grade_objectives'])}
Prerequisites from Grade {grade_level-1 if grade_level > 1 else 'Foundation'}: {', '.join(curriculum_context['prerequisite_grade'])}

LEARNING STYLE ADAPTATION FOR {learning_style.value.upper()}:
- Use techniques: {', '.join(style_context['techniques'])}
- Incorporate tools: {', '.join(style_context['tools'])}
- Language style: {', '.join(style_context['language'])}

RESPONSE FORMAT (JSON):
{{
    "aligned_content": "Content aligned to Cambridge standards and learning style",
    "cambridge_codes": ["Relevant Cambridge curriculum codes"],
    "curriculum_alignment_score": 0.95,
    "learning_style_adaptations": ["Specific adaptations made"],
    "prerequisite_concepts": ["What students need to know first"],
    "next_steps": ["What to learn next"],
    "vocabulary_level": "appropriate|simplified|advanced",
    "complexity_score": 0.6,
    "assessment_alignment": "How this aligns with Cambridge assessment expectations"
}}

ALIGNMENT CRITERIA:
- Content must match Grade {grade_level} Cambridge objectives
- Vocabulary appropriate for age {age}
- {learning_style.value} learning preferences incorporated
- Progressive difficulty following Cambridge framework
- Assessment-ready explanations"""
    
    def _get_prerequisite_knowledge(self, subject: Subject, grade_level: int) -> List[str]:
        """Get prerequisite knowledge for grade level"""
        if grade_level <= 1:
            return ["Basic recognition", "Simple counting", "Following instructions"]
        
        prerequisites = []
        for grade in range(1, grade_level):
            grade_objectives = self.curriculum_progression.get(subject, {}).get(grade, [])
            prerequisites.extend(grade_objectives)
        
        return prerequisites[-5:] if len(prerequisites) > 5 else prerequisites  # Return most recent 5
    
    async def _validate_alignment(self, response: Dict, subject: Subject, grade_level: int, topic_id: str = None) -> Dict[str, Any]:
        """Validate curriculum alignment of the response"""
        validation = {
            "is_aligned": True,
            "alignment_score": 0.8,
            "issues": [],
            "recommendations": []
        }
        
        # Check cambridge codes if provided
        if response.get("cambridge_codes"):
            for code in response["cambridge_codes"]:
                code_validation = self.alignment_service.validate_cambridge_code(code, subject)
                if not code_validation["is_valid"]:
                    validation["issues"].append(f"Invalid Cambridge code: {code}")
                    validation["alignment_score"] -= 0.1
                elif code_validation["grade_level"] != grade_level:
                    validation["issues"].append(f"Grade mismatch in code {code}: expected {grade_level}, got {code_validation['grade_level']}")
                    validation["alignment_score"] -= 0.05
        
        # Check if content mentions appropriate grade level concepts
        content = response.get("aligned_content", "").lower()
        grade_concepts = self.curriculum_progression.get(subject, {}).get(grade_level, [])
        
        concept_matches = sum(1 for concept in grade_concepts if any(word in content for word in concept.lower().split()))
        if concept_matches == 0:
            validation["issues"].append("Content doesn't reference grade-level concepts")
            validation["alignment_score"] -= 0.2
        
        # Final validation
        validation["is_aligned"] = validation["alignment_score"] >= 0.7
        if not validation["is_aligned"]:
            validation["recommendations"].append("Content needs better alignment with Cambridge standards")
        
        return validation