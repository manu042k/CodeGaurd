"""
Google Gemini Provider
"""

from typing import Optional
import google.generativeai as genai
from .base import LLMProvider
import logging

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini provider for code analysis"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        super().__init__(api_key, model)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use model as-is (API now has consistent naming)
        self.model_instance = genai.GenerativeModel(model)
        
        # Model context limits
        self.context_limits = {
            "gemini-2.5-pro": 1048576,  # 1M tokens
            "gemini-2.5-flash": 1048576,  # 1M tokens
            "gemini-2.0-flash": 1048576,  # 1M tokens
            "gemini-pro-latest": 1048576,  # 1M tokens
            "gemini-flash-latest": 1048576,  # 1M tokens
            "gemini-1.5-pro": 2000000,  # 2M tokens (legacy)
            "gemini-1.5-flash": 1000000,  # 1M tokens (legacy)
            "gemini-pro": 32768,
        }
        
        # Safety settings - relaxed for code analysis
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    
    async def generate_analysis(
        self, 
        prompt: str, 
        context: str,
        max_tokens: int = 8192,
        temperature: float = 0.3
    ) -> str:
        """Generate analysis using Google Gemini"""
        try:
            self.logger.info(f"Calling Gemini API with model: {self.model}")
            
            # Combine system prompt and user context
            full_prompt = f"{prompt}\n\n{context}"
            
            # Configure generation
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
            
            # Generate content
            response = await self.model_instance.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            # Check if response was blocked
            if not response.text:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    error_msg = f"Content blocked: {response.prompt_feedback.block_reason}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                else:
                    error_msg = "Empty response from Gemini"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
            
            self.logger.info("Gemini API call successful")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {str(e)}")
            raise
    
    def get_max_context_length(self) -> int:
        """Get maximum context length for this model"""
        return self.context_limits.get(self.model, 32768)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        try:
            # Try to use Gemini's token counting
            response = self.model_instance.count_tokens(text)
            return response.total_tokens
        except Exception:
            # Fallback: rough estimate
            return len(text) // 4
