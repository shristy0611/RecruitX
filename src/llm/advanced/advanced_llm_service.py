"""
Advanced LLM Integration Service for RecruitPro AI.

This module provides a sophisticated LLM integration service that leverages
advanced prompting techniques, context optimization, and result caching to
enhance performance, reduce costs, and improve response quality.

Key features:
- Enhanced Gemini Pro API integration with specialized prompting
- Advanced multilingual support with Gemma 3
- Query optimization and result caching
- Adaptation to different LLM strengths
- Fallback strategy handling
"""

import json
import logging
import time
import random
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from threading import Lock
from functools import lru_cache

import numpy as np

from src.llm.gemini_service import GeminiService, get_gemini_service
from src.llm.gemma_service import GemmaService, get_gemma_service
from src.llm.advanced.context_manager import get_context_manager
from src.llm.advanced.prompt_manager import get_prompt_manager, PromptTemplate
from src.utils.config import (
    DEBUG,
    GEMINI_PRO_MODEL,
    GEMINI_THINKING_MODEL,
    GEMINI_API_KEYS,
    GEMMA_API_KEYS,
    GEMMA_MODEL
)

logger = logging.getLogger(__name__)


class ModelSelectionStrategy:
    """Strategy for selecting the optimal model for a given task."""
    
    COST_OPTIMIZED = "cost_optimized"  # Prefer cheaper models
    QUALITY_OPTIMIZED = "quality_optimized"  # Prefer higher quality models
    SPEED_OPTIMIZED = "speed_optimized"  # Prefer faster models
    BALANCED = "balanced"  # Balance cost, quality, and speed
    
    MODEL_CAPABILITIES = {
        GEMINI_PRO_MODEL: {
            "quality": 0.9,
            "speed": 0.8,
            "cost": 0.6,  # Higher cost
            "multilingual": 0.85,
            "reasoning": 0.9,
            "instruction_following": 0.9,
            "code_generation": 0.85,
            "creative_tasks": 0.9
        },
        GEMINI_THINKING_MODEL: {
            "quality": 0.85,
            "speed": 0.75,
            "cost": 0.65,
            "multilingual": 0.8,
            "reasoning": 0.95,  # Better at reasoning/CoT
            "instruction_following": 0.85,
            "code_generation": 0.8,
            "creative_tasks": 0.85
        },
        GEMMA_MODEL: {
            "quality": 0.8,
            "speed": 0.9,  # Faster
            "cost": 0.9,  # Lower cost
            "multilingual": 0.75,
            "reasoning": 0.8,
            "instruction_following": 0.8,
            "code_generation": 0.7,
            "creative_tasks": 0.75
        }
    }
    
    @classmethod
    def select_model(
        cls,
        task_type: str,
        strategy: str = BALANCED,
        available_models: Optional[List[str]] = None
    ) -> str:
        """
        Select optimal model based on task and strategy.
        
        Args:
            task_type: Task type (reasoning, multilingual, code_generation, creative_tasks)
            strategy: Selection strategy
            available_models: List of available models
            
        Returns:
            Selected model name
        """
        if available_models is None:
            # Default to all known models
            available_models = list(cls.MODEL_CAPABILITIES.keys())
            
        # Filter to only available models
        candidates = {
            model: capabilities 
            for model, capabilities in cls.MODEL_CAPABILITIES.items()
            if model in available_models
        }
        
        if not candidates:
            # Return first available model as fallback
            return available_models[0] if available_models else GEMINI_PRO_MODEL
            
        # Apply strategy weights
        if strategy == cls.COST_OPTIMIZED:
            weights = {"cost": 0.7, "quality": 0.2, "speed": 0.1, task_type: 0.3}
        elif strategy == cls.QUALITY_OPTIMIZED:
            weights = {"quality": 0.7, "cost": 0.1, "speed": 0.2, task_type: 0.5}
        elif strategy == cls.SPEED_OPTIMIZED:
            weights = {"speed": 0.7, "quality": 0.2, "cost": 0.1, task_type: 0.3}
        else:  # BALANCED
            weights = {"quality": 0.33, "cost": 0.33, "speed": 0.34, task_type: 0.4}
            
        # Calculate weighted scores
        scores = {}
        for model, capabilities in candidates.items():
            score = 0
            for aspect, weight in weights.items():
                if aspect in capabilities:
                    score += capabilities[aspect] * weight
            scores[model] = score
            
        # Return model with highest score
        return max(scores, key=scores.get)


class AdvancedLLMService:
    """
    Advanced LLM Integration Service with sophisticated capabilities.
    
    Features:
    - Intelligent model selection for different tasks
    - Context-aware prompting with RAG integration
    - Result caching and memoization
    - Prompt optimization
    - Parallel query execution for complex tasks
    - Fallback strategies for robustness
    - Performance metrics tracking
    """
    
    def __init__(self):
        """Initialize the Advanced LLM Service."""
        # Initialize services
        try:
            self.gemini_service = get_gemini_service()
            logger.info("Initialized Gemini service for advanced LLM integration")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
            
        try:
            self.gemma_service = get_gemma_service()
            logger.info("Initialized Gemma service for advanced LLM integration")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemma service: {e}")
            self.gemma_service = None
            
        # Initialize managers
        self.context_manager = get_context_manager()
        self.prompt_manager = get_prompt_manager()
        
        # Initialize locks
        self.metrics_lock = Lock()
        
        # Initialize API availability
        self.gemini_available = self.gemini_service is not None and bool(GEMINI_API_KEYS)
        self.gemma_available = self.gemma_service is not None and bool(GEMMA_API_KEYS)
        
        # Track available models
        self.available_models = []
        if self.gemini_available:
            self.available_models.extend([GEMINI_PRO_MODEL, GEMINI_THINKING_MODEL])
        if self.gemma_available:
            self.available_models.append(GEMMA_MODEL)
            
        logger.info(f"Available models: {', '.join(self.available_models)}")
        
        # Initialize metrics
        self.metrics = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "total_tokens": 0,
            "total_response_time_ms": 0,
            "model_usage": {model: 0 for model in self.available_models}
        }
    
    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_cache: bool = True,
        strategy: str = ModelSelectionStrategy.BALANCED,
        task_type: str = "reasoning",
        max_output_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate content using the optimal LLM.
        
        Args:
            prompt: Input prompt text
            model: Optional specific model to use
            use_cache: Whether to use result caching
            strategy: Model selection strategy
            task_type: Type of task for model selection
            max_output_tokens: Maximum output tokens
            temperature: Temperature for sampling
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            Generated content
        """
        self._update_metric("requests", 1)
        
        # Check cache if enabled
        if use_cache:
            cached_result = self.context_manager.get_memoized_result(prompt, model or "auto")
            if cached_result:
                self._update_metric("cache_hits", 1)
                self._update_metric("successful_requests", 1)
                return cached_result
        
        # Select model if not specified
        selected_model = model
        if not selected_model:
            selected_model = ModelSelectionStrategy.select_model(
                task_type=task_type,
                strategy=strategy,
                available_models=self.available_models
            )
            
        if not selected_model or selected_model not in self.available_models:
            selected_model = self.available_models[0] if self.available_models else GEMINI_PRO_MODEL
        
        # Record start time for metrics
        start_time = time.time()
        
        try:
            # Route to appropriate service
            if selected_model in [GEMINI_PRO_MODEL, GEMINI_THINKING_MODEL] and self.gemini_service:
                result = self.gemini_service.generate_content(
                    prompt=prompt,
                    model=selected_model,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k
                )
            elif selected_model == GEMMA_MODEL and self.gemma_service:
                result = self.gemma_service.generate_content(
                    prompt=prompt,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k
                )
            else:
                raise ValueError(f"No service available for model: {selected_model}")
                
            # Update metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            self._update_metric("total_response_time_ms", elapsed_ms)
            self._update_metric("successful_requests", 1)
            self._update_metric(f"model_usage.{selected_model}", 1)
            
            # Estimate token count (rough approximation)
            prompt_tokens = len(prompt) // 4
            result_tokens = len(result) // 4
            total_tokens = prompt_tokens + result_tokens
            self._update_metric("total_tokens", total_tokens)
            
            # Cache result if enabled
            if use_cache:
                self.context_manager.memoize_result(prompt, result, selected_model)
                
            return result
                
        except Exception as e:
            logger.error(f"Error generating content with {selected_model}: {e}")
            self._update_metric("failed_requests", 1)
            
            # Try fallback if available and not already using fallback
            if model is None:  # Only auto-fallback if model wasn't explicitly specified
                return self._fallback_generate_content(
                    prompt=prompt,
                    original_model=selected_model,
                    task_type=task_type,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature
                )
            
            # Reraise if no fallback or fallback failed
            raise
    
    def generate_with_prompt_template(
        self,
        template_id: str,
        params: Dict[str, Any],
        model: Optional[str] = None,
        use_cache: bool = True,
        strategy: str = ModelSelectionStrategy.BALANCED,
        task_type: str = "reasoning"
    ) -> str:
        """
        Generate content using a prompt template.
        
        Args:
            template_id: Prompt template ID
            params: Template parameters
            model: Optional specific model to use
            use_cache: Whether to use result caching
            strategy: Model selection strategy
            task_type: Type of task for model selection
            
        Returns:
            Generated content
        """
        # Format prompt from template
        try:
            prompt = self.prompt_manager.format_prompt(template_id, params)
        except Exception as e:
            logger.error(f"Error formatting prompt template {template_id}: {e}")
            raise
            
        # Generate content
        return self.generate_content(
            prompt=prompt,
            model=model,
            use_cache=use_cache,
            strategy=strategy,
            task_type=task_type
        )
    
    def generate_with_context(
        self,
        query: str,
        template_id: str,
        params: Dict[str, Any],
        domain: str = "recruitment",
        model: Optional[str] = None,
        use_cache: bool = True,
        strategy: str = ModelSelectionStrategy.BALANCED,
        task_type: str = "reasoning"
    ) -> Dict[str, Any]:
        """
        Generate content with context-enhanced prompting.
        
        Args:
            query: Query for context retrieval
            template_id: Prompt template ID
            params: Template parameters
            domain: Domain for context filtering
            model: Optional specific model to use
            use_cache: Whether to use result caching
            strategy: Model selection strategy
            task_type: Type of task for model selection
            
        Returns:
            Dictionary with generated content and context info:
            {
                "content": str,  # Generated content
                "context_info": Dict,  # Context retrieval info
                "model": str,  # Model used
                "cache_hit": bool  # Whether result was from cache
            }
        """
        # Get template
        template = self.prompt_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Get relevant context
        context_info = self.context_manager.get_relevant_context(
            query=query,
            domain=domain
        )
        
        # Check if context was found
        context_text = context_info.get("context_text", "")
        
        # Add context to parameters if template has context parameter
        context_params = params.copy()
        if "context" in template.parameters:
            context_params["context"] = context_text
            
        # Generate content
        formatted_prompt = self.prompt_manager.format_prompt(template_id, context_params)
        
        # Check cache before generating
        cache_hit = False
        if use_cache:
            cached_result = self.context_manager.get_memoized_result(
                formatted_prompt, model or "auto"
            )
            if cached_result:
                content = cached_result
                cache_hit = True
                self._update_metric("cache_hits", 1)
                self._update_metric("successful_requests", 1)
            else:
                content = self.generate_content(
                    prompt=formatted_prompt,
                    model=model,
                    use_cache=use_cache,
                    strategy=strategy,
                    task_type=task_type
                )
        else:
            content = self.generate_content(
                prompt=formatted_prompt,
                model=model,
                use_cache=False,
                strategy=strategy,
                task_type=task_type
            )
            
        # Get the model that was actually used (for API response)
        used_model = model
        if not used_model:
            used_model = ModelSelectionStrategy.select_model(
                task_type=task_type,
                strategy=strategy,
                available_models=self.available_models
            )
            
        return {
            "content": content,
            "context_info": context_info,
            "model": used_model,
            "cache_hit": cache_hit
        }
    
    def generate_chain_of_thought(
        self,
        prompt: str,
        num_steps: int = 5,
        context: Optional[str] = None,
        model: Optional[str] = None,
        strategy: str = ModelSelectionStrategy.QUALITY_OPTIMIZED,
        extraction_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using chain-of-thought reasoning.
        
        Args:
            prompt: Base prompt text
            num_steps: Number of reasoning steps
            context: Optional context information
            model: Optional specific model to use
            strategy: Model selection strategy
            extraction_template: Optional template for extracting final answer
            
        Returns:
            Dictionary with:
            {
                "reasoning": str,  # Full chain-of-thought reasoning
                "steps": List[str],  # Individual reasoning steps
                "conclusion": str,  # Extracted conclusion
                "model": str  # Model used
            }
        """
        # Create chain-of-thought prompt
        cot_prompt = self.prompt_manager.create_cot_prompt(
            base_prompt=prompt,
            num_steps=num_steps,
            context=context
        )
        
        # Generate content with reasoning-optimized settings
        reasoning = self.generate_content(
            prompt=cot_prompt,
            model=model,
            strategy=strategy,
            task_type="reasoning",
            temperature=0.5,  # Lower temperature for more focused reasoning
            max_output_tokens=2048  # Longer output for detailed reasoning
        )
        
        # Extract reasoning steps and conclusion
        steps = self._extract_reasoning_steps(reasoning)
        conclusion = self._extract_conclusion(reasoning)
        
        # If no conclusion found and extraction template provided, get it
        if not conclusion and extraction_template:
            extraction_prompt = extraction_template.format(
                reasoning=reasoning
            )
            
            conclusion = self.generate_content(
                prompt=extraction_prompt,
                model=model,
                strategy=ModelSelectionStrategy.QUALITY_OPTIMIZED,
                temperature=0.3,  # Low temperature for fact extraction
                max_output_tokens=256  # Shorter output for conclusion only
            )
            
        # Get the model that was actually used
        used_model = model
        if not used_model:
            used_model = ModelSelectionStrategy.select_model(
                task_type="reasoning",
                strategy=strategy,
                available_models=self.available_models
            )
            
        return {
            "reasoning": reasoning,
            "steps": steps,
            "conclusion": conclusion,
            "model": used_model
        }
    
    def generate_multilingual(
        self,
        prompt: str,
        language: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate content optimized for a specific language.
        
        Args:
            prompt: Input prompt text
            language: Target language code (ISO 639-1)
            model: Optional specific model to use
            use_cache: Whether to use result caching
            
        Returns:
            Generated content in specified language
        """
        # Add language instruction if not already included
        if not any(marker in prompt.lower() for marker in [
            f"in {language}",
            f"respond in {language}",
            f"answer in {language}",
            f"output in {language}"
        ]):
            prompt = f"{prompt}\n\nPlease respond in {language}."
            
        # Select model optimized for multilingual tasks
        if not model:
            model = ModelSelectionStrategy.select_model(
                task_type="multilingual",
                strategy=ModelSelectionStrategy.QUALITY_OPTIMIZED,
                available_models=self.available_models
            )
            
        # Generate content
        return self.generate_content(
            prompt=prompt,
            model=model,
            use_cache=use_cache,
            task_type="multilingual"
        )
    
    def parallel_query(
        self,
        prompts: List[str],
        combine_results: bool = True,
        combination_prompt: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> Union[List[str], str]:
        """
        Execute multiple prompts in parallel and optionally combine results.
        
        Args:
            prompts: List of prompts to execute
            combine_results: Whether to combine results
            combination_prompt: Optional template for combining results
            models: Optional list of models to use (one per prompt)
            
        Returns:
            List of results or combined result string
        """
        if not prompts:
            return [] if not combine_results else ""
            
        # Validate models list if provided
        if models and len(models) != len(prompts):
            raise ValueError("Number of models must match number of prompts")
            
        # Generate content for each prompt
        results = []
        for i, prompt in enumerate(prompts):
            model = models[i] if models else None
            
            try:
                result = self.generate_content(prompt=prompt, model=model)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in parallel query for prompt {i}: {e}")
                results.append(f"Error: {str(e)}")
                
        # Return individual results if not combining
        if not combine_results:
            return results
            
        # Combine results
        if combination_prompt:
            # Use provided template
            combined_prompt = combination_prompt.format(
                results=json.dumps(results)
            )
            
            return self.generate_content(
                prompt=combined_prompt,
                strategy=ModelSelectionStrategy.QUALITY_OPTIMIZED
            )
        else:
            # Simple concatenation
            return "\n\n".join([f"Result {i+1}:\n{result}" for i, result in enumerate(results)])
    
    def _fallback_generate_content(
        self,
        prompt: str,
        original_model: str,
        task_type: str,
        max_output_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """
        Attempt to generate content using fallback models.
        
        Args:
            prompt: Input prompt text
            original_model: Original model that failed
            task_type: Type of task
            max_output_tokens: Maximum output tokens
            temperature: Temperature for sampling
            
        Returns:
            Generated content from fallback model
        """
        # Get fallback models (all except the original)
        fallback_models = [m for m in self.available_models if m != original_model]
        
        if not fallback_models:
            raise ValueError("No fallback models available")
            
        # Try each fallback model
        errors = []
        for model in fallback_models:
            try:
                if model in [GEMINI_PRO_MODEL, GEMINI_THINKING_MODEL] and self.gemini_service:
                    result = self.gemini_service.generate_content(
                        prompt=prompt,
                        model=model,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature
                    )
                    
                    # Update metrics
                    self._update_metric(f"model_usage.{model}", 1)
                    return result
                    
                elif model == GEMMA_MODEL and self.gemma_service:
                    result = self.gemma_service.generate_content(
                        prompt=prompt,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature
                    )
                    
                    # Update metrics
                    self._update_metric(f"model_usage.{model}", 1)
                    return result
            except Exception as e:
                errors.append(f"{model}: {str(e)}")
                continue
                
        # If all fallbacks failed, raise composite error
        raise ValueError(f"All fallback models failed. Errors: {'; '.join(errors)}")
    
    def _extract_reasoning_steps(self, reasoning: str) -> List[str]:
        """Extract reasoning steps from chain-of-thought output."""
        steps = []
        
        # Look for "Step X:" patterns
        step_pattern = r"Step\s+\d+\s*:([^\n]*(?:\n(?!Step\s+\d+\s*:)[^\n]*)*)"
        step_matches = re.findall(step_pattern, reasoning, re.IGNORECASE)
        
        if step_matches:
            steps = [step.strip() for step in step_matches]
        else:
            # Fallback: try to split by numbered lines
            number_pattern = r"\n\s*\d+\.\s+([^\n]*(?:\n(?!\s*\d+\.\s+)[^\n]*)*)"
            number_matches = re.findall(number_pattern, "\n" + reasoning, re.IGNORECASE)
            
            if number_matches:
                steps = [step.strip() for step in number_matches]
                
        return steps
    
    def _extract_conclusion(self, reasoning: str) -> str:
        """Extract conclusion from chain-of-thought output."""
        # Look for conclusion section
        patterns = [
            r"(?:Final conclusion|Conclusion|In conclusion|Therefore)(?:\s+based on[^:]*)?:?\s*((?:.|\n)*?)(?:\n\n|\Z)",
            r"(?:Final answer|Answer|Result):?\s*((?:.|\n)*?)(?:\n\n|\Z)",
            r"(?:In summary|To summarize|Summary):?\s*((?:.|\n)*?)(?:\n\n|\Z)"
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, reasoning, re.IGNORECASE)
            if matches:
                return matches.group(1).strip()
                
        # Fallback: Use last non-empty paragraph
        paragraphs = [p.strip() for p in reasoning.split("\n\n") if p.strip()]
        if paragraphs:
            return paragraphs[-1]
            
        return ""
    
    def _update_metric(self, key: str, value: Union[int, float]) -> None:
        """
        Thread-safe metric update.
        
        Args:
            key: Metric key (dot notation for nested)
            value: Value to add
        """
        with self.metrics_lock:
            # Handle nested keys (e.g., "model_usage.gemini_pro")
            if "." in key:
                parent_key, child_key = key.split(".", 1)
                if parent_key in self.metrics:
                    # Ensure nested dict exists
                    if parent_key not in self.metrics:
                        self.metrics[parent_key] = {}
                    self.metrics[parent_key][child_key] = (
                        self.metrics[parent_key].get(child_key, 0) + value
                    )
            else:
                # Simple key
                self.metrics[key] = self.metrics.get(key, 0) + value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        with self.metrics_lock:
            # Create a copy to avoid race conditions
            metrics_copy = json.loads(json.dumps(self.metrics))
            
            # Add derived metrics
            if metrics_copy["requests"] > 0:
                metrics_copy["success_rate"] = (
                    metrics_copy["successful_requests"] / metrics_copy["requests"]
                )
                
                if metrics_copy["successful_requests"] > 0:
                    metrics_copy["avg_response_time_ms"] = (
                        metrics_copy["total_response_time_ms"] / 
                        metrics_copy["successful_requests"]
                    )
                
                metrics_copy["cache_hit_rate"] = (
                    metrics_copy["cache_hits"] / metrics_copy["requests"]
                )
                
            # Add context manager stats
            metrics_copy["context_manager"] = self.context_manager.get_stats()
            
            # Add prompt manager stats
            metrics_copy["prompt_usage"] = self.prompt_manager.get_usage_stats()
                
            return metrics_copy


# Singleton instance
_advanced_llm_service = None

def get_advanced_llm_service() -> AdvancedLLMService:
    """
    Get or create the AdvancedLLMService singleton.
    
    Returns:
        AdvancedLLMService instance
    """
    global _advanced_llm_service
    if _advanced_llm_service is None:
        _advanced_llm_service = AdvancedLLMService()
    return _advanced_llm_service
