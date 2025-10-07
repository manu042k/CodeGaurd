"""
Multi-Agent Code Analysis System
Provides specialized agents for comprehensive code analysis.
"""

from .base_agent import BaseAgent, AgentResult, Issue, Severity
from .security_agent import SecurityAgent
from .dependency_agent import DependencyAgent
from .code_quality_agent import CodeQualityAgent
from .performance_agent import PerformanceAgent
from .best_practices_agent import BestPracticesAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "Issue",
    "Severity",
    "SecurityAgent",
    "DependencyAgent",
    "CodeQualityAgent",
    "PerformanceAgent",
    "BestPracticesAgent",
]
