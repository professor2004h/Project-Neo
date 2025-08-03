"""
Cambridge Curriculum Alignment Service - Handles curriculum code validation and content alignment
"""
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime

from ..models.curriculum_models import Subject, DifficultyLevel
from ..repositories.curriculum_repository import CurriculumTopicRepository, LearningObjectiveRepository
from utils.logger import logger


class CambridgeAlignmentService:
    """Service for Cambridge curriculum alignment and validation"""
    
    def __init__(self, db):
        self.db = db
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.objectives_repo = LearningObjectiveRepository(db)
        
        # Cambridge curriculum code patterns by subject
        self.cambridge_patterns = {
            Subject.MATHEMATICS: {
                "pattern": r"^(\d+)Ma(\d+)([a-z]?)$",
                "description": "Grade + Ma + Strand + Optional Sub-strand",
                "example": "3Ma1a"
            },
            Subject.ESL: {
                "pattern": r"^(\d+)E(\d+)([a-z]?)$", 
                "description": "Grade + E + Strand + Optional Sub-strand",
                "example": "2E3b"
            },
            Subject.SCIENCE: {
                "pattern": r"^(\d+)Sc(\d+)([a-z]?)$",
                "description": "Grade + Sc + Strand + Optional Sub-strand", 
                "example": "4Sc2a"
            }
        }
        
        # Age appropriateness mapping
        self.age_grade_mapping = {
            5: 1, 6: 1,  # Reception/Year 1
            7: 2,        # Year 2
            8: 3,        # Year 3
            9: 4,        # Year 4
            10: 5,       # Year 5
            11: 6, 12: 6 # Year 6
        }
    
    def validate_cambridge_code(self, cambridge_code: str, subject: Subject = None) -> Dict[str, Any]:
        """
        Validate Cambridge curriculum code format and extract components
        
        Args:
            cambridge_code: Cambridge curriculum code to validate
            subject: Optional subject to validate against specific pattern
            
        Returns:
            Dictionary with validation results and extracted components
        """
        try:
            cambridge_code = cambridge_code.upper().strip()
            
            validation_result = {
                "is_valid": False,
                "cambridge_code": cambridge_code,
                "subject": None,
                "grade_level": None,
                "strand": None,
                "sub_strand": None,
                "errors": []
            }
            
            if not cambridge_code:
                validation_result["errors"].append("Cambridge code cannot be empty")
                return validation_result
            
            if len(cambridge_code) < 3:
                validation_result["errors"].append("Cambridge code must be at least 3 characters")
                return validation_result
            
            # Try to match against subject patterns
            matched_subject = None
            match = None
            
            subjects_to_check = [subject] if subject else list(Subject)
            
            for subj in subjects_to_check:
                pattern = self.cambridge_patterns[subj]["pattern"]
                match = re.match(pattern, cambridge_code)
                if match:
                    matched_subject = subj
                    break
            
            if not match or not matched_subject:
                if subject:
                    validation_result["errors"].append(f"Code does not match {subject.value} pattern: {self.cambridge_patterns[subject]['example']}")
                else:
                    validation_result["errors"].append("Code does not match any known Cambridge pattern")
                return validation_result
            
            # Extract components
            grade_level = int(match.group(1))
            strand = match.group(2)
            sub_strand = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
            
            # Validate grade level
            if grade_level < 1 or grade_level > 6:
                validation_result["errors"].append("Grade level must be between 1 and 6")
                return validation_result
            
            # Successful validation
            validation_result.update({
                "is_valid": True,
                "subject": matched_subject,
                "grade_level": grade_level,
                "strand": strand,
                "sub_strand": sub_strand
            })
            
            logger.info(f"Successfully validated Cambridge code: {cambridge_code}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Cambridge code: {str(e)}")
            validation_result["errors"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def validate_curriculum_alignment(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that content aligns with Cambridge curriculum standards
        
        Args:
            content_data: Dictionary containing content information
            
        Returns:
            Dictionary containing alignment report
        """
        try:
            content_id = content_data.get("content_id", "unknown")
            topic_id = content_data.get("topic_id")
            cambridge_codes = content_data.get("cambridge_codes", [])
            
            alignment_report = {
                "content_id": content_id,
                "is_aligned": False,
                "alignment_score": 0.0,
                "cambridge_codes": cambridge_codes,
                "validated_codes": [],
                "invalid_codes": [],
                "topic_alignment": None,
                "recommendations": [],
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Validate Cambridge codes
            total_codes = len(cambridge_codes)
            valid_codes = 0
            
            for code in cambridge_codes:
                validation = self.validate_cambridge_code(code)
                if validation["is_valid"]:
                    alignment_report["validated_codes"].append({
                        "code": code,
                        "subject": validation["subject"].value,
                        "grade_level": validation["grade_level"],
                        "strand": validation["strand"]
                    })
                    valid_codes += 1
                else:
                    alignment_report["invalid_codes"].append({
                        "code": code,
                        "errors": validation["errors"]
                    })
            
            # Calculate code alignment score
            code_alignment_score = (valid_codes / total_codes) if total_codes > 0 else 0
            
            # Validate topic alignment if topic_id provided
            topic_alignment_score = 0
            if topic_id:
                topic_alignment = await self._validate_topic_alignment(topic_id, cambridge_codes)
                alignment_report["topic_alignment"] = topic_alignment
                topic_alignment_score = topic_alignment.get("alignment_score", 0)
            
            # Calculate overall alignment score
            alignment_report["alignment_score"] = (code_alignment_score + topic_alignment_score) / 2
            
            # Determine if content is aligned (threshold: 0.8)
            alignment_report["is_aligned"] = alignment_report["alignment_score"] >= 0.8
            
            # Generate recommendations
            if alignment_report["alignment_score"] < 0.8:
                alignment_report["recommendations"] = self._generate_alignment_recommendations(
                    alignment_report
                )
            
            logger.info(f"Validated curriculum alignment for content {content_id}: {alignment_report['alignment_score']:.2f}")
            return alignment_report
            
        except Exception as e:
            logger.error(f"Error validating curriculum alignment: {str(e)}")
            alignment_report["recommendations"].append(f"Validation error: {str(e)}")
            return alignment_report
    
    async def _validate_topic_alignment(self, topic_id: str, cambridge_codes: List[str]) -> Dict[str, Any]:
        """Validate alignment between topic and Cambridge codes"""
        try:
            # Get the topic from database
            topic = await self.curriculum_repo.get_by_id(topic_id, "topic_id")
            if not topic:
                return {
                    "topic_found": False,
                    "alignment_score": 0,
                    "message": "Topic not found"
                }
            
            topic_code = topic.get("cambridge_code", "")
            topic_subject = topic.get("subject", "")
            topic_grade = topic.get("grade_level", 0)
            
            alignment_score = 0
            matching_codes = []
            
            # Check if any provided codes match the topic's code
            for code in cambridge_codes:
                if code.upper() == topic_code.upper():
                    matching_codes.append(code)
                    alignment_score = 1.0
                    break
                
                # Check for partial matches (same subject and grade)
                validation = self.validate_cambridge_code(code)
                if (validation["is_valid"] and 
                    validation["subject"].value == topic_subject and
                    validation["grade_level"] == topic_grade):
                    matching_codes.append(code)
                    alignment_score = max(alignment_score, 0.7)
            
            return {
                "topic_found": True,
                "topic_code": topic_code,
                "topic_subject": topic_subject,
                "topic_grade": topic_grade,
                "matching_codes": matching_codes,
                "alignment_score": alignment_score,
                "message": f"Found {len(matching_codes)} matching codes"
            }
            
        except Exception as e:
            logger.error(f"Error validating topic alignment: {str(e)}")
            return {
                "topic_found": False,
                "alignment_score": 0,
                "message": f"Error: {str(e)}"
            }
    
    def _generate_alignment_recommendations(self, alignment_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving curriculum alignment"""
        recommendations = []
        
        if alignment_report["invalid_codes"]:
            recommendations.append(
                f"Fix {len(alignment_report['invalid_codes'])} invalid Cambridge codes"
            )
        
        if alignment_report["alignment_score"] < 0.5:
            recommendations.append(
                "Content significantly misaligned with Cambridge standards - major revision needed"
            )
        elif alignment_report["alignment_score"] < 0.8:
            recommendations.append(
                "Content partially aligned - verify Cambridge code mappings and topic references"
            )
        
        if not alignment_report["cambridge_codes"]:
            recommendations.append(
                "Add Cambridge curriculum codes to establish curriculum alignment"
            )
        
        topic_alignment = alignment_report.get("topic_alignment", {})
        if topic_alignment and topic_alignment.get("alignment_score", 0) < 0.7:
            recommendations.append(
                "Verify content topic mapping - may need to reassign to correct curriculum topic"
            )
        
        return recommendations
    
    def validate_age_appropriateness(self, content_data: Dict[str, Any], target_age: int) -> Dict[str, Any]:
        """
        Validate if content is appropriate for target age
        
        Args:
            content_data: Content information including difficulty level
            target_age: Target age for the content
            
        Returns:
            Dictionary with age appropriateness assessment
        """
        try:
            content_id = content_data.get("content_id", "unknown")
            difficulty_level = content_data.get("difficulty_level", "elementary")
            grade_level = content_data.get("grade_level")
            
            result = {
                "content_id": content_id,
                "target_age": target_age,
                "is_appropriate": False,
                "appropriateness_score": 0.0,
                "recommended_age_range": None,
                "issues": [],
                "recommendations": []
            }
            
            # Get recommended grade level for age
            recommended_grade = self.age_grade_mapping.get(target_age)
            if not recommended_grade:
                result["issues"].append(f"Age {target_age} is outside primary school range (5-12)")
                return result
            
            # Difficulty level mapping to grade ranges
            difficulty_grade_ranges = {
                "beginner": (1, 2),
                "elementary": (1, 3),
                "intermediate": (3, 5),
                "advanced": (5, 6),
                "expert": (6, 6)
            }
            
            difficulty_range = difficulty_grade_ranges.get(difficulty_level, (1, 6))
            result["recommended_age_range"] = {
                "min_age": 5 + difficulty_range[0] - 1,
                "max_age": 5 + difficulty_range[1] - 1,
                "min_grade": difficulty_range[0],
                "max_grade": difficulty_range[1]
            }
            
            # Calculate appropriateness score
            if grade_level:
                grade_diff = abs(grade_level - recommended_grade)
                if grade_diff == 0:
                    result["appropriateness_score"] = 1.0
                elif grade_diff == 1:
                    result["appropriateness_score"] = 0.8
                elif grade_diff == 2:
                    result["appropriateness_score"] = 0.6
                else:
                    result["appropriateness_score"] = 0.3
            else:
                # Use difficulty level assessment
                if (difficulty_range[0] <= recommended_grade <= difficulty_range[1]):
                    result["appropriateness_score"] = 0.9
                elif (difficulty_range[0] - 1 <= recommended_grade <= difficulty_range[1] + 1):
                    result["appropriateness_score"] = 0.7
                else:
                    result["appropriateness_score"] = 0.4
            
            result["is_appropriate"] = result["appropriateness_score"] >= 0.7
            
            # Generate recommendations
            if not result["is_appropriate"]:
                if result["appropriateness_score"] < 0.5:
                    result["recommendations"].append(
                        f"Content difficulty too {'high' if difficulty_range[0] > recommended_grade else 'low'} for age {target_age}"
                    )
                else:
                    result["recommendations"].append(
                        f"Content may need adaptation for age {target_age}"
                    )
            
            logger.info(f"Age appropriateness validated for content {content_id}: {result['appropriateness_score']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating age appropriateness: {str(e)}")
            result["issues"].append(f"Validation error: {str(e)}")
            return result
    
    async def get_curriculum_codes_by_topic(self, topic_id: str) -> List[str]:
        """Get Cambridge curriculum codes associated with a topic"""
        try:
            topic = await self.curriculum_repo.get_by_id(topic_id, "topic_id")
            if topic and topic.get("cambridge_code"):
                return [topic["cambridge_code"]]
            
            # Also check learning objectives for additional codes
            objectives = await self.objectives_repo.get_by_topic_id(topic_id)
            codes = []
            for obj in objectives:
                if obj.get("cambridge_reference"):
                    codes.append(obj["cambridge_reference"])
            
            return codes
            
        except Exception as e:
            logger.error(f"Error getting curriculum codes for topic: {str(e)}")
            return []
    
    def get_subject_from_code(self, cambridge_code: str) -> Optional[Subject]:
        """Extract subject from Cambridge curriculum code"""
        validation = self.validate_cambridge_code(cambridge_code)
        return validation.get("subject") if validation["is_valid"] else None