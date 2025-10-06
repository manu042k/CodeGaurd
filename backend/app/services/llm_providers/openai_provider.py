"""
OpenAI GPT Provider
"""

from typing import Optional
import openai
from openai import AsyncOpenAI
from .base import LLMProvider
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider for code analysis"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Model context limits
        self.context_limits = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385
        }
    
    async def generate_analysis(
        self, 
        prompt: str, 
        context: str,
        max_tokens: int = 4000,
        temperature: float = 0.3
    ) -> str:
        """Generate analysis using OpenAI"""
        try:
            self.logger.info(f"Calling OpenAI API with model: {self.model}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"} if "turbo" in self.model else None
            )
            
            result = response.choices[0].message.content
            self.logger.info(f"OpenAI API call successful. Tokens used: {response.usage.total_tokens}")
            
            return result
            
        except openai.RateLimitError as e:
            self.logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise Exception("Rate limit exceeded. Please try again later.")
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error calling OpenAI: {str(e)}")
            raise
    
    def get_max_context_length(self) -> int:
        """Get maximum context length for this model"""
        return self.context_limits.get(self.model, 8192)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
