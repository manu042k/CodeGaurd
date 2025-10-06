"""
LLM Service - Main orchestrator for all LLM providers
"""

from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.llm_providers import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider
)
import logging
import json
import re

logger = logging.getLogger(__name__)


class LLMService:
    """Service to manage LLM interactions across providers"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM service with specified provider
        
        Args:
            provider: Provider name ('openai', 'anthropic', 'gemini')
                     If None, uses settings.LLM_PROVIDER
        """
        self.provider_name = provider or settings.LLM_PROVIDER
        self.provider = self._initialize_provider(self.provider_name)
        
        if not self.provider.validate_config():
            raise ValueError(f"Invalid configuration for provider: {self.provider_name}")
    
    def _initialize_provider(self, provider: str) -> LLMProvider:
        """Initialize the specified LLM provider"""
        
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )
        
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            return AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL
            )
        
        elif provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def analyze_code(
        self, 
        agent_type: str,
        code_files: List[Dict[str, str]],
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze code using appropriate agent prompt
        
        Args:
            agent_type: Type of analysis ('CodeQuality', 'Security', etc.)
            code_files: List of files with path, content, language
            project_context: Project metadata (name, language, description)
        
        Returns:
            Analysis result with summary, score, and issues
        """
        try:
            # Get agent-specific prompt
            prompt = self._get_agent_prompt(agent_type)
            
            # Prepare context
            context = self._prepare_context(code_files, project_context)
            
            # Check token limits
            estimated_tokens = self.provider.estimate_tokens(prompt + context)
            max_context = self.provider.get_max_context_length()
            
            if estimated_tokens > max_context * 0.8:  # Use 80% of limit
                logger.warning(
                    f"Context too large ({estimated_tokens} tokens). "
                    f"Truncating files..."
                )
                code_files = self._truncate_files(code_files, max_context)
                context = self._prepare_context(code_files, project_context)
            
            # Generate analysis
            logger.info(f"Running {agent_type} analysis with {len(code_files)} files")
            response = await self.provider.generate_analysis(
                prompt=prompt,
                context=context,
                max_tokens=8192 if self.provider_name == "gemini" else 4000
            )
            
            # Parse response
            result = self._parse_analysis_response(response, agent_type)
            
            logger.info(
                f"{agent_type} analysis complete. "
                f"Score: {result.get('score', 0):.2f}, "
                f"Issues: {len(result.get('issues', []))}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def _get_agent_prompt(self, agent_type: str) -> str:
        """Get system prompt for specific agent type"""
        
        base_instruction = """
You are an expert code analyst. Analyze the provided code and return your findings as a JSON object with this EXACT structure:

{
  "summary": "Brief 2-3 sentence overview of your analysis",
  "score": 0.85,
  "issues": [
    {
      "type": "code_smell|security|architecture|documentation",
      "severity": "critical|high|medium|low",
      "title": "Short title of the issue",
      "description": "Detailed explanation of the issue",
      "file_path": "relative/path/to/file.py",
      "line_number": 42,
      "rule": "rule_identifier",
      "suggestion": "How to fix this issue"
    }
  ],
  "metrics": {
    "key": "value"
  }
}

IMPORTANT: Return ONLY valid JSON. No markdown, no explanations outside the JSON.
"""
        
        agent_prompts = {
            "CodeQuality": base_instruction + """
Analyze code quality focusing on:
- Code smells and anti-patterns
- Naming conventions
- Code complexity and readability
- Maintainability issues
- Performance concerns
- Code duplication
- Best practices violations

Score from 0.0 (poor) to 1.0 (excellent).
""",
            
            "Security": base_instruction + """
Analyze security vulnerabilities focusing on:
- SQL injection risks
- XSS vulnerabilities
- Authentication/authorization flaws
- Exposed secrets or credentials
- Insecure dependencies
- OWASP Top 10 vulnerabilities
- Insecure cryptographic practices
- Input validation issues
- API security concerns

Score from 0.0 (critical vulnerabilities) to 1.0 (secure).
Severity levels: critical (immediate fix needed), high (fix soon), medium (should fix), low (minor concern).
""",
            
            "Architecture": base_instruction + """
Analyze software architecture focusing on:
- Design patterns usage and appropriateness
- Separation of concerns
- Modularity and coupling
- Scalability considerations
- Code organization
- Dependency management
- Technical debt
- Layer violations
- Component cohesion

Score from 0.0 (poor architecture) to 1.0 (excellent architecture).
""",
            
            "Documentation": base_instruction + """
Analyze code documentation focusing on:
- Missing or incomplete docstrings/comments
- API documentation quality
- Function/class documentation
- Inline comment quality
- Type hints and annotations
- README completeness
- Code examples availability
- Documentation consistency

Score from 0.0 (no documentation) to 1.0 (excellent documentation).
"""
        }
        
        return agent_prompts.get(agent_type, base_instruction)
    
    def _prepare_context(
        self, 
        code_files: List[Dict[str, str]],
        project_context: Dict[str, Any]
    ) -> str:
        """Prepare code context for LLM"""
        
        context_parts = [
            "=== PROJECT INFORMATION ===",
            f"Project: {project_context.get('name', 'Unknown')}",
            f"Language: {project_context.get('language', 'Unknown')}",
            f"Description: {project_context.get('description', 'N/A')}",
            f"Total Files: {len(code_files)}",
            "",
            "=== CODE FILES ===",
            ""
        ]
        
        for idx, file_info in enumerate(code_files, 1):
            context_parts.append(f"--- File {idx}/{len(code_files)}: {file_info['path']} ---")
            context_parts.append(f"Language: {file_info.get('language', 'unknown')}")
            context_parts.append(f"Lines: {file_info.get('lines', 0)}")
            context_parts.append("")
            context_parts.append("```" + file_info.get('language', ''))
            context_parts.append(file_info['content'])
            context_parts.append("```")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _truncate_files(
        self, 
        code_files: List[Dict[str, str]], 
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """Truncate files to fit within token limit"""
        
        # Take smaller files first, prioritize important files
        sorted_files = sorted(code_files, key=lambda f: f.get('size', 0))
        
        truncated = []
        current_tokens = 0
        target_tokens = max_tokens * 0.6  # Use 60% for content
        
        for file_info in sorted_files:
            file_tokens = self.provider.estimate_tokens(file_info['content'])
            
            if current_tokens + file_tokens < target_tokens:
                truncated.append(file_info)
                current_tokens += file_tokens
            else:
                # Try to include partial content
                remaining_tokens = target_tokens - current_tokens
                if remaining_tokens > 500:  # Only if meaningful content can fit
                    chars_to_include = int(remaining_tokens * 4)  # rough estimate
                    truncated_content = file_info['content'][:chars_to_include]
                    truncated.append({
                        **file_info,
                        'content': truncated_content + "\n\n... (truncated)"
                    })
                break
        
        logger.info(f"Truncated from {len(code_files)} to {len(truncated)} files")
        return truncated
    
    def _parse_analysis_response(
        self, 
        response: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        
        try:
            # Try to extract JSON from response
            # Sometimes LLMs wrap JSON in markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON object
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response
            
            # Parse JSON
            result = json.loads(json_str)
            
            # Validate and ensure required fields
            if "summary" not in result:
                result["summary"] = response[:500] if len(response) > 500 else response
            
            if "score" not in result:
                result["score"] = 0.75  # Default neutral score
            
            if "issues" not in result:
                result["issues"] = []
            
            if "metrics" not in result:
                result["metrics"] = {}
            
            # Ensure score is between 0 and 1
            result["score"] = max(0.0, min(1.0, float(result["score"])))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response[:500]}...")
            
            # Fallback to basic structure
            return {
                "summary": response[:500] if len(response) > 500 else response,
                "full_analysis": response,
                "score": 0.75,
                "issues": [],
                "metrics": {},
                "parse_error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {str(e)}")
            return {
                "summary": "Error parsing analysis response",
                "score": 0.0,
                "issues": [],
                "metrics": {},
                "error": str(e)
            }
