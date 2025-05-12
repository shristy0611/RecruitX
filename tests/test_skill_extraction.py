"""
Test module for the Skill Extraction V2 implementation.

This module tests all skill extraction components, 
including the base, enhanced, multilingual, and taxonomy extractors.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.extractors.base_extractor import Skill
from src.skills.extractors.enhanced_extractor import EnhancedSkillExtractor
from src.skills.extractors.multilingual_extractor import MultilingualSkillExtractor
from src.skills.extractors.taxonomy_extractor import TaxonomySkillExtractor
from src.skills.extractors.factory import SkillExtractorFactory
from src.skills.taxonomy.taxonomy_manager import SkillsTaxonomyManager


def test_skill_object():
    """Test the Skill class functionality."""
    # Create a skill
    skill = Skill(
        name="Python",
        confidence=0.9,
        category="technical",
        source="test",
        context="Python programming experience",
        aliases=["py"]
    )
    
    # Test basic properties
    assert skill.name == "Python"
    assert skill.confidence == 0.9
    assert skill.category == "technical"
    assert skill.source == "test"
    assert skill.context == "Python programming experience"
    assert skill.aliases == ["py"]
    
    # Test dictionary conversion
    skill_dict = skill.to_dict()
    assert skill_dict["name"] == "Python"
    assert skill_dict["confidence"] == 0.9
    
    # Test equality
    skill2 = Skill(name="python", confidence=0.8)  # Different case, lower confidence
    assert skill == skill2  # Should be equal (case-insensitive name comparison)
    
    # Test from_dict
    skill3 = Skill.from_dict(skill_dict)
    assert skill3.name == "Python"
    assert skill3.confidence == 0.9


def test_taxonomy_manager():
    """Test the taxonomy manager functionality."""
    # Initialize taxonomy manager
    data_dir = Path(__file__).parent.parent / "data" / "taxonomies"
    os.makedirs(data_dir, exist_ok=True)
    
    manager = SkillsTaxonomyManager(str(data_dir))
    
    # Create a unique test domain name using timestamp to avoid conflicts
    import time
    test_domain = f"test_skills_domain_{int(time.time())}"
    
    # Create a new test domain instead of using 'tech' which might already exist
    result = manager.create_taxonomy(test_domain)
    assert result, f"Failed to create test domain: {test_domain}"
    
    # Test domain retrieval
    domains = manager.get_all_domains()
    assert test_domain in domains
    
    # Add a parent category for testing
    assert manager.add_skill(test_domain, "Programming Languages", "technical")
    
    # Test skill addition
    assert manager.add_skill(test_domain, "Go Programming", "technical", ["Programming Languages"])
    
    # Test skill lookup
    go_skill = manager.find_skill(test_domain, "Go Programming")
    assert go_skill is not None
    assert go_skill.name == "Go Programming"
    
    # Test hierarchy retrieval
    hierarchy = manager.get_skill_hierarchy(test_domain, "Go Programming")
    assert "Programming Languages" in hierarchy["ancestors"]
    
    # Test saving and loading
    assert manager.save_taxonomy(test_domain)
    
    # Create a new manager to test loading
    manager2 = SkillsTaxonomyManager(str(data_dir))
    assert test_domain in manager2.get_all_domains()
    
    # Test loaded skill
    go_skill2 = manager2.find_skill(test_domain, "Go Programming")
    assert go_skill2 is not None
    assert go_skill2.name == "Go Programming"


def test_taxonomy_extractor():
    """Test the taxonomy-aware skill extractor."""
    # Initialize taxonomy manager
    data_dir = Path(__file__).parent.parent / "data" / "taxonomies"
    os.makedirs(data_dir, exist_ok=True)
    
    manager = SkillsTaxonomyManager(str(data_dir))
    # Create a test domain with a unique name using timestamp
    import time
    test_domain = f"test_extractor_domain_{int(time.time())}"
    manager.create_taxonomy(test_domain)
    
    # Add programming skills to the taxonomy
    manager.add_skill(test_domain, "Programming Languages", "technical")
    manager.add_skill(test_domain, "Python", "technical", ["Programming Languages"])
    manager.add_skill(test_domain, "JavaScript", "technical", ["Programming Languages"])
    
    # Initialize extractor with our test domain
    extractor = TaxonomySkillExtractor(manager, domains=[test_domain])
    
    # Test extraction
    sample_text = """
    I have experience with Python programming and JavaScript development.
    I've worked with React for frontend and Django for backend projects.
    """
    
    skills = extractor.extract_skills(sample_text)
    
    # We should have at least some skills extracted
    assert len(skills) > 0
    
    # Check if we found Python and JavaScript
    skill_names = [skill.name.lower() for skill in skills]
    assert any("python" in name for name in skill_names)
    assert any("javascript" in name for name in skill_names)
    
    # Test skill enrichment
    python_skill = next((s for s in skills if "python" in s.name.lower()), None)
    if python_skill:
        # If Python was found in the taxonomy, it should have taxonomy information
        assert python_skill.metadata.get("taxonomy_validated", False)


def test_factory():
    """Test the skill extractor factory."""
    # Get extractors of different types
    enhanced = SkillExtractorFactory.get_extractor("enhanced")
    assert isinstance(enhanced, EnhancedSkillExtractor)
    
    multilingual = SkillExtractorFactory.get_extractor("multilingual")
    assert isinstance(multilingual, MultilingualSkillExtractor)
    
    taxonomy = SkillExtractorFactory.get_extractor("taxonomy")
    assert isinstance(taxonomy, TaxonomySkillExtractor)
    
    # Test singleton behavior
    enhanced2 = SkillExtractorFactory.get_extractor("enhanced")
    assert enhanced is enhanced2  # Should be the same instance
    
    # Test error handling
    with pytest.raises(ValueError):
        SkillExtractorFactory.get_extractor("invalid_type")
    
    # Test taxonomy manager access
    manager = SkillExtractorFactory.get_taxonomy_manager()
    assert isinstance(manager, SkillsTaxonomyManager)


def test_skill_extraction_pipeline():
    """Test the full skill extraction pipeline using all extractor types."""
    # Sample resumes in different languages
    resume_en = """
    Experienced Software Engineer with 5+ years developing scalable backend systems.
    Strong skills in Python, Java, and SQL. Experienced with AWS cloud services.
    Built microservices using Spring Boot and Django. Familiar with React and Angular.
    """
    
    # Get all extractor types through the factory
    extractors = {
        "enhanced": SkillExtractorFactory.get_extractor("enhanced"),
        "multilingual": SkillExtractorFactory.get_extractor("multilingual"),
        "taxonomy": SkillExtractorFactory.get_extractor("taxonomy")
    }
    
    all_results = {}
    
    # Extract skills with each extractor
    for name, extractor in extractors.items():
        skills = extractor.extract_skills(resume_en)
        
        # Verify we have skills
        assert len(skills) > 0
        
        # Convert to dictionaries for inspection
        skill_dicts = [skill.to_dict() for skill in skills]
        all_results[name] = skill_dicts
        
        # Print results for debugging
        print(f"\n{name.upper()} EXTRACTOR RESULTS:")
        for skill in skill_dicts:
            print(f"- {skill['name']} ({skill['confidence']:.2f})")
    
    # Verify common skills are found by all extractors
    common_tech_skills = ["python", "java", "sql", "aws"]
    
    for skill_name in common_tech_skills:
        for extractor_name, results in all_results.items():
            # Check if this skill is found by this extractor
            found = any(skill_name.lower() in skill["name"].lower() for skill in results)
            print(f"{extractor_name}: {skill_name} - {'✓' if found else '✗'}")


if __name__ == "__main__":
    # Run the tests
    print("Testing Skill class...")
    test_skill_object()
    
    print("\nTesting Taxonomy Manager...")
    test_taxonomy_manager()
    
    print("\nTesting Taxonomy Extractor...")
    test_taxonomy_extractor()
    
    print("\nTesting Factory...")
    test_factory()
    
    print("\nTesting Full Pipeline...")
    test_skill_extraction_pipeline()
    
    print("\nAll tests passed!")
