from typing import Dict, List, Optional, Union
import json
import hashlib

from openai import (
    APIError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.config import LLMSettings, config
from app.logger import logger  # Assuming a logger is set up in your app
from app.schema import Message, TOOL_CHOICE_TYPE, ROLE_VALUES, TOOL_CHOICE_VALUES, ToolChoice
from app.db.api import DatabaseAPI


class LLM:
    _instances: Dict[str, "LLM"] = {}

    def __new__(
        cls, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name, llm_config)
            cls._instances[config_name] = instance
        return cls._instances[config_name]

    def __init__(
        self, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if not hasattr(self, "client"):  # Only initialize if not already initialized
            llm_config = llm_config or config.llm
            llm_config = llm_config.get(config_name, llm_config["default"])
            self.model = llm_config.model
            self.max_tokens = llm_config.max_tokens
            self.temperature = llm_config.temperature
            self.api_type = llm_config.api_type
            self.api_key = llm_config.api_key
            self.api_version = llm_config.api_version
            self.base_url = llm_config.base_url
            
            # Initialize database API for caching
            self.db_api = DatabaseAPI()
            
            # Set up caching parameters
            self.use_cache = llm_config.get("use_cache", True)
            self.cache_ttl = llm_config.get("cache_ttl", 3600 * 24 * 7)  # 1 week default
            
            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def format_messages(self, messages: List[Union[dict, Message]]) -> List[Dict]:
        """
        Format messages to the standard OpenAI API format.

        Args:
            messages: List of messages (dict or Message objects)

        Returns:
            List[Dict]: Formatted messages ready for OpenAI API
        """
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                # Validate and format dict message
                if not message or "role" not in message or "content" not in message:
                    raise ValueError(f"Invalid message format: {message}")
                if message["role"] not in ROLE_VALUES:
                    raise ValueError(f"Invalid role: {message['role']}")
                formatted_message = {
                    "role": message["role"],
                    "content": message["content"],
                }
                formatted_messages.append(formatted_message)
            elif isinstance(message, Message):
                # Convert Message object to dict
                formatted_message = {
                    "role": message.role,
                    "content": message.content,
                }
                formatted_messages.append(formatted_message)
            else:
                raise ValueError(f"Message must be dict or Message object: {message}")
        return formatted_messages

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to the LLM and get the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response
            temperature (float): Sampling temperature for the response

        Returns:
            str: The generated response

        Raises:
            ValueError: If messages are invalid or response is empty
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        try:
            # Format system and user messages
            if system_msgs:
                system_msgs = self.format_messages(system_msgs)
                messages = system_msgs + self.format_messages(messages)
            else:
                messages = self.format_messages(messages)
                
            # Check cache if enabled and not streaming
            if self.use_cache and not stream:
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                # Try to get from cache
                cached_response = await self._get_from_cache(request_data)
                if cached_response:
                    logger.info("Retrieved response from cache")
                    return cached_response

            if not stream:
                # Non-streaming request
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=temperature or self.temperature,
                    stream=False,
                )
                
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("Empty or invalid response from LLM")
                
                response_text = response.choices[0].message.content
                
                # Cache response if caching is enabled
                if self.use_cache:
                    request_data = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature or self.temperature,
                        "max_tokens": self.max_tokens
                    }
                    await self._cache_response(request_data, response_text)
                
                return response_text

            # Streaming request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                stream=True,
            )

            collected_messages = []
            async for chunk in response:
                chunk_message = chunk.choices[0].delta.content or ""
                collected_messages.append(chunk_message)
                print(chunk_message, end="", flush=True)

            print()  # Newline after streaming
            full_response = "".join(collected_messages).strip()
            if not full_response:
                raise ValueError("Empty response from streaming LLM")
                
            # Cache full streamed response
            if self.use_cache:
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                }
                await self._cache_response(request_data, full_response)
                
            return full_response

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise
        except OpenAIError as oe:
            logger.error(f"OpenAI API error: {oe}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
            
    async def _get_from_cache(self, request_data: Dict) -> Optional[str]:
        """
        Get response from cache
        
        Args:
            request_data: Request data dict
            
        Returns:
            Cached response or None if not found
        """
        try:
            # Determine API type for cache key prefix
            api_name = "azure" if self.api_type == "azure" else "openai"
            
            # Get from cache
            return self.db_api.get_cached_api_response(api_name, request_data)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            return None
            
    async def _cache_response(self, request_data: Dict, response: str) -> None:
        """
        Cache API response
        
        Args:
            request_data: Request data dict
            response: Response to cache
        """
        try:
            # Determine API type for cache key prefix
            api_name = "azure" if self.api_type == "azure" else "openai"
            
            # Store in cache
            self.db_api.cache_api_response(
                api_name=api_name,
                request_data=request_data,
                response_data=response,
                ttl_seconds=self.cache_ttl
            )
        except Exception as e:
            logger.warning(f"Caching failed: {e}")

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask_with_tools(
        self,
        messages: List[Union[dict, Message]],
        tools: List[Dict],
        tool_choice: Optional[TOOL_CHOICE_TYPE] = None,
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        temperature: Optional[float] = None,
    ) -> Dict:
        """
        Send a prompt to the LLM with tools.

        Args:
            messages: List of conversation messages
            tools: List of tools
            tool_choice: Tool choice option
            system_msgs: Optional system messages to prepend
            temperature: Sampling temperature

        Returns:
            Dict: The complete API response

        Raises:
            ValueError: If messages are invalid
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        try:
            # Format system and user messages
            if system_msgs:
                system_msgs = self.format_messages(system_msgs)
                messages = system_msgs + self.format_messages(messages)
            else:
                messages = self.format_messages(messages)

            # Validate tool_choice
            if tool_choice is not None and not isinstance(
                tool_choice, (str, dict, ToolChoice)
            ):
                raise ValueError(f"Invalid tool_choice: {tool_choice}")

            # Convert ToolChoice enum to string
            if isinstance(tool_choice, ToolChoice):
                tool_choice = tool_choice.value

            # Check cache if enabled
            if self.use_cache:
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": tool_choice,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                # Try to get from cache
                cached_response = await self._get_from_cache(request_data)
                if cached_response:
                    logger.info("Retrieved tool response from cache")
                    return json.loads(cached_response)

            # Make API request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
            )
            
            # Cache response if caching is enabled
            if self.use_cache:
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": tool_choice,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                }
                await self._cache_response(request_data, json.dumps(response.model_dump()))
                
            return response.model_dump()

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise
        except OpenAIError as oe:
            logger.error(f"OpenAI API error: {oe}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
