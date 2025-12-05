"""Service for interacting with OpenAI LLM."""

from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()


class LLMService:
    """Service for interacting with OpenAI LLM."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=120.0
        )
        self.model = settings.openai_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response from OpenAI.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            stream: Whether to stream (not used in this method)
            
        Returns:
            Generated response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from OpenAI.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Yields:
            Response tokens as they are generated
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Chat with conversation history.
        
        Args:
            messages: List of messages [{"role": "user/assistant", "content": "..."}]
            system_prompt: Optional system prompt
            
        Returns:
            Generated response text
        """
        all_messages = []
        
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        
        all_messages.extend(messages)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def chat_with_functions(
        self,
        messages: list[dict],
        functions: list[dict],
        function_call: str = "auto"
    ) -> dict:
        """
        Chat with function calling support.
        
        Args:
            messages: Conversation messages
            functions: Available functions
            function_call: "auto", "none", or {"name": "function_name"}
            
        Returns:
            Dict with 'content' and optional 'function_call'
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[{"type": "function", "function": f} for f in functions],
            tool_choice=function_call,
            temperature=0.3,
            max_tokens=2000
        )
        
        message = response.choices[0].message
        
        result = {
            "content": message.content,
            "function_call": None,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        # Extract function call if present
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            result["function_call"] = {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        
        return result
    
    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat with conversation history.
        
        Args:
            messages: List of messages
            system_prompt: Optional system prompt
            
        Yields:
            Response tokens as they are generated
        """
        all_messages = []
        
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        
        all_messages.extend(messages)
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=0.7,
            max_tokens=4000,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            # Make a minimal test request
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"OpenAI health check failed: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "provider": "openai",
            "model": self.model,
            "base_url": settings.openai_base_url
        }


# Singleton instance
llm_service = LLMService()


