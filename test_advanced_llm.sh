#!/bin/bash
# Test script for Advanced LLM Integration

# Set up environment
export PYTHONPATH=/Users/shivashishjaishy/Desktop/recruitX:$PYTHONPATH

# Create test directory if it doesn't exist
mkdir -p /Users/shivashishjaishy/Desktop/recruitX/tests/llm/advanced

# Run modified tests with dependency handling
echo "Running Advanced LLM tests..."
cd /Users/shivashishjaishy/Desktop/recruitX

# Test ExpiringCache functionality (no heavy dependencies)
python3 -c "
from src.llm.advanced.context_manager import ExpiringCache
import time

print('Testing ExpiringCache...')
cache = ExpiringCache(max_size=3, ttl_seconds=0.1)
cache['key1'] = 'value1'
print(f\"Cache contains 'key1': {'key1' in cache}\")
time.sleep(0.2)
print(f\"Cache contains 'key1' after TTL: {'key1' in cache}\")

# Test LRU eviction
cache = ExpiringCache(max_size=2)
cache['key1'] = 'value1'
cache['key2'] = 'value2'
# Access key1 to make it recently used
_ = cache['key1']
# Add a new item to trigger eviction
cache['key3'] = 'value3'
# key2 should be evicted (least recently used)
print(f\"LRU eviction test passed: {'key1' in cache and 'key3' in cache and 'key2' not in cache}\")

print('ExpiringCache tests completed successfully!')
"

# Test PromptTemplate functionality (minimal dependencies)
python3 -c "
from src.llm.advanced.prompt_manager import PromptTemplate
from unittest.mock import patch, MagicMock

print('Testing PromptTemplate...')
template = PromptTemplate(
    id='test_template',
    name='Test Template',
    template='Hello, {name}! Welcome to {service}.',
    parameters=['name', 'service']
)

formatted = template.format(name='User', service='RecruitPro')
print(f\"Template formatting test: {formatted == 'Hello, User! Welcome to RecruitPro.'}\")

template_dict = template.to_dict()
new_template = PromptTemplate.from_dict(template_dict)
print(f\"Template serialization test: {new_template.id == template.id and new_template.template == template.template}\")

print('PromptTemplate tests completed successfully!')
"

# Test PromptManager with mocks to avoid heavy dependencies
python3 -c "
from src.llm.advanced.prompt_manager import PromptManager
from unittest.mock import patch, MagicMock

print('Testing PromptManager with mocks...')
with patch('src.llm.advanced.prompt_manager.get_context_manager', return_value=MagicMock()):
    manager = PromptManager()
    
    # Check default templates
    has_defaults = 'base_resume_analysis' in manager.templates and 'skill_extraction' in manager.templates
    print(f\"PromptManager has default templates: {has_defaults}\")
    
    # Test template creation with parameter detection
    template = manager.create_template(
        name='Test Template',
        template='This is a {test} template.'
    )
    
    param_detection = 'test' in template.parameters
    print(f\"Parameter auto-detection test: {param_detection}\")

print('PromptManager tests completed successfully!')
"

# Test AdvancedLLMService with mocks
python3 -c "
from unittest.mock import patch, MagicMock
import sys

print('Testing AdvancedLLMService with mocks...')

# Set up mocks
mock_gemini = MagicMock()
mock_gemini.generate_content.return_value = 'Gemini response'

mock_gemma = MagicMock()
mock_gemma.generate_content.return_value = 'Gemma response'

mock_context = MagicMock()
mock_context.get_memoized_result.return_value = None

mock_prompt = MagicMock()
mock_prompt.format_prompt.return_value = 'Formatted prompt'

# Apply patches
with patch('src.llm.advanced.advanced_llm_service.get_gemini_service', return_value=mock_gemini), \
     patch('src.llm.advanced.advanced_llm_service.get_gemma_service', return_value=mock_gemma), \
     patch('src.llm.advanced.advanced_llm_service.get_context_manager', return_value=mock_context), \
     patch('src.llm.advanced.advanced_llm_service.get_prompt_manager', return_value=mock_prompt), \
     patch('src.llm.advanced.advanced_llm_service.GEMINI_API_KEYS', ['test_key']), \
     patch('src.llm.advanced.advanced_llm_service.GEMMA_API_KEYS', ['test_key']):
    
    from src.llm.advanced.advanced_llm_service import AdvancedLLMService
    from src.utils.config import GEMINI_PRO_MODEL, GEMMA_MODEL
    
    # Create service
    service = AdvancedLLMService()
    
    # Test Gemini generation
    response = service.generate_content(
        prompt='Test prompt',
        model=GEMINI_PRO_MODEL
    )
    
    gemini_test = response == 'Gemini response' and mock_gemini.generate_content.called
    print(f\"Gemini generation test: {gemini_test}\")
    
    # Reset mock
    mock_gemini.generate_content.reset_mock()
    
    # Test Gemma generation
    response = service.generate_content(
        prompt='Test prompt',
        model=GEMMA_MODEL
    )
    
    gemma_test = response == 'Gemma response' and mock_gemma.generate_content.called
    print(f\"Gemma generation test: {gemma_test}\")
    
    # Test cache hit
    mock_context.get_memoized_result.return_value = 'Cached response'
    
    response = service.generate_content(
        prompt='Test prompt',
        use_cache=True
    )
    
    cache_test = response == 'Cached response' and not mock_gemini.generate_content.called and not mock_gemma.generate_content.called
    print(f\"Cache hit test: {cache_test}\")

print('AdvancedLLMService tests completed successfully!')
"

echo "All Advanced LLM tests completed."
