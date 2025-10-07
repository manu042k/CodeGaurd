"""
Simple LLM Wrapper for Agent Analysis
Simplified interface for agents to use LLM services.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimpleLLMService:
    """Simplified LLM service interface for agents"""
    
    def __init__(self, llm_service = None):
        """
        Initialize with existing LLM service
        
        Args:
            llm_service: Existing LLMService instance (from app.services.llm_service)
        """
        self.llm_service = llm_service
        self.enabled = llm_service is not None

    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text response
        """
        if not self.enabled or not self.llm_service:
            raise ValueError("LLM service not initialized")
        
        try:
            # Use the existing LLM service's generate method
            response = await self.llm_service.provider.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.get("content", "")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise

    async def analyze_code_snippet(
        self,
        code: str,
        language: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a code snippet (convenience method)
        
        Args:
            code: Code to analyze
            language: Programming language
            analysis_type: Type of analysis (security, quality, etc.)
            context: Additional context
            
        Returns:
            Analysis results as dictionary
        """
        import json
        
        prompt = f"""Analyze this {language} code for {analysis_type}:

```{language}
{code[:3000]}
```

Return analysis as JSON."""
        
        response = await self.generate_response(prompt, temperature=0.2)
        
        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Return as plain text if not JSON
            return {"analysis": response}

    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.enabled

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> "SimpleLLMService":
        """
        Create LLM service from configuration
        
        Args:
            config: Configuration dictionary with provider settings
            
        Returns:
            SimpleLLMService instance
        """
        # This would load from settings and create proper LLM service
        # For now, return disabled service
        return cls(llm_service=None)
