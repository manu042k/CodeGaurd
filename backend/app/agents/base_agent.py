"""
Base Agent Class
Abstract base class for all code analysis agents.
Supports hybrid analysis: rule-based (fast) + LLM-based (intelligent)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime
import json
import random
import re


class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Issue:
    """Represents a single analysis issue"""
    title: str
    description: str
    severity: Severity
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None
    category: Optional[str] = None  # e.g., "security", "performance", "code_quality"
    confidence: Optional[float] = None  # 0.0 to 1.0
    references: List[str] = field(default_factory=list)  # External references/links
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "rule_id": self.rule_id,
            "category": self.category,
            "confidence": self.confidence,
            "references": self.references,
            "metadata": self.metadata,
        }


@dataclass
class AgentResult:
    """Result from an agent's analysis"""
    agent_name: str
    file_path: str
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None  # 0-10 scale
    execution_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "agent_name": self.agent_name,
            "file_path": self.file_path,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "score": self.score,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }

    def get_issue_count_by_severity(self) -> Dict[str, int]:
        """Get count of issues by severity"""
        counts = {severity.value: 0 for severity in Severity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts


class BaseAgent(ABC):
    """Abstract base class for all analysis agents with hybrid LLM + Logic approach"""

    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        llm_service: Optional[Any] = None  # LLMService instance
    ):
        """
        Initialize the agent
        
        Args:
            config: Agent-specific configuration
            llm_service: LLM service for intelligent analysis (optional)
        """
        self.config = config or {}
        self.llm_service = llm_service
        self.use_llm = llm_service is not None and self.config.get("use_llm", True)
        self.llm_sample_rate = self.config.get("llm_sample_rate", 0.2)  # Analyze 20% with LLM
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for the agent"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the agent's version"""
        pass

    @property
    def description(self) -> str:
        """Return the agent's description"""
        return "Code analysis agent"

    @property
    def supported_languages(self) -> List[str]:
        """Return list of supported programming languages"""
        return ["*"]  # All languages by default

    def can_analyze(self, file_path: str, language: str) -> bool:
        """
        Check if the agent can analyze the given file
        
        Args:
            file_path: Path to the file
            language: Programming language of the file
            
        Returns:
            True if agent can analyze the file
        """
        if "*" in self.supported_languages:
            return True
        return language.lower() in [lang.lower() for lang in self.supported_languages]

    async def analyze(
        self,
        file_path: str,
        file_content: str,
        language: str,
        **kwargs
    ) -> AgentResult:
        """
        Hybrid analysis: Rule-based + LLM-based (if enabled)
        
        Args:
            file_path: Path to the file being analyzed
            file_content: Content of the file
            language: Programming language of the file
            **kwargs: Additional arguments
            
        Returns:
            AgentResult containing issues and metrics
        """
        # Tier 1: Fast rule-based analysis (always run)
        rule_issues = await self._rule_based_analysis(file_path, file_content, language, **kwargs)
        
        # Tier 2: LLM-based deep analysis (conditional)
        if self.use_llm and self._should_use_llm(file_path, file_content, rule_issues):
            self.log_info(f"Using LLM analysis for {file_path}")
            llm_issues = await self._llm_based_analysis(file_path, file_content, language, rule_issues, **kwargs)
            all_issues = self._merge_and_deduplicate_issues(rule_issues, llm_issues)
        else:
            all_issues = rule_issues
        
        return all_issues

    @abstractmethod
    async def _rule_based_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
        **kwargs
    ) -> AgentResult:
        """
        Fast rule-based analysis using patterns and logic
        
        Args:
            file_path: Path to the file being analyzed
            file_content: Content of the file
            language: Programming language of the file
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with rule-based findings
        """
        pass

    async def _llm_based_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
        rule_issues: AgentResult,
        **kwargs
    ) -> AgentResult:
        """
        Deep LLM-based analysis for context-aware findings
        
        Args:
            file_path: Path to the file being analyzed
            file_content: Content of the file
            language: Programming language of the file
            rule_issues: Issues found by rule-based analysis
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with LLM-based findings
        """
        if not self.llm_service:
            return self._create_result(file_path=file_path)
        
        try:
            # Build prompt for this agent type
            prompt = self._build_llm_prompt(file_path, file_content, language, rule_issues)
            
            # Call LLM
            response = await self.llm_service.generate_response(
                prompt=prompt,
                temperature=0.3,  # Lower for consistent analysis
                max_tokens=2000
            )
            
            # Parse LLM response
            issues = self._parse_llm_response(response, file_path)
            
            # Calculate metrics and score
            metrics = {"llm_analysis": True, "llm_issues_found": len(issues)}
            score = self.calculate_score(issues)
            
            return self._create_result(
                file_path=file_path,
                issues=issues,
                metrics=metrics,
                score=score
            )
            
        except Exception as e:
            self.log_error(f"LLM analysis failed for {file_path}: {str(e)}")
            return self._create_result(file_path=file_path, error=str(e))

    def _create_result(
        self,
        file_path: str,
        issues: List[Issue] = None,
        metrics: Dict[str, Any] = None,
        score: Optional[float] = None,
        execution_time: Optional[float] = None,
        error: Optional[str] = None,
    ) -> AgentResult:
        """
        Create an AgentResult object
        
        Args:
            file_path: Path to the analyzed file
            issues: List of issues found
            metrics: Analysis metrics
            score: Overall score (0-10)
            execution_time: Time taken for analysis
            error: Error message if analysis failed
            
        Returns:
            AgentResult object
        """
        return AgentResult(
            agent_name=self.name,
            file_path=file_path,
            issues=issues or [],
            metrics=metrics or {},
            score=score,
            execution_time=execution_time,
            error=error,
        )

    def calculate_score(self, issues: List[Issue], max_score: float = 10.0) -> float:
        """
        Calculate overall score based on issues
        
        Args:
            issues: List of issues
            max_score: Maximum possible score
            
        Returns:
            Score between 0 and max_score
        """
        if not issues:
            return max_score

        # Weight by severity
        severity_weights = {
            Severity.CRITICAL: 2.0,
            Severity.HIGH: 1.5,
            Severity.MEDIUM: 1.0,
            Severity.LOW: 0.5,
            Severity.INFO: 0.1,
        }

        total_penalty = sum(
            severity_weights.get(issue.severity, 0) for issue in issues
        )

        # Calculate score (never go below 0)
        score = max(0, max_score - (total_penalty * 0.5))
        return round(score, 2)

    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(f"[{self.name}] {message}")

    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(f"[{self.name}] {message}")

    def _should_use_llm(
        self, 
        file_path: str, 
        file_content: str, 
        rule_issues: AgentResult
    ) -> bool:
        """
        Decide if LLM analysis is worth the cost/time
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            rule_issues: Issues found by rule-based analysis
            
        Returns:
            True if LLM analysis should be performed
        """
        # Always use LLM if critical issues found (to verify)
        if any(i.severity == Severity.CRITICAL for i in rule_issues.issues):
            return True
        
        # Skip for very small files
        lines = file_content.count('\n') + 1
        if lines < 20:
            return False
        
        # Skip for config/data files
        config_extensions = ['.json', '.yaml', '.yml', '.xml', '.toml', '.ini']
        if any(file_path.endswith(ext) for ext in config_extensions):
            return False
        
        # Use LLM for complex files (high nesting, many functions)
        if self._estimate_complexity(file_content) > 15:
            return True
        
        # Use LLM periodically for sampling (cost optimization)
        return random.random() < self.llm_sample_rate

    def _estimate_complexity(self, content: str) -> int:
        """Estimate code complexity (simple heuristic)"""
        # Count control flow keywords
        keywords = ['if', 'else', 'elif', 'for', 'while', 'try', 'except', 'switch', 'case']
        complexity = sum(content.count(keyword) for keyword in keywords)
        return complexity

    def _build_llm_prompt(
        self,
        file_path: str,
        file_content: str,
        language: str,
        rule_issues: AgentResult
    ) -> str:
        """
        Build prompt for LLM analysis
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            language: Programming language
            rule_issues: Issues found by rule-based analysis
            
        Returns:
            Formatted prompt string
        """
        # Format rule-based issues for context
        rule_findings = ""
        if rule_issues.issues:
            rule_findings = "\n".join([
                f"- [{i.severity.value}] {i.title} (Line {i.line_number}): {i.description}"
                for i in rule_issues.issues[:10]  # Limit to top 10
            ])
        else:
            rule_findings = "No issues found by quick scan."
        
        prompt = f"""You are a {self.name} expert analyzing {language} code.

FILE: {file_path}

CODE:
```{language}
{file_content[:4000]}  # Limit to 4000 chars to save tokens
```

QUICK SCAN RESULTS:
{rule_findings}

YOUR TASK:
{self._get_agent_specific_instructions()}

OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "title": "Issue title",
      "description": "Detailed explanation",
      "severity": "critical|high|medium|low|info",
      "line_number": 42,
      "code_snippet": "problematic code",
      "suggestion": "How to fix",
      "confidence": 0.95,
      "rule_id": "LLM_ISSUE_TYPE"
    }}
  ],
  "false_positives": [0, 2],
  "overall_assessment": "Brief summary",
  "recommendations": ["General improvement 1", "General improvement 2"]
}}

IMPORTANT:
- Only report high-confidence issues (>0.7)
- Provide specific line numbers when possible
- Include actionable suggestions
- Consider the full context, not just individual lines
- Return ONLY valid JSON, no additional text"""

        return prompt

    def _get_agent_specific_instructions(self) -> str:
        """
        Get agent-specific instructions for LLM prompt
        Override in subclasses for specialized analysis
        
        Returns:
            Instructions string
        """
        return f"""Perform a thorough {self.name} analysis.
Look for issues that pattern matching might miss.
Consider context, business logic, and subtle problems."""

    def _parse_llm_response(self, response: str, file_path: str) -> List[Issue]:
        """
        Parse LLM JSON response into Issue objects
        
        Args:
            response: LLM response string
            file_path: Path to the file being analyzed
            
        Returns:
            List of Issue objects
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                json_str = json_match.group(0) if json_match else response
            
            data = json.loads(json_str)
            issues = []
            
            for item in data.get("issues", []):
                # Only include high-confidence issues
                if item.get("confidence", 1.0) >= 0.7:
                    issues.append(Issue(
                        title=item.get("title", "LLM-detected issue"),
                        description=item.get("description", ""),
                        severity=self._parse_severity(item.get("severity", "medium")),
                        file_path=file_path,
                        line_number=item.get("line_number"),
                        code_snippet=item.get("code_snippet"),
                        suggestion=item.get("suggestion"),
                        rule_id=item.get("rule_id", f"LLM_{self.name}"),
                        metadata={
                            "confidence": item.get("confidence", 1.0),
                            "source": "llm"
                        }
                    ))
            
            return issues
            
        except (json.JSONDecodeError, AttributeError) as e:
            self.log_error(f"Failed to parse LLM response: {str(e)}")
            return []

    def _parse_severity(self, severity_str: str) -> Severity:
        """Parse severity string to Severity enum"""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        return severity_map.get(severity_str.lower(), Severity.MEDIUM)

    def _merge_and_deduplicate_issues(
        self, 
        rule_result: AgentResult, 
        llm_result: AgentResult
    ) -> AgentResult:
        """
        Merge rule-based and LLM-based issues, removing duplicates
        
        Args:
            rule_result: Result from rule-based analysis
            llm_result: Result from LLM analysis
            
        Returns:
            Merged AgentResult
        """
        all_issues = list(rule_result.issues)
        
        # Add LLM issues that don't duplicate rule issues
        for llm_issue in llm_result.issues:
            is_duplicate = False
            for rule_issue in rule_result.issues:
                # Check if similar (same line, similar title)
                if (rule_issue.line_number == llm_issue.line_number and
                    self._are_similar_titles(rule_issue.title, llm_issue.title)):
                    is_duplicate = True
                    # Enhance rule issue with LLM insights
                    if llm_issue.suggestion and not rule_issue.suggestion:
                        rule_issue.suggestion = llm_issue.suggestion
                    break
            
            if not is_duplicate:
                all_issues.append(llm_issue)
        
        # Merge metrics
        merged_metrics = {**rule_result.metrics, **llm_result.metrics}
        merged_metrics["total_issues"] = len(all_issues)
        
        # Recalculate score
        score = self.calculate_score(all_issues)
        
        return self._create_result(
            file_path=rule_result.file_path,
            issues=all_issues,
            metrics=merged_metrics,
            score=score,
            execution_time=(rule_result.execution_time or 0) + (llm_result.execution_time or 0)
        )

    def _are_similar_titles(self, title1: str, title2: str) -> bool:
        """Check if two issue titles are similar (simple heuristic)"""
        # Convert to lowercase and remove common words
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return False
        
        similarity = len(intersection) / len(union)
        return similarity > 0.5
