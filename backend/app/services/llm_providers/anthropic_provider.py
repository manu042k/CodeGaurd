"""
Anthropic Claude Provider
"""

from typing import Optional
import anthropic
from anthropic import AsyncAnthropic
from .base import LLMProvider
import logging

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for code analysis"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Model context limits
        self.context_limits = {
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
        }
    
    async def generate_analysis(
        self, 
        prompt: str, 
        context: str,
        max_tokens: int = 4000,
        temperature: float = 0.3
    ) -> str:
        """Generate analysis using Anthropic Claude"""
        try:
            self.logger.info(f"Calling Anthropic API with model: {self.model}")
            
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=prompt,
                messages=[
                    {"role": "user", "content": context}
                ]
            )
            
            result = message.content[0].text
            self.logger.info(
                f"Anthropic API call successful. "
                f"Input tokens: {message.usage.input_tokens}, "
                f"Output tokens: {message.usage.output_tokens}"
            )
            
            return result
            
        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic rate limit exceeded: {str(e)}")
            raise Exception("Rate limit exceeded. Please try again later.")
        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error calling Anthropic: {str(e)}")
            raise
    
    def get_max_context_length(self) -> int:
        """Get maximum context length for this model"""
        return self.context_limits.get(self.model, 200000)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Claude uses similar tokenization to GPT
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
