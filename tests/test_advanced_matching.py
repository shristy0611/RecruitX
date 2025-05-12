"""
Test suite for Advanced Matching V1.

This module tests the advanced matching capabilities including:
1. Context-aware matching with bi-directional preferences
2. Team fit analysis using Gemini's comparative reasoning
3. Career trajectory prediction and growth potential assessment
"""

import logging
import json
import unittest
from unittest.mock import MagicMock, patch

from src.matching.advanced_matcher import AdvancedMatcher
from src.matching.team_fit_analyzer import TeamFitAnalyzer
from src.matching.career_trajectory_analyzer import CareerTrajectoryAnalyzer
from src.matching.models import (
    AdvancedMatchingResult,
    BiDirectionalPreference,
    TeamFitResult,
    CareerTrajectoryResult
)
from src.knowledge_base.vector_store import VectorStore
from src.agents.matching_agent import MatchingAgent, MatchingResult

# Configure logging
logger = logging.getLogger(__name__)


class TestAdvancedMatching(unittest.TestCase):
    """Test cases for Advanced Matching V1 implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the vector store
        self.mock_vector_store = MagicMock(spec=VectorStore)
        
        # Set up mock data
        self.candidate_data = {
            "id": "candidate123",
            "name": "Test Candidate",
            "skills": ["Python", "Machine Learning", "SQL", "Cloud Computing"],
            "experience": "5 years of experience in software engineering",
            "education": "Bachelor's in Computer Science",
            "current_role": "Senior Software Engineer",
            "preferences": {
                "remote_work": 0.8,
                "work_life_balance": 0.7,
                "growth_opportunities": 0.9,
                "collaborative_environment": 0.6
            }
        }
        
        self.job_data = {
            "id": "job456",
            "title": "Senior Data Scientist",
            "company": {
                "id": "company789",
                "name": "TechCorp",
                "description": "Leading technology company",
                "teams": [
                    {"id": "team123", "name": "Data Science Team"}
                ]
            },
            "description": "Senior role in data science team",
            "requirements": "Python, Machine Learning, SQL required",
            "preferences": {
                "collaborative_environment": 0.8,
                "innovation": 0.9,
                "remote_work": 0.7
            }
        }
        
        self.team_data = {
            "id": "team123",
            "name": "Data Science Team",
            "size": 8,
            "composition": "3 Senior Data Scientists, 4 Data Scientists, 1 ML Engineer",
            "culture": "Collaborative and innovative",
            "working_style": "Agile with bi-weekly sprints",
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Data Visualization"]
        }
        
        # Configure mock vector store responses
        self.mock_vector_store.get_by_id.side_effect = self._mock_get_by_id
        
        # Mock base matcher
        self.mock_base_matcher = MagicMock(spec=MatchingAgent)
        self.mock_base_matcher.match_candidates.return_value = [
            MatchingResult(
                candidate_id="candidate123",
                job_id="job456",
                overall_score=85.0,
                skill_match_score=90.0,
                experience_match_score=80.0,
                education_match_score=75.0,
                explanation="Mock basic matching explanation",
                skills_matched=["Python", "SQL"],
                skills_missing=["TensorFlow"],
                matching_id="match789"
            )
        ]
        
        # Create test instance
        self.advanced_matcher = AdvancedMatcher(
            base_matcher=self.mock_base_matcher,
            vector_store=self.mock_vector_store
        )
        
        # Mock team fit analyzer and career trajectory analyzer
        self.advanced_matcher.team_fit_analyzer = MagicMock(spec=TeamFitAnalyzer)
        self.advanced_matcher.team_fit_analyzer.predict_team_fit.return_value = TeamFitResult(
            team_id="team123",
            candidate_id="candidate123",
            compatibility_score=82.5,
            key_factors=[
                {"factor": "Skill complementarity", "impact": "Strong overlap", "score": 85.0},
                {"factor": "Working style", "impact": "Good alignment", "score": 80.0}
            ],
            detailed_analysis="Mock team fit analysis",
            cultural_fit_score=80.0,
            working_style_compatibility=78.0,
            skill_complementarity=85.0,
            team_dynamics_impact=75.0
        )
        
        self.advanced_matcher.career_analyzer = MagicMock(spec=CareerTrajectoryAnalyzer)
        self.advanced_matcher.career_analyzer.predict_career_trajectory.return_value = CareerTrajectoryResult(
            candidate_id="candidate123",
            job_id="job456",
            growth_potential_score=88.0,
            trajectory_alignment_score=85.0,
            skills_growth_opportunity=90.0,
            predicted_future_roles=["Director of Data Science", "VP of AI"],
            growth_timeline={"Director of Data Science": 3, "VP of AI": 6},
            detailed_analysis="Mock career trajectory analysis",
            development_areas=["Leadership", "Communication", "Strategic Planning"]
        )
    
    def _mock_get_by_id(self, collection, doc_id):
        """Mock implementation of vector store get_by_id."""
        if collection == "CandidateProfile" and doc_id == "candidate123":
            return self.candidate_data
        elif collection == "JobDescription" and doc_id == "job456":
            return self.job_data
        elif collection == "TeamProfile" and doc_id == "team123":
            return self.team_data
        return None
    
    def test_match_candidate_to_job(self):
        """Test matching a candidate to a job with all advanced features."""
        result = self.advanced_matcher.match_candidate_to_job(
            candidate_id="candidate123",
            job_id="job456",
            include_team_fit=True,
            include_career_trajectory=True,
            team_id="team123"
        )
        
        # Verify base matching was called
        self.mock_base_matcher.match_candidates.assert_called_once_with(
            job_id="job456",
            candidate_ids=["candidate123"],
            require_explanation=True
        )
        
        # Verify result has all components
        self.assertEqual(result.candidate_id, "candidate123")
        self.assertEqual(result.job_id, "job456")
        self.assertEqual(result.overall_score, 85.0)
        self.assertEqual(result.skill_match_score, 90.0)
        self.assertEqual(result.experience_match_score, 80.0)
        self.assertEqual(result.education_match_score, 75.0)
        
        # Verify bi-directional preferences were calculated
        self.assertIsNotNone(result.bi_directional_preferences)
        self.assertGreater(result.bi_directional_preferences.preference_alignment_score, 0)
        
        # Verify team fit was included
        self.assertIsNotNone(result.team_fit)
        self.assertEqual(result.team_fit.compatibility_score, 82.5)
        
        # Verify career trajectory was included
        self.assertIsNotNone(result.career_trajectory)
        self.assertEqual(result.career_trajectory.growth_potential_score, 88.0)
        
        # Verify detailed explanation was generated
        self.assertIsNotNone(result.detailed_explanation)
    
    def test_bi_directional_preferences(self):
        """Test bi-directional preference calculation."""
        # Calculate preferences directly
        preferences = self.advanced_matcher._analyze_bi_directional_preferences(
            self.candidate_data, self.job_data
        )
        
        # Verify basic structure
        self.assertIsInstance(preferences, BiDirectionalPreference)
        self.assertGreater(len(preferences.candidate_preferences), 0)
        self.assertGreater(len(preferences.company_preferences), 0)
        
        # Verify alignment score calculation
        self.assertGreaterEqual(preferences.preference_alignment_score, 0)
        self.assertLessEqual(preferences.preference_alignment_score, 100)
        
        # Print detailed results for inspection
        print(f"\nBi-directional preference alignment score: {preferences.preference_alignment_score:.1f}%")
        print(f"Candidate preferences: {json.dumps(preferences.candidate_preferences, indent=2)}")
        print(f"Company preferences: {json.dumps(preferences.company_preferences, indent=2)}")
    
    def test_infer_preferences(self):
        """Test inference of preferences from profile data."""
        # Test with candidate without explicit preferences
        candidate_without_prefs = dict(self.candidate_data)
        candidate_without_prefs.pop("preferences")
        
        inferred_prefs = self.advanced_matcher._infer_candidate_preferences(candidate_without_prefs)
        
        # Verify some preferences were inferred
        self.assertGreater(len(inferred_prefs), 0)
        print(f"\nInferred candidate preferences: {json.dumps(inferred_prefs, indent=2)}")
        
        # Test job preference inference
        job_without_prefs = dict(self.job_data)
        job_without_prefs.pop("preferences")
        
        inferred_job_prefs = self.advanced_matcher._infer_job_preferences(job_without_prefs)
        
        # Verify some preferences were inferred
        self.assertGreater(len(inferred_job_prefs), 0)
        print(f"Inferred job preferences: {json.dumps(inferred_job_prefs, indent=2)}")
    
    def test_match_candidates_to_job(self):
        """Test matching multiple candidates to a job."""
        # Mock more candidates
        self.mock_base_matcher.match_candidates.return_value = [
            MatchingResult(
                candidate_id="candidate123",
                job_id="job456",
                overall_score=85.0,
                skill_match_score=90.0,
                experience_match_score=80.0,
                education_match_score=75.0,
                explanation="Mock explanation 1",
                matching_id="match789"
            ),
            MatchingResult(
                candidate_id="candidate456",
                job_id="job456",
                overall_score=75.0,
                skill_match_score=80.0,
                experience_match_score=70.0,
                education_match_score=65.0,
                explanation="Mock explanation 2",
                matching_id="match987"
            )
        ]
        
        # Need to reset the advanced matcher to use the new mock
        self.advanced_matcher = AdvancedMatcher(
            base_matcher=self.mock_base_matcher,
            vector_store=self.mock_vector_store
        )
        
        # Mock individual match calls
        self.advanced_matcher.match_candidate_to_job = MagicMock()
        self.advanced_matcher.match_candidate_to_job.side_effect = [
            AdvancedMatchingResult(
                candidate_id="candidate123",
                job_id="job456",
                overall_score=85.0,
                matching_id="match789"
            ),
            AdvancedMatchingResult(
                candidate_id="candidate456",
                job_id="job456",
                overall_score=75.0,
                matching_id="match987"
            )
        ]
        
        results = self.advanced_matcher.match_candidates_to_job(
            job_id="job456",
            candidate_ids=["candidate123", "candidate456"],
            include_team_fit=True,
            include_career_trajectory=True
        )
        
        # Verify we got expected number of results
        self.assertEqual(len(results), 2)
        
        # Verify results are ordered by score
        self.assertEqual(results[0].overall_score, 85.0)
        self.assertEqual(results[1].overall_score, 75.0)
    
    def test_enhanced_explanation(self):
        """Test generation of enhanced explanations."""
        # Mock result with all components
        result = AdvancedMatchingResult(
            candidate_id="candidate123",
            job_id="job456",
            overall_score=85.0,
            skill_match_score=90.0,
            experience_match_score=80.0,
            education_match_score=75.0,
            explanation="Basic explanation",
            matching_id="match789"
        )
        
        # Add bi-directional preferences
        result.bi_directional_preferences = BiDirectionalPreference(
            candidate_preferences={"remote_work": 0.8, "growth_opportunities": 0.9},
            company_preferences={"remote_work": 0.7, "innovation": 0.9},
            preference_alignment_score=75.0
        )
        
        # Add team fit
        result.team_fit = TeamFitResult(
            team_id="team123",
            candidate_id="candidate123",
            compatibility_score=82.5,
            detailed_analysis="Team fit analysis text"
        )
        
        # Add career trajectory
        result.career_trajectory = CareerTrajectoryResult(
            candidate_id="candidate123",
            job_id="job456",
            growth_potential_score=88.0,
            detailed_analysis="Career trajectory analysis text"
        )
        
        # Generate enhanced explanation
        explanation = self.advanced_matcher._generate_enhanced_explanation(
            result, self.job_data, self.candidate_data
        )
        
        # Verify explanation structure
        self.assertIn("summary", explanation)
        self.assertIn("basic_explanation", explanation)
        self.assertIn("sections", explanation)
        self.assertIn("overall_recommendation", explanation)
        
        # Verify sections were created for each component
        self.assertEqual(len(explanation["sections"]), 3)  # Preferences, Team Fit, Career
        
        # Print summary for inspection
        print(f"\nEnhanced explanation summary: {explanation['summary']}")
        print(f"Recommendation: {explanation['overall_recommendation']}")


if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the tests
    unittest.main()
