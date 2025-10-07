"""
Performance Agent
Analyzes code for performance issues including inefficient algorithms,
unnecessary operations, memory leaks, and optimization opportunities.
"""

import re
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, Issue, AgentResult, Severity


class PerformanceAgent(BaseAgent):
    """Agent for analyzing performance issues."""
    
    def __init__(self, config_manager=None, llm_wrapper=None):
        super().__init__("performance", config_manager, llm_wrapper)
        
    async def analyze_file(self, file_path: str, content: str, language: str) -> AgentResult:
        """
        Analyze a file for performance issues.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            AgentResult with performance findings
        """
        findings = []
        
        # Rule-based checks
        findings.extend(self._check_nested_loops(file_path, content, language))
        findings.extend(self._check_inefficient_operations(file_path, content, language))
        findings.extend(self._check_repeated_computations(file_path, content, language))
        findings.extend(self._check_string_concatenation(file_path, content, language))
        findings.extend(self._check_unnecessary_list_operations(file_path, content, language))
        findings.extend(self._check_database_queries(file_path, content, language))
        findings.extend(self._check_file_operations(file_path, content, language))
        findings.extend(self._check_blocking_operations(file_path, content, language))
        findings.extend(self._check_memory_leaks(file_path, content, language))
        findings.extend(self._check_regex_performance(file_path, content, language))
        
        # LLM analysis for deeper insights
        if self.llm_enabled and self.llm_wrapper:
            llm_findings = await self._llm_analyze(file_path, content, language, findings)
            findings.extend(llm_findings)
        
        # Deduplicate and calculate score
        findings = self._deduplicate_findings(findings)
        score = self._calculate_performance_score(findings)
        
        return AgentResult(
            agent_name=self.name,
            file_path=file_path,
            language=language,
            findings=findings,
            score=score,
            metadata={
                'issues_found': len(findings),
                'critical_issues': len([f for f in findings if f.severity == 'critical']),
                'performance_level': self._get_performance_level(score)
            }
        )
    
    def _check_nested_loops(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect nested loops that may cause performance issues."""
        findings = []
        
        loop_patterns = {
            'python': r'^\s+for\s+\w+\s+in\s+',
            'javascript': r'^\s+for\s*\(',
            'typescript': r'^\s+for\s*\(',
            'java': r'^\s+for\s*\(',
            'go': r'^\s+for\s+',
        }
        
        pattern = loop_patterns.get(language)
        if not pattern:
            return findings
        
        lines = content.split('\n')
        loop_stack = []
        
        for i, line in enumerate(lines):
            indent = len(line) - len(line.lstrip())
            
            # Pop loops that ended (decreased indent)
            while loop_stack and loop_stack[-1][1] >= indent:
                loop_stack.pop()
            
            # Check for loop
            if re.search(pattern, line):
                if len(loop_stack) >= 2:  # O(n^3) or worse
                    findings.append(Issue(
                        type='nested_loops',
                        severity='critical',
                        message=f"Deeply nested loops detected (O(n^{len(loop_stack) + 1}) complexity)",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Consider using more efficient algorithms (e.g., hash maps, sets) or restructuring the logic to reduce complexity."
                    ))
                elif len(loop_stack) >= 1:  # O(n^2)
                    findings.append(Issue(
                        type='nested_loops',
                        severity='high',
                        message=f"Nested loops detected (O(n^2) complexity)",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Evaluate if this nested loop can be optimized with better data structures or algorithms."
                    ))
                
                loop_stack.append((i, indent))
        
        return findings
    
    def _check_inefficient_operations(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for known inefficient operations."""
        findings = []
        
        inefficient_patterns = {
            'python': [
                (r'\.append\([^)]+\).*in\s+range\(', 'list_append_in_loop', 
                 'Use list comprehension instead of append in loop'),
                (r'\blist\([^)]*\)\s*\+\s*\blist\(', 'list_concatenation',
                 'Use extend() or itertools.chain() instead of list concatenation'),
                (r'\.keys\(\)\s+in\s+', 'unnecessary_keys',
                 'Remove unnecessary .keys() call when iterating dict'),
                (r'len\([^)]+\)\s*==\s*0', 'len_check_empty',
                 'Use "if not x:" instead of "len(x) == 0"'),
            ],
            'javascript': [
                (r'\.push\([^)]+\).*\.length', 'array_push_length',
                 'Avoid checking length in loop condition, cache it'),
                (r'document\.getElementById.*in.*loop', 'dom_query_in_loop',
                 'Cache DOM queries outside loops'),
            ],
        }
        
        patterns = inefficient_patterns.get(language, [])
        lines = content.split('\n')
        
        for pattern, issue_type, recommendation in patterns:
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    findings.append(Issue(
                        type=issue_type,
                        severity='medium',
                        message=f"Inefficient operation: {issue_type.replace('_', ' ')}",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation=recommendation
                    ))
        
        return findings
    
    def _check_repeated_computations(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect repeated computations that could be cached."""
        findings = []
        
        lines = content.split('\n')
        
        # Look for function calls inside loops
        loop_pattern = r'(for|while)\s+'
        function_call_pattern = r'(\w+)\s*\([^)]*\)'
        
        in_loop = False
        loop_start = 0
        seen_calls = {}
        
        for i, line in enumerate(lines):
            if re.search(loop_pattern, line):
                in_loop = True
                loop_start = i
                seen_calls = {}
            elif in_loop:
                # Check for function calls
                calls = re.findall(function_call_pattern, line)
                for call in calls:
                    if call in seen_calls:
                        findings.append(Issue(
                            type='repeated_computation',
                            severity='medium',
                            message=f"Function '{call}()' called multiple times in loop",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation=f"Cache the result of '{call}()' before the loop if it's a pure function."
                        ))
                        break
                    seen_calls[call] = i
                
                # End loop detection (simplified)
                indent = len(line) - len(line.lstrip())
                if indent == 0 and line.strip():
                    in_loop = False
        
        return findings
    
    def _check_string_concatenation(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for inefficient string concatenation in loops."""
        findings = []
        
        patterns = {
            'python': r'\+=.*["\'].*in\s+(range|enumerate)',
            'javascript': r'\+=.*["\'].*for\s*\(',
            'java': r'\+=.*".*for\s*\(',
        }
        
        pattern = patterns.get(language)
        if not pattern:
            return findings
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                solution = {
                    'python': 'Use list and join() or io.StringIO',
                    'javascript': 'Use array and join() or template literals',
                    'java': 'Use StringBuilder'
                }.get(language, 'Use appropriate string builder')
                
                findings.append(Issue(
                    type='inefficient_string_concat',
                    severity='high',
                    message="String concatenation in loop detected",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation=solution
                ))
        
        return findings
    
    def _check_unnecessary_list_operations(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for unnecessary list operations."""
        findings = []
        
        if language == 'python':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Check for list() on already iterable
                if re.search(r'list\(\[.*\]\)', line):
                    findings.append(Issue(
                        type='unnecessary_list_call',
                        severity='low',
                        message="Unnecessary list() call on list literal",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Remove redundant list() call"
                    ))
                
                # Check for creating list just to check membership
                if re.search(r'\bin\s+\[.*\]', line) and len(line.split(',')) > 3:
                    findings.append(Issue(
                        type='list_membership_check',
                        severity='medium',
                        message="Using list for membership check (O(n) instead of O(1))",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Use set instead of list for membership checks"
                    ))
        
        return findings
    
    def _check_database_queries(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for database query performance issues."""
        findings = []
        
        lines = content.split('\n')
        
        # N+1 query problem
        query_in_loop = False
        for i, line in enumerate(lines):
            if re.search(r'(for|while)\s+', line):
                query_in_loop = True
            elif query_in_loop and re.search(r'\.(query|execute|find|get)\(', line):
                findings.append(Issue(
                    type='n_plus_one_query',
                    severity='critical',
                    message="Potential N+1 query problem detected",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation="Use eager loading, join queries, or batch fetching to avoid N+1 problem"
                ))
                query_in_loop = False
        
        # SELECT * queries
        for i, line in enumerate(lines):
            if re.search(r'SELECT\s+\*\s+FROM', line, re.IGNORECASE):
                findings.append(Issue(
                    type='select_star_query',
                    severity='medium',
                    message="SELECT * query detected",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation="Select only required columns instead of using SELECT *"
                ))
        
        return findings
    
    def _check_file_operations(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for inefficient file operations."""
        findings = []
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Reading entire file into memory
            if re.search(r'\.read\(\)\s*$', line):
                findings.append(Issue(
                    type='read_entire_file',
                    severity='medium',
                    message="Reading entire file into memory",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation="Consider reading file in chunks or line by line for large files"
                ))
            
            # File operations in loop
            if re.search(r'(open\(|File\()', line):
                # Check if we're in a loop (simplified check)
                if i > 0 and re.search(r'(for|while)\s+', lines[i-1]):
                    findings.append(Issue(
                        type='file_operation_in_loop',
                        severity='high',
                        message="File operation inside loop",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Move file operations outside loop or batch them"
                    ))
        
        return findings
    
    def _check_blocking_operations(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for blocking operations that should be async."""
        findings = []
        
        blocking_ops = ['requests.get', 'requests.post', 'urlopen', 'sleep', 'time.sleep']
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            for op in blocking_ops:
                if op in line and 'async' not in lines[max(0, i-2):i+1]:
                    findings.append(Issue(
                        type='blocking_operation',
                        severity='medium',
                        message=f"Blocking operation '{op}' detected",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation=f"Consider using async version of '{op}' to avoid blocking"
                    ))
        
        return findings
    
    def _check_memory_leaks(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for potential memory leaks."""
        findings = []
        
        if language == 'python':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Global list/dict that keeps growing
                if re.search(r'(global|self\.).*\.(append|update|add)\(', line):
                    findings.append(Issue(
                        type='potential_memory_leak',
                        severity='medium',
                        message="Potential memory leak: unbounded collection growth",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Ensure collection has size limits or cleanup mechanism"
                    ))
        
        elif language == 'javascript':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Event listeners without cleanup
                if 'addEventListener' in line and 'removeEventListener' not in content:
                    findings.append(Issue(
                        type='event_listener_leak',
                        severity='medium',
                        message="Event listener added without cleanup",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Add removeEventListener in cleanup/unmount"
                    ))
        
        return findings
    
    def _check_regex_performance(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for potentially slow regex patterns."""
        findings = []
        
        lines = content.split('\n')
        
        # Patterns that can cause catastrophic backtracking
        dangerous_patterns = [
            (r'\(\.\*\)\+', 'Nested quantifiers can cause catastrophic backtracking'),
            (r'\(\.\+\)\+', 'Nested quantifiers can cause catastrophic backtracking'),
            (r'\(\.\*\)\*', 'Nested quantifiers can cause catastrophic backtracking'),
        ]
        
        for i, line in enumerate(lines):
            if 're.compile' in line or 'RegExp' in line or 'regex' in line.lower():
                for pattern, message in dangerous_patterns:
                    if re.search(pattern, line):
                        findings.append(Issue(
                            type='inefficient_regex',
                            severity='medium',
                            message=f"Potentially slow regex pattern: {message}",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation="Simplify regex pattern or use non-greedy quantifiers"
                        ))
        
        return findings
    
    def _calculate_performance_score(self, findings: List[Issue]) -> float:
        """Calculate performance score (0-100)."""
        if not findings:
            return 100.0
        
        severity_weights = {
            'critical': 15,
            'high': 10,
            'medium': 5,
            'low': 2,
            'info': 1
        }
        
        total_penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        score = max(0, 100 - total_penalty)
        
        return round(score, 2)
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description."""
        if score >= 90:
            return 'Optimal'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Critical'
    
    def _generate_llm_prompt(self, file_path: str, content: str, language: str,
                           rule_findings: List[Issue]) -> str:
        """Generate LLM prompt for performance analysis."""
        prompt = f"""Analyze this {language} code for performance issues beyond basic checks.

File: {file_path}

Code:
```{language}
{content[:2000]}
```

Rule-based findings: {len(rule_findings)} issues

Analyze for:
1. Algorithm complexity issues
2. Scalability concerns
3. Resource utilization problems
4. Caching opportunities
5. Async/await optimization
6. Database query optimization
7. Memory usage patterns

Return JSON array of findings with type, severity, message, line_number, recommendation.
"""
        return prompt
    
    def _parse_llm_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse LLM response into Issue objects."""
        return super()._parse_llm_response(response, file_path)
