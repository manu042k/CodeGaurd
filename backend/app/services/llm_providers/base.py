"""
Base LLM Provider Abstract Class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def generate_analysis(
        self, 
        prompt: str, 
        context: str,
        max_tokens: int = 4000,
        temperature: float = 0.3
    ) -> str:
        """
        Generate analysis using LLM
        
        Args:
            prompt: System prompt defining the agent's role
            context: Code context to analyze
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
        
        Returns:
            Analysis response as string (preferably JSON)
        """
        pass
    
    @abstractmethod
    def get_max_context_length(self) -> int:
        """Get maximum context length for this provider"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for given text"""
        pass
    
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        if not self.api_key:
            self.logger.error("API key not provided")
            return False
        if not self.model:
            self.logger.error("Model not specified")
            return False
        return True
