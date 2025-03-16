"""Feedback Collection and Analysis System

This module implements a comprehensive feedback collection and analysis system for the recruitment process.
It follows SOTA practices including:
1. Structured feedback templates with quantitative and qualitative components
2. Real-time sentiment analysis using Gemini
3. Automated insights generation
4. Bias detection and mitigation
5. Integration with the candidate ranking system

The design is inspired by patterns in the OpenManus-main repository.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
from dataclasses import dataclass
from google.generativeai.types import model_types

@dataclass
class FeedbackTemplate:
    """Template for structured feedback collection."""
    technical_skills: Dict[str, float]  # Skill -> Rating (0-5)
    soft_skills: Dict[str, float]  # Skill -> Rating (0-5)
    communication: float  # 0-5
    problem_solving: float  # 0-5
    cultural_fit: float  # 0-5
    overall_rating: float  # 0-5
    strengths: List[str]
    areas_for_improvement: List[str]
    additional_comments: str
    interviewer_id: str
    timestamp: datetime

@dataclass
class FeedbackAnalysis:
    """Analysis results for collected feedback."""
    average_ratings: Dict[str, float]
    sentiment_scores: Dict[str, float]
    key_insights: List[str]
    potential_biases: List[Dict[str, Any]]
    recommendation: str
    confidence_score: float

class FeedbackCollector:
    def __init__(
        self,
        storage_dir: str,
        gemini_model: model_types.GenerativeModel,
        min_confidence: float = 0.7
    ):
        """Initialize the feedback collector.
        
        Args:
            storage_dir: Directory for storing feedback data
            gemini_model: Gemini model for analysis
            min_confidence: Minimum confidence threshold for insights
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.gemini = gemini_model
        self.min_confidence = min_confidence
        self.feedback_cache = {}

    async def submit_feedback(
        self,
        candidate_id: str,
        feedback: FeedbackTemplate
    ) -> bool:
        """Submit feedback for a candidate.
        
        Args:
            candidate_id: Candidate identifier
            feedback: Structured feedback data
            
        Returns:
            Success status
        """
        try:
            # Create feedback entry
            entry = {
                "candidate_id": candidate_id,
                "timestamp": feedback.timestamp.isoformat(),
                "interviewer_id": feedback.interviewer_id,
                "technical_skills": feedback.technical_skills,
                "soft_skills": feedback.soft_skills,
                "communication": feedback.communication,
                "problem_solving": feedback.problem_solving,
                "cultural_fit": feedback.cultural_fit,
                "overall_rating": feedback.overall_rating,
                "strengths": feedback.strengths,
                "areas_for_improvement": feedback.areas_for_improvement,
                "additional_comments": feedback.additional_comments
            }

            # Save to file
            feedback_file = self.storage_dir / f"{candidate_id}_{feedback.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(feedback_file, "w") as f:
                json.dump(entry, f, indent=2)

            # Update cache
            if candidate_id not in self.feedback_cache:
                self.feedback_cache[candidate_id] = []
            self.feedback_cache[candidate_id].append(entry)

            return True
        except Exception as e:
            print(f"Error submitting feedback: {e}")
            return False

    async def analyze_feedback(
        self,
        candidate_id: str
    ) -> Optional[FeedbackAnalysis]:
        """Analyze feedback for a candidate using Gemini.
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            Analysis results or None if no feedback found
        """
        # Get all feedback for candidate
        feedback_list = await self._get_candidate_feedback(candidate_id)
        if not feedback_list:
            return None

        # Calculate average ratings
        avg_ratings = self._calculate_average_ratings(feedback_list)

        # Analyze sentiment and generate insights using Gemini
        sentiment_scores, insights = await self._analyze_with_gemini(feedback_list)

        # Check for potential biases
        biases = await self._detect_biases(feedback_list)

        # Generate recommendation
        recommendation = await self._generate_recommendation(
            feedback_list,
            avg_ratings,
            sentiment_scores,
            biases
        )

        # Calculate confidence score
        confidence = self._calculate_confidence(feedback_list)

        return FeedbackAnalysis(
            average_ratings=avg_ratings,
            sentiment_scores=sentiment_scores,
            key_insights=insights,
            potential_biases=biases,
            recommendation=recommendation,
            confidence_score=confidence
        )

    async def _get_candidate_feedback(
        self,
        candidate_id: str
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a candidate.
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            List of feedback entries
        """
        if candidate_id in self.feedback_cache:
            return self.feedback_cache[candidate_id]

        feedback_list = []
        for file in self.storage_dir.glob(f"{candidate_id}_*.json"):
            try:
                with open(file, "r") as f:
                    feedback_list.append(json.load(f))
            except Exception as e:
                print(f"Error loading feedback file {file}: {e}")

        self.feedback_cache[candidate_id] = feedback_list
        return feedback_list

    def _calculate_average_ratings(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate average ratings across all feedback.
        
        Args:
            feedback_list: List of feedback entries
            
        Returns:
            Dictionary of average ratings
        """
        if not feedback_list:
            return {}

        # Initialize accumulators
        total_ratings = {
            "technical_skills": {},
            "soft_skills": {},
            "communication": 0,
            "problem_solving": 0,
            "cultural_fit": 0,
            "overall_rating": 0
        }
        counts = {
            "technical_skills": {},
            "soft_skills": {},
            "communication": 0,
            "problem_solving": 0,
            "cultural_fit": 0,
            "overall_rating": 0
        }

        # Accumulate ratings
        for feedback in feedback_list:
            # Technical skills
            for skill, rating in feedback["technical_skills"].items():
                if skill not in total_ratings["technical_skills"]:
                    total_ratings["technical_skills"][skill] = 0
                    counts["technical_skills"][skill] = 0
                total_ratings["technical_skills"][skill] += rating
                counts["technical_skills"][skill] += 1

            # Soft skills
            for skill, rating in feedback["soft_skills"].items():
                if skill not in total_ratings["soft_skills"]:
                    total_ratings["soft_skills"][skill] = 0
                    counts["soft_skills"][skill] = 0
                total_ratings["soft_skills"][skill] += rating
                counts["soft_skills"][skill] += 1

            # Other ratings
            for key in ["communication", "problem_solving", "cultural_fit", "overall_rating"]:
                total_ratings[key] += feedback[key]
                counts[key] += 1

        # Calculate averages
        avg_ratings = {
            "technical_skills": {
                skill: total / counts["technical_skills"][skill]
                for skill, total in total_ratings["technical_skills"].items()
            },
            "soft_skills": {
                skill: total / counts["soft_skills"][skill]
                for skill, total in total_ratings["soft_skills"].items()
            }
        }

        for key in ["communication", "problem_solving", "cultural_fit", "overall_rating"]:
            avg_ratings[key] = total_ratings[key] / counts[key]

        return avg_ratings

    async def _analyze_with_gemini(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> tuple[Dict[str, float], List[str]]:
        """Analyze feedback using Gemini for sentiment and insights.
        
        Args:
            feedback_list: List of feedback entries
            
        Returns:
            Tuple of (sentiment_scores, key_insights)
        """
        prompt = f"""Analyze this candidate feedback:

        {json.dumps(feedback_list, indent=2)}

        Provide:
        1. Sentiment scores (0-1) for:
           - Technical feedback
           - Soft skills feedback
           - Overall impression
        2. Key insights (list of strings)

        Return as JSON:
        {{
            "sentiment": {{
                "technical": float,
                "soft_skills": float,
                "overall": float
            }},
            "insights": [
                "string"
            ]
        }}
        """

        response = await self.gemini.generate_content(prompt)
        result = response.json()

        return result["sentiment"], result["insights"]

    async def _detect_biases(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect potential biases in feedback using Gemini.
        
        Args:
            feedback_list: List of feedback entries
            
        Returns:
            List of potential biases detected
        """
        prompt = f"""Analyze this feedback for potential biases:

        {json.dumps(feedback_list, indent=2)}

        Consider:
        1. Language patterns
        2. Rating distributions
        3. Inconsistencies
        4. Subjective vs objective assessments

        Return as JSON array of:
        {{
            "type": "bias type",
            "description": "description",
            "confidence": float,
            "evidence": [
                "supporting examples"
            ]
        }}
        """

        response = await self.gemini.generate_content(prompt)
        return response.json()

    async def _generate_recommendation(
        self,
        feedback_list: List[Dict[str, Any]],
        avg_ratings: Dict[str, float],
        sentiment_scores: Dict[str, float],
        biases: List[Dict[str, Any]]
    ) -> str:
        """Generate final recommendation using Gemini.
        
        Args:
            feedback_list: List of feedback entries
            avg_ratings: Average ratings
            sentiment_scores: Sentiment analysis scores
            biases: Detected biases
            
        Returns:
            Recommendation string
        """
        prompt = f"""Generate a final recommendation based on:

        Feedback:
        {json.dumps(feedback_list, indent=2)}

        Average Ratings:
        {json.dumps(avg_ratings, indent=2)}

        Sentiment Scores:
        {json.dumps(sentiment_scores, indent=2)}

        Potential Biases:
        {json.dumps(biases, indent=2)}

        Provide a concise, actionable recommendation considering all factors.
        """

        response = await self.gemini.generate_content(prompt)
        return response.text

    def _calculate_confidence(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for the analysis.
        
        Args:
            feedback_list: List of feedback entries
            
        Returns:
            Confidence score (0-1)
        """
        if not feedback_list:
            return 0.0

        # Factors affecting confidence:
        # 1. Number of feedback entries
        # 2. Consistency of ratings
        # 3. Completeness of feedback

        # Calculate rating consistency
        overall_ratings = [f["overall_rating"] for f in feedback_list]
        rating_std = np.std(overall_ratings) if len(overall_ratings) > 1 else 0
        consistency_score = max(0, 1 - (rating_std / 5))  # Normalize to 0-1

        # Calculate completeness
        completeness_scores = []
        for feedback in feedback_list:
            required_fields = [
                "technical_skills",
                "soft_skills",
                "communication",
                "problem_solving",
                "cultural_fit",
                "overall_rating",
                "strengths",
                "areas_for_improvement"
            ]
            complete_fields = sum(1 for field in required_fields if feedback.get(field))
            completeness_scores.append(complete_fields / len(required_fields))
        completeness_score = np.mean(completeness_scores)

        # Calculate final confidence
        n_feedback = len(feedback_list)
        feedback_count_score = min(n_feedback / 3, 1.0)  # Normalize, max at 3 feedback entries

        # Weighted average of factors
        weights = [0.4, 0.3, 0.3]  # feedback_count, consistency, completeness
        confidence = np.average(
            [feedback_count_score, consistency_score, completeness_score],
            weights=weights
        )

        return float(confidence) 