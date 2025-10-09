"""
LLM Provider for Ollama integration with Qwen2.5:8b model
"""
import json
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class OllamaLLMProvider:
    """LLM Provider for Ollama with Qwen3:8b model"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip('/')
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:8b")
        self.timeout = 300  # 5 minutes timeout for analysis
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make async HTTP request to Ollama API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Request error to Ollama: {e}")
                raise Exception(f"Failed to connect to Ollama: {e}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from Ollama: {e}")
                raise Exception(f"Ollama API error: {e}")
    
    async def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate completion using Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Lower temperature for more consistent analysis
                "top_p": 0.9,
                "num_predict": 4096
            }
        }
        
        try:
            response = await self._make_request("/api/chat", data)
            return response.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def analyze_code(self, code_content: str, analysis_type: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze code with specific analysis type"""
        system_prompt = self._get_system_prompt(analysis_type)
        
        # Prepare context information
        context_info = ""
        if context:
            context_info = f"Context: {json.dumps(context, indent=2)}\n\n"
        
        prompt = f"""{context_info}Please analyze the following code:

```
{code_content}
```

Provide your analysis in valid JSON format only, no additional text or explanations outside the JSON."""

        try:
            response = await self.generate_completion(prompt, system_prompt)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error in code analysis: {e}")
            return {"error": str(e), "analysis_type": analysis_type}
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt based on analysis type"""
        prompts = {
            "quality": """You are a code quality expert. Analyze code for:
- Readability and maintainability
- Naming consistency and clarity
- Function/method complexity
- Code duplication
- Code smells (long functions, deep nesting, etc.)
- Refactoring opportunities

Return JSON with: {"category": "Quality", "score": 0-100, "issues": [{"file": "filename", "line": number, "desc": "description", "severity": "low|medium|high"}], "suggestions": ["suggestion1", "suggestion2"]}""",
            
            "security": """You are a security expert. Analyze code for:
- Hardcoded secrets, tokens, passwords
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure deserialization
- Unsafe file operations
- Authentication/authorization issues
- Configuration security issues

Return JSON with: {"category": "Security", "score": 0-100, "issues": [{"file": "filename", "line": number, "desc": "description", "severity": "low|medium|high|critical", "cwe": "CWE-XXX"}], "recommendations": ["rec1", "rec2"]}""",
            
            "architecture": """You are a software architecture expert. Analyze code for:
- Module structure and organization
- Separation of concerns
- Design patterns usage
- Coupling and cohesion
- Circular dependencies
- SOLID principles adherence
- Code organization best practices

Return JSON with: {"category": "Architecture", "score": 0-100, "summary": "brief summary", "issues": [{"desc": "description", "severity": "low|medium|high"}], "suggestions": ["suggestion1", "suggestion2"]}""",
            
            "documentation": """You are a documentation expert. Analyze code for:
- Docstring coverage and quality
- Inline comment clarity
- README completeness
- Code self-documentation
- API documentation
- Missing explanations for complex logic

Return JSON with: {"category": "Documentation", "score": 0-100, "missing_docs": ["file1", "file2"], "issues": [{"file": "filename", "desc": "description"}], "suggestions": ["suggestion1", "suggestion2"]}""",
            
            "testing": """You are a testing expert. Analyze code for:
- Test coverage assessment
- Test structure and organization
- Test naming conventions
- Edge case coverage
- Mock usage
- Integration vs unit tests
- Test maintainability

Return JSON with: {"category": "Testing", "score": 0-100, "summary": "brief summary", "issues": [{"desc": "description", "severity": "low|medium|high"}], "suggestions": ["suggestion1", "suggestion2"]}""",
            
            "dependencies": """You are a dependency management expert. Analyze for:
- Outdated packages
- Security vulnerabilities in dependencies
- License compatibility issues
- Unused dependencies
- Dependency bloat
- Version pinning best practices

Return JSON with: {"category": "Dependencies", "score": 0-100, "issues": [{"package": "package_name", "version": "version", "desc": "description", "severity": "low|medium|high|critical"}], "suggestions": ["suggestion1", "suggestion2"]}"""
        }
        
        return prompts.get(analysis_type, "You are a code analysis expert. Analyze the provided code and return your findings in JSON format.")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling potential formatting issues"""
        try:
            # Clean up the response
            response = response.strip()
            
            # Remove <think> tags and content if present
            if "<think>" in response and "</think>" in response:
                think_start = response.find("<think>")
                think_end = response.find("</think>") + 8
                response = response[:think_start] + response[think_end:]
                response = response.strip()
            
            # Look for JSON block markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.rfind("```")
                if end != -1 and end > start:
                    response = response[start:end].strip()
            
            # Find JSON-like content between braces
            if not response.startswith('{'):
                # Look for first opening brace
                brace_start = response.find('{')
                if brace_start != -1:
                    # Find matching closing brace
                    brace_count = 0
                    brace_end = -1
                    for i in range(brace_start, len(response)):
                        if response[i] == '{':
                            brace_count += 1
                        elif response[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                brace_end = i + 1
                                break
                    
                    if brace_end != -1:
                        response = response[brace_start:brace_end]
            
            # Try to parse JSON
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response[:500]}...")
            
            # Return a fallback structure
            return {
                "error": "Failed to parse LLM response",
                "raw_response": response[:1000],
                "parse_error": str(e)
            }
    
    async def check_health(self) -> bool:
        """Check if Ollama service is healthy and model is available"""
        try:
            # Check if Ollama is running
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                # Check if our model is available
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found. Available models: {model_names}")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

# Global LLM provider instance
llm_provider = OllamaLLMProvider()
