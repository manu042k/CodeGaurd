"""
Result Aggregator
Aggregates, deduplicates, and organizes results from multiple agents
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
import hashlib
import logging

from ..agents.base_agent import AgentResult, Issue, Severity

logger = logging.getLogger(__name__)


class ResultAggregator:
    """
    Aggregates results from multiple agents into unified reports
    
    Features:
    - Deduplication of identical issues
    - Severity-based prioritization
    - Category grouping
    - Score calculation
    - Summary statistics
    """
    
    def __init__(self):
        """Initialize result aggregator"""
        self.severity_weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
            Severity.INFO: 0,
        }
        
    def aggregate(
        self,
        results: List[AgentResult],
        repository_path: str,
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents
        
        Args:
            results: List of agent results
            repository_path: Path to repository
            
        Returns:
            Aggregated report dictionary
        """
        if not results:
            return {
                "status": "completed",
                "repository": repository_path,
                "files_analyzed": 0,
                "total_issues": 0,
                "issues": [],
                "issues_by_severity": {},
                "issues_by_category": {},
                "issues_by_file": {},
                "summary": self._generate_empty_summary(),
                "agent_reports": [],
            }
        
        # Extract all issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        # Deduplicate issues
        unique_issues = self._deduplicate_issues(all_issues)
        
        # Sort by severity
        sorted_issues = self._sort_by_severity(unique_issues)
        
        # Group issues
        by_severity = self._group_by_severity(sorted_issues)
        by_category = self._group_by_category(sorted_issues)
        by_file = self._group_by_file(sorted_issues)
        
        # Calculate statistics
        summary = self._generate_summary(results, sorted_issues)
        
        # Build report
        report = {
            "status": "completed",
            "repository": repository_path,
            "files_analyzed": self._count_unique_files(results),
            "total_issues": len(sorted_issues),
            "issues": [self._issue_to_dict(issue) for issue in sorted_issues],
            "issues_by_severity": {
                severity: [self._issue_to_dict(issue) for issue in issues]
                for severity, issues in by_severity.items()
            },
            "issues_by_category": {
                category: [self._issue_to_dict(issue) for issue in issues]
                for category, issues in by_category.items()
            },
            "issues_by_file": {
                file_path: [self._issue_to_dict(issue) for issue in issues]
                for file_path, issues in by_file.items()
            },
            "summary": summary,
            "agent_reports": [self._agent_result_to_dict(r) for r in results],
        }
        
        return report
        
    def _deduplicate_issues(self, issues: List[Issue]) -> List[Issue]:
        """
        Deduplicate issues based on content hash
        
        Two issues are considered duplicates if they have:
        - Same file path
        - Same line number
        - Same rule ID (or similar message)
        - Same severity
        """
        seen_hashes: Set[str] = set()
        unique_issues = []
        
        for issue in issues:
            issue_hash = self._generate_issue_hash(issue)
            
            if issue_hash not in seen_hashes:
                seen_hashes.add(issue_hash)
                unique_issues.append(issue)
            else:
                logger.debug(f"Duplicate issue filtered: {issue.message[:50]}")
        
        logger.info(
            f"Deduplication: {len(issues)} -> {len(unique_issues)} issues "
            f"({len(issues) - len(unique_issues)} duplicates removed)"
        )
        
        return unique_issues
        
    def _generate_issue_hash(self, issue: Issue) -> str:
        """Generate unique hash for an issue"""
        # Create hash from key attributes
        hash_content = (
            f"{issue.file_path}:"
            f"{issue.line_number}:"
            f"{issue.rule_id or issue.title[:100]}:"
            f"{issue.severity.value}"
        )
        return hashlib.md5(hash_content.encode()).hexdigest()
        
    def _sort_by_severity(self, issues: List[Issue]) -> List[Issue]:
        """Sort issues by severity (critical first)"""
        return sorted(
            issues,
            key=lambda x: (
                -self.severity_weights.get(x.severity, 0),  # Severity (descending)
                x.file_path,  # File path
                x.line_number or 0,  # Line number
            )
        )
        
    def _group_by_severity(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by severity"""
        grouped = defaultdict(list)
        for issue in issues:
            grouped[issue.severity.value].append(issue)
        return dict(grouped)
        
    def _group_by_category(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by category"""
        grouped = defaultdict(list)
        for issue in issues:
            category = issue.category or "general"
            grouped[category].append(issue)
        return dict(grouped)
        
    def _group_by_file(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by file path"""
        grouped = defaultdict(list)
        for issue in issues:
            grouped[issue.file_path].append(issue)
        return dict(grouped)
        
    def _count_unique_files(self, results: List[AgentResult]) -> int:
        """Count unique files analyzed"""
        unique_files = set()
        for result in results:
            unique_files.add(result.file_path)
        return len(unique_files)
        
    def _generate_summary(
        self,
        results: List[AgentResult],
        issues: List[Issue]
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        # Count by severity
        severity_counts = defaultdict(int)
        for issue in issues:
            severity_counts[issue.severity.value] += 1
        
        # Count by category
        category_counts = defaultdict(int)
        for issue in issues:
            category = issue.category or "general"
            category_counts[category] += 1
        
        # Agent statistics
        agent_stats = defaultdict(lambda: {"files": 0, "issues": 0})
        for result in results:
            agent_stats[result.agent_name]["files"] += 1
            agent_stats[result.agent_name]["issues"] += len(result.issues)
        
        # Calculate overall score (0-100, lower is better)
        score = self._calculate_score(issues)
        
        # Get top files with most issues
        file_issue_counts = defaultdict(int)
        for issue in issues:
            file_issue_counts[issue.file_path] += 1
        top_files = sorted(
            file_issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_issues": len(issues),
            "by_severity": dict(severity_counts),
            "by_category": dict(category_counts),
            "by_agent": dict(agent_stats),
            "overall_score": score,
            "grade": self._score_to_grade(score),
            "top_problematic_files": [
                {"file": file, "issues": count}
                for file, count in top_files
            ],
            "recommendations": self._generate_recommendations(issues, severity_counts),
        }
        
    def _generate_empty_summary(self) -> Dict[str, Any]:
        """Generate empty summary for no issues"""
        return {
            "total_issues": 0,
            "by_severity": {},
            "by_category": {},
            "by_agent": {},
            "overall_score": 100,
            "grade": "A+",
            "top_problematic_files": [],
            "recommendations": ["No issues found! Great work! 🎉"],
        }
        
    def _calculate_score(self, issues: List[Issue]) -> int:
        """
        Calculate overall code quality score (0-100)
        100 = perfect, 0 = terrible
        """
        if not issues:
            return 100
        
        # Calculate weighted issue score
        total_weight = sum(
            self.severity_weights.get(issue.severity, 0)
            for issue in issues
        )
        
        # Normalize to 0-100 scale (logarithmic to avoid harsh penalties)
        # Formula: 100 - min(100, log_scale(total_weight))
        import math
        if total_weight == 0:
            return 100
        
        # Use logarithmic scaling to make scores more meaningful
        penalty = min(100, int(10 * math.log10(total_weight + 1)))
        score = max(0, 100 - penalty)
        
        return score
        
    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"
            
    def _generate_recommendations(
        self,
        issues: List[Issue],
        severity_counts: Dict[str, int]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        critical = severity_counts.get("critical", 0)
        high = severity_counts.get("high", 0)
        medium = severity_counts.get("medium", 0)
        
        if critical > 0:
            recommendations.append(
                f"🚨 URGENT: Fix {critical} critical issue(s) immediately - "
                "these pose serious security or stability risks"
            )
        
        if high > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Address {high} high-severity issue(s) soon"
            )
        
        if medium > 0:
            recommendations.append(
                f"📋 MEDIUM PRIORITY: Plan to fix {medium} medium-severity issue(s)"
            )
        
        # Category-specific recommendations
        category_counts = defaultdict(int)
        for issue in issues:
            category = issue.category or "general"
            category_counts[category] += 1
        
        if category_counts.get("security", 0) > 0:
            recommendations.append(
                "🔒 Security: Prioritize security vulnerabilities to protect your application"
            )
        
        if category_counts.get("dependency", 0) > 0:
            recommendations.append(
                "📦 Dependencies: Update outdated or vulnerable dependencies"
            )
        
        if category_counts.get("code_quality", 0) > 5:
            recommendations.append(
                "✨ Code Quality: Consider refactoring to improve maintainability"
            )
        
        if category_counts.get("performance", 0) > 0:
            recommendations.append(
                "⚡ Performance: Optimize slow operations to improve user experience"
            )
        
        if not recommendations:
            recommendations.append("✅ No major issues found! Keep up the good work!")
        
        return recommendations
        
    def _issue_to_dict(self, issue: Issue) -> Dict[str, Any]:
        """Convert Issue object to dictionary"""
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "column": issue.column,
            "severity": issue.severity.value,
            "category": issue.category,
            "rule_id": issue.rule_id,
            "title": issue.title,
            "description": issue.description,
            "code_snippet": issue.code_snippet,
            "suggestion": issue.suggestion,
            "references": issue.references,
            "confidence": issue.confidence,
        }
        
    def _agent_result_to_dict(self, result: AgentResult) -> Dict[str, Any]:
        """Convert AgentResult to dictionary"""
        return {
            "agent_name": result.agent_name,
            "file_path": result.file_path,
            "execution_time": result.execution_time,
            "issues_found": len(result.issues),
            "score": result.score,
            "metrics": result.metrics,
            "error": result.error,
        }
