"""
Code Quality Agent
Analyzes code for quality issues including complexity, duplication, maintainability,
code smells, and adherence to clean code principles.
"""

import re
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .base_agent import BaseAgent, Issue, AgentResult, Severity


class CodeQualityAgent(BaseAgent):
    """Agent for analyzing code quality issues."""
    
    def __init__(self, config_manager=None, llm_wrapper=None):
        super().__init__("code_quality", config_manager, llm_wrapper)
        self.complexity_thresholds = {
            'low': 10,
            'medium': 20,
            'high': 30
        }
        
    async def analyze_file(self, file_path: str, content: str, language: str) -> AgentResult:
        """
        Analyze a file for code quality issues.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            AgentResult with quality findings
        """
        findings = []
        
        # Rule-based checks
        findings.extend(self._check_function_length(file_path, content, language))
        findings.extend(self._check_cyclomatic_complexity(file_path, content, language))
        findings.extend(self._check_code_duplication(file_path, content, language))
        findings.extend(self._check_deep_nesting(file_path, content, language))
        findings.extend(self._check_long_parameter_lists(file_path, content, language))
        findings.extend(self._check_magic_numbers(file_path, content, language))
        findings.extend(self._check_dead_code(file_path, content, language))
        findings.extend(self._check_god_classes(file_path, content, language))
        findings.extend(self._check_naming_conventions(file_path, content, language))
        findings.extend(self._check_commented_out_code(file_path, content, language))
        
        # LLM analysis for deeper insights
        if self.llm_enabled and self.llm_wrapper:
            llm_findings = await self._llm_analyze(file_path, content, language, findings)
            findings.extend(llm_findings)
        
        # Deduplicate and calculate score
        findings = self._deduplicate_findings(findings)
        score = self._calculate_quality_score(findings, len(content.split('\n')))
        
        return AgentResult(
            agent_name=self.name,
            file_path=file_path,
            language=language,
            findings=findings,
            score=score,
            metadata={
                'total_lines': len(content.split('\n')),
                'issues_found': len(findings),
                'quality_level': self._get_quality_level(score)
            }
        )
    
    def _check_function_length(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for excessively long functions/methods."""
        findings = []
        max_lines = self.rules.get('max_function_length', 50)
        
        patterns = {
            'python': r'^\s*def\s+(\w+)\s*\(',
            'javascript': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)',
            'typescript': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)',
            'java': r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
            'go': r'^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(',
            'rust': r'^\s*(?:pub\s+)?fn\s+(\w+)\s*\(',
        }
        
        pattern = patterns.get(language)
        if not pattern:
            return findings
        
        lines = content.split('\n')
        func_starts = []
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                func_starts.append((i, line))
        
        # Calculate function lengths
        for idx, (start, line) in enumerate(func_starts):
            func_name = re.search(pattern, line)
            if func_name:
                func_name = next((g for g in func_name.groups() if g), 'unknown')
            else:
                func_name = 'unknown'
            
            # Find end of function (simplified - look for next function or end of file)
            if idx < len(func_starts) - 1:
                end = func_starts[idx + 1][0]
            else:
                end = len(lines)
            
            func_length = end - start
            
            if func_length > max_lines:
                severity = 'high' if func_length > max_lines * 2 else 'medium'
                findings.append(Issue(
                    type='long_function',
                    severity=severity,
                    message=f"Function '{func_name}' is too long ({func_length} lines, max: {max_lines})",
                    file_path=file_path,
                    line_number=start + 1,
                    code_snippet=line.strip(),
                    recommendation=f"Break down '{func_name}' into smaller, more focused functions. Consider extracting logic into helper methods."
                ))
        
        return findings
    
    def _check_cyclomatic_complexity(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Estimate cyclomatic complexity."""
        findings = []
        
        # Keywords that increase complexity
        complexity_keywords = {
            'python': ['if', 'elif', 'for', 'while', 'and', 'or', 'except', 'with'],
            'javascript': ['if', 'else if', 'for', 'while', '&&', '||', 'case', 'catch'],
            'typescript': ['if', 'else if', 'for', 'while', '&&', '||', 'case', 'catch'],
            'java': ['if', 'else if', 'for', 'while', '&&', '||', 'case', 'catch'],
            'go': ['if', 'for', 'switch', 'case', '&&', '||'],
            'rust': ['if', 'for', 'while', 'match', '&&', '||'],
        }
        
        keywords = complexity_keywords.get(language, [])
        if not keywords:
            return findings
        
        lines = content.split('\n')
        
        # Simple complexity estimation per function
        func_pattern = {
            'python': r'^\s*def\s+(\w+)',
            'javascript': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=)',
            'typescript': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=)',
            'java': r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
        }.get(language, r'^\s*def\s+(\w+)')
        
        current_func = None
        func_complexity = 0
        func_start_line = 0
        
        for i, line in enumerate(lines):
            func_match = re.match(func_pattern, line)
            if func_match:
                # Check previous function
                if current_func and func_complexity > self.complexity_thresholds['medium']:
                    severity = 'critical' if func_complexity > self.complexity_thresholds['high'] else 'high'
                    findings.append(Issue(
                        type='high_complexity',
                        severity=severity,
                        message=f"Function '{current_func}' has high cyclomatic complexity ({func_complexity})",
                        file_path=file_path,
                        line_number=func_start_line + 1,
                        code_snippet=lines[func_start_line].strip(),
                        recommendation=f"Simplify '{current_func}' by reducing conditional logic, extracting methods, or using design patterns."
                    ))
                
                # Start new function
                current_func = next((g for g in func_match.groups() if g), 'unknown')
                func_complexity = 1  # Base complexity
                func_start_line = i
            
            # Count complexity-increasing keywords
            for keyword in keywords:
                func_complexity += len(re.findall(r'\b' + keyword + r'\b', line))
        
        # Check last function
        if current_func and func_complexity > self.complexity_thresholds['medium']:
            severity = 'critical' if func_complexity > self.complexity_thresholds['high'] else 'high'
            findings.append(Issue(
                type='high_complexity',
                severity=severity,
                message=f"Function '{current_func}' has high cyclomatic complexity ({func_complexity})",
                file_path=file_path,
                line_number=func_start_line + 1,
                code_snippet=lines[func_start_line].strip() if func_start_line < len(lines) else '',
                recommendation=f"Simplify '{current_func}' by reducing conditional logic, extracting methods, or using design patterns."
            ))
        
        return findings
    
    def _check_code_duplication(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect potential code duplication."""
        findings = []
        min_duplicate_lines = self.rules.get('min_duplicate_lines', 5)
        
        lines = content.split('\n')
        # Normalize lines (remove whitespace and comments)
        normalized_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                normalized_lines.append('')
            else:
                normalized_lines.append(stripped)
        
        # Find duplicate sequences
        seen_sequences = defaultdict(list)
        
        for i in range(len(normalized_lines) - min_duplicate_lines):
            sequence = tuple(normalized_lines[i:i+min_duplicate_lines])
            if all(line for line in sequence):  # Skip if contains empty lines
                seen_sequences[sequence].append(i)
        
        # Report duplicates
        for sequence, positions in seen_sequences.items():
            if len(positions) > 1:
                findings.append(Issue(
                    type='code_duplication',
                    severity='medium',
                    message=f"Duplicate code block found ({min_duplicate_lines}+ lines appear {len(positions)} times)",
                    file_path=file_path,
                    line_number=positions[0] + 1,
                    code_snippet='\n'.join(lines[positions[0]:positions[0]+3]),
                    recommendation="Extract duplicate code into a reusable function or method. Also found at lines: " + 
                                 ', '.join(str(p+1) for p in positions[1:])
                ))
                break  # Only report first duplication to avoid spam
        
        return findings
    
    def _check_deep_nesting(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for deeply nested code blocks."""
        findings = []
        max_depth = self.rules.get('max_nesting_depth', 4)
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Count indentation depth
            indent = len(line) - len(line.lstrip())
            indent_size = 4 if language == 'python' else 2
            depth = indent // indent_size
            
            if depth > max_depth and line.strip():
                findings.append(Issue(
                    type='deep_nesting',
                    severity='medium',
                    message=f"Code is nested {depth} levels deep (max: {max_depth})",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation="Reduce nesting by extracting methods, using guard clauses, or inverting conditions."
                ))
                break  # Only report first occurrence
        
        return findings
    
    def _check_long_parameter_lists(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for functions with too many parameters."""
        findings = []
        max_params = self.rules.get('max_parameters', 5)
        
        patterns = {
            'python': r'def\s+(\w+)\s*\(([^)]+)\)',
            'javascript': r'function\s+(\w+)\s*\(([^)]+)\)',
            'typescript': r'function\s+(\w+)\s*\(([^)]+)\)',
            'java': r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(([^)]+)\)',
        }
        
        pattern = patterns.get(language)
        if not pattern:
            return findings
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            matches = re.finditer(pattern, line)
            for match in matches:
                func_name = match.group(1)
                params = match.group(2)
                
                # Count parameters
                param_count = len([p.strip() for p in params.split(',') if p.strip()])
                
                if param_count > max_params:
                    findings.append(Issue(
                        type='long_parameter_list',
                        severity='medium',
                        message=f"Function '{func_name}' has too many parameters ({param_count}, max: {max_params})",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation=f"Refactor '{func_name}' to use parameter objects, builders, or configuration objects."
                    ))
        
        return findings
    
    def _check_magic_numbers(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect magic numbers (unexplained numeric literals)."""
        findings = []
        
        # Skip common acceptable numbers
        acceptable_numbers = {0, 1, -1, 100, 1000}
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Skip comments and strings
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            
            # Find numeric literals (simplified)
            numbers = re.findall(r'\b(\d+\.?\d*)\b', line)
            
            for num_str in numbers:
                try:
                    num = float(num_str) if '.' in num_str else int(num_str)
                    
                    # Check if it's a magic number
                    if num not in acceptable_numbers and abs(num) > 1:
                        # Check if it's in a variable assignment (somewhat acceptable)
                        if '=' in line and line.index(num_str) > line.index('='):
                            continue
                        
                        findings.append(Issue(
                            type='magic_number',
                            severity='low',
                            message=f"Magic number '{num_str}' found without explanation",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation=f"Replace magic number with a named constant that explains its purpose."
                        ))
                        break  # One per line is enough
                except ValueError:
                    continue
        
        return findings
    
    def _check_dead_code(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect potentially dead/unreachable code."""
        findings = []
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for code after return statements
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.startswith('return ') and stripped and not stripped.startswith('}') and not stripped.startswith('#'):
                    findings.append(Issue(
                        type='dead_code',
                        severity='medium',
                        message="Unreachable code after return statement",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=stripped,
                        recommendation="Remove unreachable code or restructure the logic."
                    ))
            
            # Check for if (false) or if (0) patterns
            if re.search(r'if\s+\(?\s*(false|False|0|None|null)\s*\)?', stripped):
                findings.append(Issue(
                    type='dead_code',
                    severity='medium',
                    message="Conditional with constant false value",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=stripped,
                    recommendation="Remove dead conditional code."
                ))
        
        return findings
    
    def _check_god_classes(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect god classes (classes with too many responsibilities)."""
        findings = []
        max_methods = self.rules.get('max_class_methods', 20)
        
        if language not in ['python', 'java', 'javascript', 'typescript']:
            return findings
        
        patterns = {
            'python': (r'^class\s+(\w+)', r'^\s+def\s+(\w+)'),
            'java': (r'^(?:public\s+)?class\s+(\w+)', r'^\s+(?:public|private|protected).*\s+\w+\s+(\w+)\s*\('),
        }
        
        class_pattern, method_pattern = patterns.get(language, patterns['python'])
        
        lines = content.split('\n')
        current_class = None
        method_count = 0
        class_start_line = 0
        
        for i, line in enumerate(lines):
            class_match = re.match(class_pattern, line)
            if class_match:
                # Check previous class
                if current_class and method_count > max_methods:
                    findings.append(Issue(
                        type='god_class',
                        severity='high',
                        message=f"Class '{current_class}' has too many methods ({method_count}, max: {max_methods})",
                        file_path=file_path,
                        line_number=class_start_line + 1,
                        code_snippet=lines[class_start_line].strip(),
                        recommendation=f"Split '{current_class}' into smaller, more focused classes following Single Responsibility Principle."
                    ))
                
                current_class = class_match.group(1)
                method_count = 0
                class_start_line = i
            elif current_class and re.match(method_pattern, line):
                method_count += 1
        
        # Check last class
        if current_class and method_count > max_methods:
            findings.append(Issue(
                type='god_class',
                severity='high',
                message=f"Class '{current_class}' has too many methods ({method_count}, max: {max_methods})",
                file_path=file_path,
                line_number=class_start_line + 1,
                code_snippet=lines[class_start_line].strip() if class_start_line < len(lines) else '',
                recommendation=f"Split '{current_class}' into smaller, more focused classes following Single Responsibility Principle."
            ))
        
        return findings
    
    def _check_naming_conventions(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check naming conventions."""
        findings = []
        
        conventions = {
            'python': {
                'function': r'^def\s+([a-z_][a-z0-9_]*)\s*\(',
                'class': r'^class\s+([A-Z][a-zA-Z0-9]*)',
                'constant': r'^([A-Z][A-Z0-9_]*)\s*='
            },
            'javascript': {
                'function': r'function\s+([a-z][a-zA-Z0-9]*)\s*\(',
                'class': r'class\s+([A-Z][a-zA-Z0-9]*)',
                'constant': r'const\s+([A-Z][A-Z0-9_]*)\s*='
            }
        }
        
        conv = conventions.get(language)
        if not conv:
            return findings
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Check functions
            if 'function' in conv:
                func_matches = re.finditer(r'def\s+(\w+)|function\s+(\w+)', line)
                for match in func_matches:
                    name = next((g for g in match.groups() if g), None)
                    if name and not re.match(r'^[a-z_][a-z0-9_]*$', name):
                        findings.append(Issue(
                            type='naming_convention',
                            severity='low',
                            message=f"Function '{name}' doesn't follow naming convention (should be snake_case/camelCase)",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation=f"Rename '{name}' to follow language naming conventions."
                        ))
        
        return findings
    
    def _check_commented_out_code(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Detect commented-out code."""
        findings = []
        
        lines = content.split('\n')
        comment_patterns = {
            'python': r'^\s*#\s*(.+)',
            'javascript': r'^\s*//\s*(.+)',
            'typescript': r'^\s*//\s*(.+)',
            'java': r'^\s*//\s*(.+)',
        }
        
        pattern = comment_patterns.get(language)
        if not pattern:
            return findings
        
        code_indicators = ['def ', 'function ', 'class ', 'if ', 'for ', 'while ', 'return ', '=', ';']
        
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                comment_content = match.group(1).strip()
                # Check if comment looks like code
                if any(indicator in comment_content for indicator in code_indicators):
                    findings.append(Issue(
                        type='commented_code',
                        severity='low',
                        message="Commented-out code detected",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Remove commented-out code. Use version control instead."
                    ))
        
        return findings
    
    def _calculate_quality_score(self, findings: List[Issue], total_lines: int) -> float:
        """Calculate overall code quality score (0-100)."""
        if not findings:
            return 100.0
        
        # Weight by severity
        severity_weights = {
            'critical': 10,
            'high': 7,
            'medium': 4,
            'low': 2,
            'info': 1
        }
        
        total_penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        
        # Normalize by file size (more lenient for larger files)
        normalized_penalty = (total_penalty / max(total_lines / 10, 1)) * 10
        
        score = max(0, 100 - normalized_penalty)
        return round(score, 2)
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level description."""
        if score >= 90:
            return 'Excellent'
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
        """Generate LLM prompt for code quality analysis."""
        prompt = f"""Analyze this {language} code for quality issues beyond basic rule checks.

File: {file_path}

Code:
```{language}
{content[:2000]}  # Limit content size
```

Rule-based findings already detected:
{len(rule_findings)} issues found including: {', '.join(set(f.type for f in rule_findings[:5]))}

Please analyze for:
1. Design smells and anti-patterns
2. Code maintainability issues
3. Potential refactoring opportunities
4. Cohesion and coupling problems
5. Violation of SOLID principles
6. Any quality issues not caught by rules

Return findings in JSON format:
[
  {{
    "type": "design_smell",
    "severity": "medium",
    "message": "Description of issue",
    "line_number": 42,
    "recommendation": "How to fix it"
  }}
]
"""
        return prompt
    
    def _parse_llm_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse LLM response into Issue objects."""
        # Use the base class parser
        return super()._parse_llm_response(response, file_path)
