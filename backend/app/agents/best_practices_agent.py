"""
Best Practices Agent
Analyzes code for adherence to language-specific best practices,
design patterns, and industry standards.
"""

import re
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, Issue, AgentResult, Severity


class BestPracticesAgent(BaseAgent):
    """Agent for analyzing best practices compliance."""
    
    def __init__(self, config_manager=None, llm_wrapper=None):
        super().__init__("best_practices", config_manager, llm_wrapper)
        
    async def analyze_file(self, file_path: str, content: str, language: str) -> AgentResult:
        """
        Analyze a file for best practices violations.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            AgentResult with best practices findings
        """
        findings = []
        
        # Rule-based checks
        findings.extend(self._check_error_handling(file_path, content, language))
        findings.extend(self._check_resource_management(file_path, content, language))
        findings.extend(self._check_type_hints(file_path, content, language))
        findings.extend(self._check_docstrings(file_path, content, language))
        findings.extend(self._check_imports(file_path, content, language))
        findings.extend(self._check_constants(file_path, content, language))
        findings.extend(self._check_global_variables(file_path, content, language))
        findings.extend(self._check_mutable_defaults(file_path, content, language))
        findings.extend(self._check_exception_handling(file_path, content, language))
        findings.extend(self._check_design_patterns(file_path, content, language))
        
        # LLM analysis
        if self.llm_enabled and self.llm_wrapper:
            llm_findings = await self._llm_analyze(file_path, content, language, findings)
            findings.extend(llm_findings)
        
        findings = self._deduplicate_findings(findings)
        score = self._calculate_best_practices_score(findings)
        
        return AgentResult(
            agent_name=self.name,
            file_path=file_path,
            language=language,
            findings=findings,
            score=score,
            metadata={
                'issues_found': len(findings),
                'compliance_level': self._get_compliance_level(score)
            }
        )
    
    def _check_error_handling(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check error handling patterns."""
        findings = []
        lines = content.split('\n')
        
        if language == 'python':
            # Bare except
            for i, line in enumerate(lines):
                if re.search(r'except\s*:', line):
                    findings.append(Issue(
                        type='bare_except',
                        severity='high',
                        message="Bare except clause catches all exceptions",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Catch specific exceptions instead of using bare except"
                    ))
                
                # Catching Exception
                if re.search(r'except\s+Exception\s*:', line):
                    findings.append(Issue(
                        type='broad_exception',
                        severity='medium',
                        message="Catching broad Exception type",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Catch specific exception types when possible"
                    ))
                
                # Empty except block
                if i < len(lines) - 1:
                    if 'except' in line and lines[i+1].strip() == 'pass':
                        findings.append(Issue(
                            type='silent_exception',
                            severity='high',
                            message="Silent exception handling (pass in except block)",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation="Log the exception or handle it appropriately, don't silently ignore"
                        ))
        
        elif language in ['javascript', 'typescript']:
            for i, line in enumerate(lines):
                # Empty catch blocks
                if i < len(lines) - 1:
                    if 'catch' in line and '}' in lines[i+1] and lines[i+1].strip() == '}':
                        findings.append(Issue(
                            type='empty_catch',
                            severity='high',
                            message="Empty catch block",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation="Handle or log the error appropriately"
                        ))
        
        return findings
    
    def _check_resource_management(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check proper resource management."""
        findings = []
        lines = content.split('\n')
        
        if language == 'python':
            # File operations without context manager
            for i, line in enumerate(lines):
                if re.search(r'open\s*\(', line) and 'with' not in line:
                    findings.append(Issue(
                        type='no_context_manager',
                        severity='medium',
                        message="File opened without context manager (with statement)",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Use 'with open() as f:' to ensure proper resource cleanup"
                    ))
        
        return findings
    
    def _check_type_hints(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for missing type hints."""
        findings = []
        
        if language == 'python':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Function without type hints
                func_match = re.match(r'^\s*def\s+(\w+)\s*\(([^)]*)\)', line)
                if func_match and '->' not in line:
                    func_name = func_match.group(1)
                    if not func_name.startswith('_'):  # Skip private methods for now
                        findings.append(Issue(
                            type='missing_type_hints',
                            severity='low',
                            message=f"Function '{func_name}' missing type hints",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation="Add type hints for parameters and return type"
                        ))
        
        elif language == 'typescript':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Function without return type
                if re.search(r'function\s+\w+\s*\([^)]*\)\s*{', line) and ':' not in line:
                    findings.append(Issue(
                        type='missing_return_type',
                        severity='low',
                        message="Function missing return type annotation",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Add explicit return type annotation"
                    ))
        
        return findings
    
    def _check_docstrings(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for missing or inadequate docstrings."""
        findings = []
        
        if language == 'python':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Public function/class without docstring
                if re.match(r'^(class|def)\s+(\w+)', line):
                    name = re.match(r'^(class|def)\s+(\w+)', line).group(2)
                    
                    # Skip private/magic methods
                    if name.startswith('_'):
                        continue
                    
                    # Check next non-empty line for docstring
                    has_docstring = False
                    for j in range(i+1, min(i+3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line.startswith('"""') or next_line.startswith("'''"):
                            has_docstring = True
                            break
                        if next_line and not next_line.startswith('#'):
                            break
                    
                    if not has_docstring:
                        findings.append(Issue(
                            type='missing_docstring',
                            severity='low',
                            message=f"Public {line.split()[0]} '{name}' missing docstring",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            recommendation="Add docstring describing purpose, parameters, and return value"
                        ))
        
        return findings
    
    def _check_imports(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check import statements."""
        findings = []
        lines = content.split('\n')
        
        if language == 'python':
            imports_section = True
            last_import_line = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Wildcard imports
                if re.match(r'from\s+\S+\s+import\s+\*', stripped):
                    findings.append(Issue(
                        type='wildcard_import',
                        severity='medium',
                        message="Wildcard import detected",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=stripped,
                        recommendation="Import specific names instead of using wildcard imports"
                    ))
                
                # Track imports location
                if stripped.startswith('import ') or stripped.startswith('from '):
                    last_import_line = i
                    if not imports_section and i > 10:  # Imports not at top
                        findings.append(Issue(
                            type='import_not_at_top',
                            severity='low',
                            message="Import statement not at top of file",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=stripped,
                            recommendation="Move imports to the top of the file"
                        ))
                
                # End of imports section
                if stripped and not stripped.startswith('import') and not stripped.startswith('from') and not stripped.startswith('#'):
                    imports_section = False
        
        return findings
    
    def _check_constants(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check constant definitions."""
        findings = []
        lines = content.split('\n')
        
        if language == 'python':
            for i, line in enumerate(lines):
                # UPPER_CASE variable that's reassigned (not truly constant)
                match = re.match(r'^([A-Z][A-Z0-9_]*)\s*=', line)
                if match:
                    const_name = match.group(1)
                    # Check if it's reassigned later
                    for j in range(i+1, len(lines)):
                        if re.match(f'^{const_name}\\s*=', lines[j]):
                            findings.append(Issue(
                                type='modified_constant',
                                severity='medium',
                                message=f"Constant '{const_name}' is reassigned",
                                file_path=file_path,
                                line_number=j + 1,
                                code_snippet=lines[j].strip(),
                                recommendation="Constants should not be reassigned. Use a variable name or make it truly immutable."
                            ))
                            break
        
        return findings
    
    def _check_global_variables(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for global variable usage."""
        findings = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.search(r'\bglobal\s+\w+', line):
                findings.append(Issue(
                    type='global_variable',
                    severity='medium',
                    message="Global variable usage detected",
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    recommendation="Avoid global variables. Use function parameters, class attributes, or dependency injection."
                ))
        
        return findings
    
    def _check_mutable_defaults(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for mutable default arguments."""
        findings = []
        
        if language == 'python':
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Function with list/dict default
                if re.search(r'def\s+\w+\([^)]*=\s*(\[\]|\{\})', line):
                    findings.append(Issue(
                        type='mutable_default_argument',
                        severity='high',
                        message="Mutable default argument detected",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Use None as default and create mutable object inside function"
                    ))
        
        return findings
    
    def _check_exception_handling(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check exception handling patterns."""
        findings = []
        lines = content.split('\n')
        
        # Check for try without finally/else
        in_try = False
        try_line = 0
        has_finally = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('try:'):
                in_try = True
                try_line = i
                has_finally = False
            elif in_try:
                if stripped.startswith('finally:'):
                    has_finally = True
                elif stripped.startswith('except'):
                    continue
                elif stripped and not line.startswith(' '):
                    # End of try block
                    in_try = False
        
        return findings
    
    def _check_design_patterns(self, file_path: str, content: str, language: str) -> List[Issue]:
        """Check for design pattern violations."""
        findings = []
        lines = content.split('\n')
        
        # Singleton pattern misuse
        if language == 'python':
            for i, line in enumerate(lines):
                # Multiple __init__ in singleton
                if '__new__' in line:
                    findings.append(Issue(
                        type='singleton_pattern',
                        severity='info',
                        message="Singleton pattern detected - ensure thread safety",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        recommendation="Ensure singleton implementation is thread-safe if used in concurrent context"
                    ))
        
        # God object anti-pattern (too many imports)
        import_count = len([l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')])
        if import_count > 20:
            findings.append(Issue(
                type='too_many_dependencies',
                severity='medium',
                message=f"File has {import_count} imports, indicating high coupling",
                file_path=file_path,
                line_number=1,
                code_snippet=f"{import_count} import statements",
                recommendation="Consider splitting into smaller, more focused modules"
            ))
        
        return findings
    
    def _calculate_best_practices_score(self, findings: List[Issue]) -> float:
        """Calculate best practices compliance score."""
        if not findings:
            return 100.0
        
        severity_weights = {
            'critical': 12,
            'high': 8,
            'medium': 5,
            'low': 2,
            'info': 0.5
        }
        
        total_penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        score = max(0, 100 - total_penalty)
        
        return round(score, 2)
    
    def _get_compliance_level(self, score: float) -> str:
        """Get compliance level description."""
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
        """Generate LLM prompt for best practices analysis."""
        prompt = f"""Analyze this {language} code for best practices violations.

File: {file_path}

Code:
```{language}
{content[:2000]}
```

Rule findings: {len(rule_findings)} issues

Analyze for:
1. SOLID principles violations
2. Design pattern misuse
3. Language-specific idioms
4. Error handling patterns
5. Code organization
6. Dependency management
7. Testing practices

Return JSON array of findings.
"""
        return prompt
    
    def _parse_llm_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse LLM response into Issue objects."""
        return super()._parse_llm_response(response, file_path)
