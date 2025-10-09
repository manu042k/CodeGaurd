"""
Code Quality Agent - Analyzes code readability, maintainability, naming consistency, and general style quality
"""
import os
import ast
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_agent import BaseAgent

class CodeQualityAgent(BaseAgent):
    """Agent for analyzing code quality, complexity, and maintainability"""
    
    def __init__(self, llm_provider):
        super().__init__("Code Quality Agent", "Quality", llm_provider)
        self.max_function_length = 50
        self.max_complexity = 10
        self.max_nesting_depth = 4
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze repository for code quality issues"""
        self.logger.info(f"Starting code quality analysis for {repo_path}")
        
        # Find relevant code files
        code_files = self.find_code_files(repo_path)
        
        if not code_files:
            return self.create_result_structure(
                score=100,
                summary="No code files found to analyze"
            )
        
        # Perform static analysis
        static_issues = await self._analyze_static_quality(code_files, repo_path)
        
        # Sample files for LLM analysis
        sample_files = self._select_sample_files(code_files, max_files=5)
        llm_issues = await self._analyze_with_llm(sample_files, repo_path)
        
        # Combine results
        all_issues = static_issues + llm_issues
        score = self._calculate_quality_score(all_issues, len(code_files))
        
        suggestions = self._generate_suggestions(all_issues)
        summary = self._generate_summary(score, all_issues, len(code_files))
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def find_code_files(self, repo_path: str) -> List[str]:
        """Find code files for analysis"""
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go']
        return self.find_files_by_extension(repo_path, extensions)
    
    async def _analyze_static_quality(self, code_files: List[str], repo_path: str) -> List[Dict]:
        """Perform static analysis for code quality issues"""
        issues = []
        
        for file_path in code_files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Analyze based on file type
                if file_path.endswith('.py'):
                    issues.extend(self._analyze_python_file(content, relative_path))
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    issues.extend(self._analyze_javascript_file(content, relative_path))
                
                # General quality checks
                issues.extend(self._analyze_general_quality(content, relative_path))
                
            except Exception as e:
                self.logger.error(f"Error analyzing file {file_path}: {e}")
                issues.append({
                    "file": os.path.relpath(file_path, repo_path),
                    "desc": f"Failed to analyze file: {str(e)}",
                    "severity": "low"
                })
        
        return issues
    
    def _analyze_python_file(self, content: str, file_path: str) -> List[Dict]:
        """Analyze Python file for quality issues"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check function length
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > self.max_function_length:
                        issues.append({
                            "file": file_path,
                            "line": node.lineno,
                            "desc": f"Function '{node.name}' is too long ({func_lines} lines)",
                            "severity": "medium"
                        })
                    
                    # Check for missing docstrings
                    if not ast.get_docstring(node):
                        issues.append({
                            "file": file_path,
                            "line": node.lineno,
                            "desc": f"Function '{node.name}' missing docstring",
                            "severity": "low"
                        })
                
                elif isinstance(node, ast.ClassDef):
                    # Check for missing class docstrings
                    if not ast.get_docstring(node):
                        issues.append({
                            "file": file_path,
                            "line": node.lineno,
                            "desc": f"Class '{node.name}' missing docstring",
                            "severity": "low"
                        })
        
        except SyntaxError as e:
            issues.append({
                "file": file_path,
                "line": e.lineno or 0,
                "desc": f"Syntax error: {e.msg}",
                "severity": "high"
            })
        except Exception as e:
            self.logger.error(f"Error parsing Python file {file_path}: {e}")
        
        return issues
    
    def _analyze_javascript_file(self, content: str, file_path: str) -> List[Dict]:
        """Analyze JavaScript/TypeScript file for quality issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for long functions (simple heuristic)
        in_function = False
        function_start = 0
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            # Simple function detection
            if re.search(r'function\s+\w+|const\s+\w+\s*=\s*\(|\w+\s*:\s*\(', line):
                in_function = True
                function_start = i
                brace_count = 0
            
            if in_function:
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and i > function_start:
                    func_length = i - function_start
                    if func_length > self.max_function_length:
                        issues.append({
                            "file": file_path,
                            "line": function_start,
                            "desc": f"Function is too long ({func_length} lines)",
                            "severity": "medium"
                        })
                    in_function = False
            
            # Check for console.log statements
            if 'console.log' in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "desc": "Console.log statement found - should be removed in production",
                    "severity": "low"
                })
        
        return issues
    
    def _analyze_general_quality(self, content: str, file_path: str) -> List[Dict]:
        """Analyze general code quality issues"""
        issues = []
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for long lines
            if len(line) > 120:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "desc": f"Line too long ({len(line)} characters)",
                    "severity": "low"
                })
            
            # Check for TODO/FIXME comments
            if re.search(r'(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                issues.append({
                    "file": file_path,
                    "line": i,
                    "desc": "TODO/FIXME comment found - consider addressing",
                    "severity": "low"
                })
        
        # Check for duplicate code (simple heuristic)
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith(('#', '//', '/*', '*')):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        for line, count in line_counts.items():
            if count > 2:
                issues.append({
                    "file": file_path,
                    "desc": f"Potential duplicate code found ({count} occurrences): {line[:50]}...",
                    "severity": "medium"
                })
        
        return issues
    
    def _select_sample_files(self, code_files: List[str], max_files: int = 5) -> List[str]:
        """Select representative files for LLM analysis"""
        if len(code_files) <= max_files:
            return code_files
        
        # Prioritize larger files and different file types
        files_with_size = []
        for file_path in code_files:
            try:
                size = os.path.getsize(file_path)
                files_with_size.append((file_path, size))
            except OSError:
                continue
        
        # Sort by size and take top files
        files_with_size.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in files_with_size[:max_files]]
    
    async def _analyze_with_llm(self, sample_files: List[str], repo_path: str) -> List[Dict]:
        """Use LLM to analyze code quality"""
        issues = []
        
        for file_path in sample_files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Analyze with LLM
                result = await self.llm_provider.analyze_code(
                    content, 
                    "quality",
                    {"file_path": relative_path, "file_type": Path(file_path).suffix}
                )
                
                if "issues" in result:
                    for issue in result["issues"]:
                        issue["file"] = relative_path
                        issues.append(issue)
                
            except Exception as e:
                self.logger.error(f"Error in LLM analysis for {file_path}: {e}")
        
        return issues
    
    def _calculate_quality_score(self, issues: List[Dict], total_files: int) -> int:
        """Calculate overall quality score based on issues"""
        if not issues:
            return 100
        
        # Weight issues by severity
        severity_weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}
        total_weight = sum(severity_weights.get(issue.get("severity", "low"), 1) for issue in issues)
        
        # Calculate penalty based on issues per file
        penalty = min(90, (total_weight / max(total_files, 1)) * 10)
        
        return max(10, 100 - int(penalty))
    
    def _generate_suggestions(self, issues: List[Dict]) -> List[str]:
        """Generate improvement suggestions based on issues"""
        suggestions = []
        
        # Categorize issues
        categories = {}
        for issue in issues:
            severity = issue.get("severity", "low")
            categories[severity] = categories.get(severity, 0) + 1
        
        if categories.get("high", 0) > 0 or categories.get("critical", 0) > 0:
            suggestions.append("Address high-severity issues first to improve code stability")
        
        if categories.get("medium", 0) > 5:
            suggestions.append("Refactor long functions and reduce code complexity")
        
        if any("docstring" in issue.get("desc", "") for issue in issues):
            suggestions.append("Add comprehensive docstrings to improve code documentation")
        
        if any("duplicate" in issue.get("desc", "").lower() for issue in issues):
            suggestions.append("Extract common code into reusable functions to reduce duplication")
        
        if any("TODO" in issue.get("desc", "") for issue in issues):
            suggestions.append("Review and address TODO comments before production deployment")
        
        return suggestions
    
    def _generate_summary(self, score: int, issues: List[Dict], total_files: int) -> str:
        """Generate analysis summary"""
        severity_counts = {}
        for issue in issues:
            severity = issue.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary = f"Analyzed {total_files} files with overall quality score of {score}/100. "
        
        if issues:
            issue_parts = []
            for severity in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    issue_parts.append(f"{count} {severity}")
            
            if issue_parts:
                summary += f"Found {len(issues)} issues: {', '.join(issue_parts)}."
        else:
            summary += "No quality issues detected."
        
        if score >= 90:
            summary += " Excellent code quality!"
        elif score >= 70:
            summary += " Good code quality with room for minor improvements."
        elif score >= 50:
            summary += " Moderate code quality - consider refactoring key areas."
        else:
            summary += " Code quality needs significant improvement."
        
        return summary
