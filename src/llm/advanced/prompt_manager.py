"""
Advanced Prompt Management for RecruitPro AI.

This module provides sophisticated prompt management and engineering techniques:
- Structured prompt templating for consistent interactions
- Chain-of-thought (CoT) prompting for complex reasoning
- Few-shot learning exemplar management
- Domain-specific prompt optimization
- Prompt versioning and evaluation
"""

import logging
import json
import re
import os
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
import uuid
import hashlib

from src.llm.advanced.context_manager import get_context_manager
from src.utils.config import DEBUG

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """
    Structured prompt template with metadata and versioning.
    """
    id: str
    name: str
    template: str
    version: str = "1.0"
    description: Optional[str] = None
    domain: str = "recruitment"
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    modified_at: Optional[float] = None
    parameters: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "version": self.version,
            "description": self.description,
            "domain": self.domain,
            "tags": self.tags,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "parameters": self.parameters,
            "examples": self.examples,
            "performance_metrics": self.performance_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            template=data["template"],
            version=data.get("version", "1.0"),
            description=data.get("description"),
            domain=data.get("domain", "recruitment"),
            tags=data.get("tags", []),
            created_at=data.get("created_at", time.time()),
            modified_at=data.get("modified_at"),
            parameters=data.get("parameters", []),
            examples=data.get("examples", []),
            performance_metrics=data.get("performance_metrics", {})
        )
    
    def format(self, **kwargs) -> str:
        """
        Format the template with provided parameters.
        Raises KeyError if a required parameter is missing.
        """
        # Validate that all required parameters are provided
        for param in self.parameters:
            if param not in kwargs:
                raise KeyError(f"Required parameter '{param}' missing")
        
        # Format template
        return self.template.format(**kwargs)
    
    def add_example(self, inputs: Dict[str, Any], output: str) -> None:
        """
        Add an example for few-shot learning.
        
        Args:
            inputs: Dictionary of input parameters
            output: Example output
        """
        self.examples.append({
            "inputs": inputs,
            "output": output,
            "added_at": time.time()
        })
        self.modified_at = time.time()
    
    def clear_examples(self) -> None:
        """Clear all examples."""
        self.examples = []
        self.modified_at = time.time()
    
    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Update performance metrics.
        
        Args:
            metrics: Dictionary of metrics to update
        """
        self.performance_metrics.update(metrics)
        self.modified_at = time.time()


class PromptManager:
    """
    Advanced prompt management system with optimization and versioning.
    
    Features:
    - Template management with versioning
    - Few-shot learning example organization
    - Chain-of-thought (CoT) prompting
    - Domain-specific prompt libraries
    - Prompt performance tracking
    - Context-aware prompt optimization
    """
    
    def __init__(self):
        """Initialize the prompt manager."""
        # Initialize templates library
        self.templates: Dict[str, PromptTemplate] = {}
        
        # Initialize default library with common prompt patterns
        self._initialize_default_library()
        
        # Get context manager for optimization
        self.context_manager = get_context_manager()
        
        # Tracking
        self.prompt_usage_stats: Dict[str, int] = {}
        
    def _initialize_default_library(self) -> None:
        """Initialize default prompt template library."""
        # Base recruitment templates
        templates = [
            PromptTemplate(
                id="base_resume_analysis",
                name="Base Resume Analysis",
                template=(
                    "Analyze the following resume against the job description.\n\n"
                    "Resume:\n{resume_text}\n\n"
                    "Job Description:\n{job_description}\n\n"
                    "Provide a structured analysis including:\n"
                    "1. Overall match percentage\n"
                    "2. Key matching skills\n"
                    "3. Missing skills\n"
                    "4. Experience relevance\n"
                    "5. Education relevance\n"
                    "6. Overall recommendation"
                ),
                version="1.0",
                description="Basic resume analysis against job description",
                domain="recruitment",
                tags=["resume", "analysis", "matching"],
                parameters=["resume_text", "job_description"]
            ),
            PromptTemplate(
                id="cot_resume_analysis",
                name="Chain-of-Thought Resume Analysis",
                template=(
                    "Analyze the following resume against the job description. "
                    "Let's think through this step by step:\n\n"
                    "Resume:\n{resume_text}\n\n"
                    "Job Description:\n{job_description}\n\n"
                    "Step 1: Identify key skills required by the job.\n"
                    "Step 2: Find matching skills in the resume.\n"
                    "Step 3: Identify missing critical skills.\n"
                    "Step 4: Evaluate experience relevance and duration.\n"
                    "Step 5: Consider education and certifications.\n"
                    "Step 6: Based on the steps above, calculate an overall match percentage.\n"
                    "Step 7: Formulate a final recommendation.\n\n"
                    "Follow this step-by-step approach in your analysis."
                ),
                version="1.0",
                description="Resume analysis using chain-of-thought reasoning",
                domain="recruitment",
                tags=["resume", "analysis", "matching", "CoT"],
                parameters=["resume_text", "job_description"]
            ),
            PromptTemplate(
                id="skill_extraction",
                name="Skill Extraction",
                template=(
                    "Extract all professional skills from the following text. "
                    "Include both technical skills and soft skills.\n\n"
                    "Text:\n{text}\n\n"
                    "Format your response as JSON:\n"
                    "{\n"
                    '  "technical_skills": ["skill1", "skill2", ...],\n'
                    '  "soft_skills": ["skill1", "skill2", ...],\n'
                    '  "skill_levels": [\n'
                    '    {"skill": "skill1", "level": "beginner|intermediate|expert", "evidence": "text evidence"}\n'
                    "  ]\n"
                    "}"
                ),
                version="1.0",
                description="Extract skills from text with levels and evidence",
                domain="recruitment",
                tags=["skills", "extraction"],
                parameters=["text"]
            ),
            PromptTemplate(
                id="context_aware_matching",
                name="Context-Aware Matching",
                template=(
                    "Use the following context information along with the resume and job description "
                    "to provide a more informed matching analysis.\n\n"
                    "Context:\n{context}\n\n"
                    "Resume:\n{resume_text}\n\n"
                    "Job Description:\n{job_description}\n\n"
                    "Based on this complete information, provide a detailed matching analysis."
                ),
                version="1.0",
                description="Resume-job matching with additional context",
                domain="recruitment",
                tags=["resume", "matching", "context"],
                parameters=["context", "resume_text", "job_description"]
            ),
            PromptTemplate(
                id="multilingual_resume_analysis",
                name="Multilingual Resume Analysis",
                template=(
                    "Analyze the following resume in {language} against the job description.\n\n"
                    "Resume:\n{resume_text}\n\n"
                    "Job Description:\n{job_description}\n\n"
                    "Provide your analysis in {output_language}. Include:\n"
                    "1. Overall match percentage\n"
                    "2. Key matching skills\n"
                    "3. Missing skills\n"
                    "4. Experience relevance\n"
                    "5. Education relevance\n"
                    "6. Overall recommendation"
                ),
                version="1.0",
                description="Resume analysis supporting multiple languages",
                domain="recruitment",
                tags=["resume", "analysis", "multilingual"],
                parameters=["resume_text", "job_description", "language", "output_language"]
            ),
            PromptTemplate(
                id="team_fit_analysis",
                name="Team Fit Analysis",
                template=(
                    "Analyze how well the candidate would fit with the existing team, "
                    "based on their resume and the team profile.\n\n"
                    "Candidate Resume:\n{resume_text}\n\n"
                    "Team Profile:\n{team_profile}\n\n"
                    "Consider the following dimensions in your analysis:\n"
                    "1. Skill complementarity\n"
                    "2. Working style compatibility\n"
                    "3. Experience diversity\n"
                    "4. Cultural alignment\n"
                    "5. Potential team dynamics\n\n"
                    "Provide a compatibility score (0-100) and detailed explanation."
                ),
                version="1.0",
                description="Team fit analysis for a candidate",
                domain="recruitment",
                tags=["team", "fit", "analysis"],
                parameters=["resume_text", "team_profile"]
            )
        ]
        
        # Add templates to library
        for template in templates:
            self.templates[template.id] = template
            
        logger.info(f"Initialized default prompt library with {len(templates)} templates")
        
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a prompt template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def add_template(self, template: PromptTemplate) -> None:
        """
        Add a prompt template to the library.
        
        Args:
            template: PromptTemplate to add
        """
        self.templates[template.id] = template
        logger.info(f"Added template: {template.id} ({template.name})")
    
    def create_template(
        self,
        name: str,
        template: str,
        description: Optional[str] = None,
        domain: str = "recruitment",
        tags: Optional[List[str]] = None,
        parameters: Optional[List[str]] = None
    ) -> PromptTemplate:
        """
        Create and add a new prompt template.
        
        Args:
            name: Template name
            template: Template text
            description: Optional description
            domain: Domain (default: recruitment)
            tags: Optional tags
            parameters: Optional list of required parameters
            
        Returns:
            Created PromptTemplate
        """
        # Auto-detect parameters if not provided
        if parameters is None:
            # Find parameters like {param_name} in the template
            param_pattern = r'\{([a-zA-Z0-9_]+)\}'
            parameters = list(set(re.findall(param_pattern, template)))
        
        # Create template ID
        template_id = f"{name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Create template
        new_template = PromptTemplate(
            id=template_id,
            name=name,
            template=template,
            description=description,
            domain=domain,
            tags=tags or [],
            parameters=parameters,
            created_at=time.time()
        )
        
        # Add to library
        self.add_template(new_template)
        
        return new_template
    
    def update_template(
        self,
        template_id: str,
        **updates
    ) -> Optional[PromptTemplate]:
        """
        Update an existing template.
        
        Args:
            template_id: Template ID
            **updates: Fields to update
            
        Returns:
            Updated template or None if not found
        """
        template = self.get_template(template_id)
        if not template:
            return None
            
        # Update fields
        for field, value in updates.items():
            if hasattr(template, field):
                setattr(template, field, value)
                
        # Update modified timestamp
        template.modified_at = time.time()
        
        # If template text is updated, auto-detect parameters
        if "template" in updates:
            param_pattern = r'\{([a-zA-Z0-9_]+)\}'
            template.parameters = list(set(re.findall(param_pattern, template.template)))
            
        logger.info(f"Updated template: {template_id}")
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a prompt template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Deleted template: {template_id}")
            return True
        return False
    
    def create_few_shot_prompt(
        self,
        template_id: str,
        examples: List[Dict[str, Any]],
        query_params: Dict[str, Any]
    ) -> str:
        """
        Create a few-shot prompt with examples and query.
        
        Args:
            template_id: Template ID
            examples: List of example dictionaries with 'inputs' and 'output'
            query_params: Parameters for the query
            
        Returns:
            Formatted few-shot prompt
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Format examples
        examples_text = []
        for i, example in enumerate(examples):
            example_prompt = template.format(**example["inputs"])
            examples_text.append(f"Example {i+1}:\n{example_prompt}\n\nResponse {i+1}:\n{example['output']}\n")
            
        # Format query
        query_prompt = template.format(**query_params)
        
        # Combine
        full_prompt = (
            "I'll provide some examples followed by a query. "
            "Please respond to the query following the pattern shown in the examples.\n\n"
            f"{''.join(examples_text)}\n"
            f"Query:\n{query_prompt}\n\n"
            "Your response:"
        )
        
        # Track usage
        self._track_template_usage(template_id)
        
        return full_prompt
    
    def create_cot_prompt(
        self,
        base_prompt: str,
        num_steps: int = 5,
        context: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> str:
        """
        Create a chain-of-thought prompt to guide step-by-step reasoning.
        
        Args:
            base_prompt: Base prompt text
            num_steps: Number of reasoning steps
            context: Optional context information
            output_format: Optional output format instructions
            
        Returns:
            Chain-of-thought prompt
        """
        # Add context if provided
        if context:
            prompt = f"Context:\n{context}\n\n{base_prompt}"
        else:
            prompt = base_prompt
            
        # Add chain-of-thought instructions
        cot_prompt = (
            f"{prompt}\n\n"
            "Let's think about this step by step to ensure we reach the correct answer.\n\n"
        )
        
        # Add numbered steps
        for i in range(1, num_steps + 1):
            cot_prompt += f"Step {i}: [Reasoning for step {i}]\n\n"
            
        # Add conclusion
        cot_prompt += (
            "Final conclusion based on the steps above:\n"
            "[Your final answer here]\n\n"
        )
        
        # Add output format if provided
        if output_format:
            cot_prompt += f"Please format your output as follows:\n{output_format}"
            
        return cot_prompt
    
    def create_optimized_prompt(
        self,
        template_id: str,
        params: Dict[str, Any],
        query: str,
        domain: str = "recruitment",
        max_context_tokens: int = 2000
    ) -> str:
        """
        Create a context-optimized prompt using relevant information.
        
        Args:
            template_id: Template ID
            params: Template parameters
            query: Query for context retrieval
            domain: Domain for context filtering
            max_context_tokens: Maximum tokens for context
            
        Returns:
            Optimized prompt with relevant context
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Get relevant context
        context_info = self.context_manager.get_relevant_context(
            query=query,
            domain=domain,
            max_tokens=max_context_tokens
        )
        
        # Add context to parameters
        context_params = params.copy()
        context_params["context"] = context_info["context_text"]
        
        # Format template
        prompt = template.format(**context_params)
        
        # Track usage
        self._track_template_usage(template_id)
        
        return prompt
    
    def format_prompt(
        self,
        template_id: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Format a prompt template with parameters.
        
        Args:
            template_id: Template ID
            params: Template parameters
            
        Returns:
            Formatted prompt
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Format template
        prompt = template.format(**params)
        
        # Track usage
        self._track_template_usage(template_id)
        
        return prompt
    
    def _track_template_usage(self, template_id: str) -> None:
        """Track template usage."""
        if template_id not in self.prompt_usage_stats:
            self.prompt_usage_stats[template_id] = 0
        self.prompt_usage_stats[template_id] += 1
        
    def get_usage_stats(self) -> Dict[str, int]:
        """Get template usage statistics."""
        return self.prompt_usage_stats
    
    def export_templates(self, filepath: str) -> None:
        """
        Export templates to a JSON file.
        
        Args:
            filepath: Path to save the templates
        """
        templates_dict = {
            tid: template.to_dict() 
            for tid, template in self.templates.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(templates_dict, f, indent=2)
            
        logger.info(f"Exported {len(templates_dict)} templates to {filepath}")
    
    def import_templates(self, filepath: str) -> int:
        """
        Import templates from a JSON file.
        
        Args:
            filepath: Path to load templates from
            
        Returns:
            Number of templates imported
        """
        with open(filepath, 'r') as f:
            templates_dict = json.load(f)
            
        count = 0
        for tid, template_data in templates_dict.items():
            template = PromptTemplate.from_dict(template_data)
            self.templates[template.id] = template
            count += 1
            
        logger.info(f"Imported {count} templates from {filepath}")
        return count


# Singleton instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """
    Get or create the PromptManager singleton.
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
