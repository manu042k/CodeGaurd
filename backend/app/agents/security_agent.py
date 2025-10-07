"""
Security Vulnerability Agent
Detects security vulnerabilities in code using hybrid rule-based + LLM approach.
"""

import re
import ast
from typing import List, Dict, Any, Optional
import time
from ..agents.base_agent import BaseAgent, AgentResult, Issue, Severity
from ..config import get_config_manager


class SecurityAgent(BaseAgent):
    """Agent for detecting security vulnerabilities"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security agent"""
        super().__init__(config)
        self.config_manager = get_config_manager()
        self.rules = self.config_manager.get_rules_for_agent("security")

    @property
    def name(self) -> str:
        return "SecurityAgent"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Detects security vulnerabilities including SQL injection, XSS, hardcoded secrets, and more"

    @property
    def supported_languages(self) -> List[str]:
        return ["python", "javascript", "typescript", "java", "php", "csharp", "ruby", "go"]

    async def _rule_based_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
        **kwargs
    ) -> AgentResult:
        """
        Fast rule-based security analysis using patterns
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            language: Programming language
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with security issues
        """
        start_time = time.time()
        issues: List[Issue] = []

        try:
            self.log_info(f"Running rule-based security analysis on {file_path}")

            # Check for SQL injection
            issues.extend(self._check_sql_injection(file_path, file_content, language))

            # Check for XSS vulnerabilities
            issues.extend(self._check_xss_vulnerability(file_path, file_content, language))

            # Check for hardcoded secrets
            issues.extend(self._check_hardcoded_secrets(file_path, file_content))

            # Check for weak cryptography
            issues.extend(self._check_weak_crypto(file_path, file_content, language))

            # Check for command injection
            issues.extend(self._check_command_injection(file_path, file_content, language))

            # Check for insecure file operations
            issues.extend(self._check_insecure_file_ops(file_path, file_content, language))

            # Check for insecure deserialization
            issues.extend(self._check_insecure_deserialization(file_path, file_content, language))

            # Language-specific checks
            if language == "python":
                issues.extend(self._check_python_specific(file_path, file_content))
            elif language in ["javascript", "typescript"]:
                issues.extend(self._check_javascript_specific(file_path, file_content))

            execution_time = time.time() - start_time
            score = self.calculate_score(issues)

            metrics = {
                "total_issues": len(issues),
                "critical_issues": sum(1 for i in issues if i.severity == Severity.CRITICAL),
                "high_issues": sum(1 for i in issues if i.severity == Severity.HIGH),
                "medium_issues": sum(1 for i in issues if i.severity == Severity.MEDIUM),
                "low_issues": sum(1 for i in issues if i.severity == Severity.LOW),
            }

            self.log_info(f"Found {len(issues)} security issues in {file_path}")

            return self._create_result(
                file_path=file_path,
                issues=issues,
                metrics=metrics,
                score=score,
                execution_time=execution_time,
            )

        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {str(e)}")
            execution_time = time.time() - start_time
            return self._create_result(
                file_path=file_path,
                error=str(e),
                execution_time=execution_time,
            )

    def _check_sql_injection(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for SQL injection vulnerabilities"""
        issues = []
        rule = self.rules.get("sql_injection", {})
        
        if not rule or language not in rule.get("languages", []):
            return issues

        patterns = rule.get("patterns", [])
        lines = content.split('\n')

        for line_num, line in enumerate(lines, start=1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        title="Potential SQL Injection",
                        description=f"SQL query appears to use string concatenation or formatting, which may lead to SQL injection",
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use parameterized queries or prepared statements instead of string concatenation",
                        rule_id="SQL_INJECTION",
                        category="security",
                    ))

        return issues

    def _check_xss_vulnerability(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for potential XSS vulnerabilities"""
        issues = []
        
        # Patterns that indicate potential XSS vulnerabilities
        xss_patterns = [
            r'innerHTML\s*=',  # JavaScript
            r'\.html\(',  # jQuery
            r'document\.write\(',  # JavaScript
            r'v-html',  # Vue.js
            r'dangerouslySetInnerHTML',  # React
            r'<%=\s*[^%]*%>',  # JSP/ERB without escaping
            r'{{.*\|safe}}',  # Django template
            r'{!!.*!!}',  # Laravel Blade
        ]
        
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern in xss_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Potential XSS Vulnerability",
                        description=f"Code appears to render user input without proper escaping, which may lead to XSS",
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Always escape user input before rendering. Use framework-provided escaping functions",
                        rule_id="XSS_VULNERABILITY",
                        category="security",
                    ))
        
        return issues

    def _check_hardcoded_secrets(self, file_path: str, content: str) -> List[Issue]:
        """Check for hardcoded secrets and credentials"""
        issues = []
        rule = self.rules.get("hardcoded_secrets", {})
        
        if not rule:
            return issues

        patterns = rule.get("patterns", [])
        lines = content.split('\n')

        # Skip if value looks like a placeholder
        placeholder_patterns = [
            r'your[_-]?.*?here',
            r'enter[_-]?.*?here',
            r'<.*?>',
            r'\$\{.*?\}',
            r'placeholder',
            r'example',
            r'xxxxx',
            r'\*\*\*\*',
        ]

        for line_num, line in enumerate(lines, start=1):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Check if it's a placeholder
                    is_placeholder = any(
                        re.search(p, line, re.IGNORECASE) for p in placeholder_patterns
                    )
                    
                    if not is_placeholder:
                        issues.append(Issue(
                            title="Hardcoded Secret Detected",
                            description=f"Potential hardcoded credential or secret found",
                            severity=Severity.CRITICAL,
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip()[:50] + "..." if len(line.strip()) > 50 else line.strip(),
                            suggestion="Move secrets to environment variables or a secure vault",
                            rule_id="HARDCODED_SECRET",
                            category="security",
                        ))

        return issues

    def _check_weak_crypto(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for weak cryptographic algorithms"""
        issues = []
        rule = self.rules.get("weak_crypto", {})
        
        if not rule or language not in rule.get("languages", []):
            return issues

        patterns = rule.get("patterns", [])
        lines = content.split('\n')

        for line_num, line in enumerate(lines, start=1):
            for pattern in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Weak Cryptographic Algorithm",
                        description=f"Usage of weak or deprecated cryptographic algorithm",
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use strong algorithms like SHA-256, SHA-3, or AES",
                        rule_id="WEAK_CRYPTO",
                        category="security",
                    ))

        return issues

    def _check_command_injection(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for command injection vulnerabilities"""
        issues = []
        rule = self.rules.get("command_injection", {})
        
        if not rule or language not in rule.get("languages", []):
            return issues

        patterns = rule.get("patterns", [])
        lines = content.split('\n')

        for line_num, line in enumerate(lines, start=1):
            for pattern in patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Potential Command Injection",
                        description=f"System command execution with user input may lead to command injection",
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Avoid using shell=True and validate/sanitize all inputs",
                        rule_id="COMMAND_INJECTION",
                        category="security",
                    ))

        return issues

    def _check_insecure_file_ops(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for insecure file operations"""
        issues = []
        lines = content.split('\n')

        # Path traversal patterns
        path_traversal_patterns = [
            r'open\(.*?\+.*?\)',
            r'readFile\(.*?\+.*?\)',
            r'writeFile\(.*?\+.*?\)',
        ]

        for line_num, line in enumerate(lines, start=1):
            for pattern in path_traversal_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Potential Path Traversal",
                        description=f"File operation with unsanitized path may allow path traversal",
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Validate and sanitize file paths, use allowlist of allowed directories",
                        rule_id="PATH_TRAVERSAL",
                        category="security",
                    ))

        return issues

    def _check_insecure_deserialization(
        self, file_path: str, content: str, language: str
    ) -> List[Issue]:
        """Check for insecure deserialization"""
        issues = []
        lines = content.split('\n')

        patterns = {
            "python": [r'pickle\.loads\(', r'yaml\.load\((?!.*?Loader=)'],
            "javascript": [r'eval\(.*?JSON', r'Function\('],
            "java": [r'ObjectInputStream', r'XMLDecoder'],
        }

        lang_patterns = patterns.get(language, [])
        
        for line_num, line in enumerate(lines, start=1):
            for pattern in lang_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Insecure Deserialization",
                        description=f"Insecure deserialization may allow arbitrary code execution",
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use safe deserialization methods and validate input data",
                        rule_id="INSECURE_DESERIALIZATION",
                        category="security",
                    ))

        return issues

    def _check_python_specific(self, file_path: str, content: str) -> List[Issue]:
        """Python-specific security checks"""
        issues = []
        lines = content.split('\n')

        # Check for eval/exec usage
        for line_num, line in enumerate(lines, start=1):
            if re.search(r'\beval\(', line) or re.search(r'\bexec\(', line):
                issues.append(Issue(
                    title="Dangerous Function Usage",
                    description=f"Use of eval() or exec() can execute arbitrary code",
                    severity=Severity.CRITICAL,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    suggestion="Avoid eval() and exec(), use ast.literal_eval() for safe evaluation",
                    rule_id="DANGEROUS_FUNCTION",
                    category="security",
                ))

        # Check for assert used for security
        for line_num, line in enumerate(lines, start=1):
            if re.search(r'assert\s+.*?password|assert\s+.*?token|assert\s+.*?auth', line, re.IGNORECASE):
                issues.append(Issue(
                    title="Assert Used for Security Check",
                    description=f"Assert statements are removed in optimized Python, should not be used for security",
                    severity=Severity.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    suggestion="Use proper if statements for security checks",
                    rule_id="ASSERT_SECURITY",
                    category="security",
                ))

        return issues

    def _check_javascript_specific(self, file_path: str, content: str) -> List[Issue]:
        """JavaScript/TypeScript-specific security checks"""
        issues = []
        lines = content.split('\n')

        # Check for dangerous functions
        dangerous_patterns = [
            (r'eval\(', "eval() can execute arbitrary code"),
            (r'new Function\(', "Function constructor can execute arbitrary code"),
            (r'setTimeout\(.*?[\'"].*?[\'\"]', "setTimeout with string argument can execute code"),
            (r'setInterval\(.*?[\'"].*?[\'\"]', "setInterval with string argument can execute code"),
        ]

        for line_num, line in enumerate(lines, start=1):
            for pattern, message in dangerous_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        title="Dangerous Function Usage",
                        description=message,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Avoid dynamic code execution",
                        rule_id="DANGEROUS_FUNCTION",
                        category="security",
                    ))

        return issues
    
    def _get_agent_specific_instructions(self) -> str:
        """Security-specific instructions for LLM analysis"""
        return """Perform a comprehensive security analysis. Look for:

1. INJECTION VULNERABILITIES:
   - SQL injection (beyond simple patterns)
   - Command injection
   - LDAP injection
   - XML injection
   - Template injection

2. AUTHENTICATION & AUTHORIZATION:
   - Broken authentication
   - Missing authorization checks
   - Insecure session management
   - JWT vulnerabilities

3. BUSINESS LOGIC FLAWS:
   - Race conditions
   - IDOR (Insecure Direct Object Reference)
   - Mass assignment vulnerabilities
   - Price manipulation

4. CRYPTOGRAPHY:
   - Weak algorithms
   - Insecure random number generation
   - Hardcoded cryptographic keys
   - Improper certificate validation

5. DATA EXPOSURE:
   - Sensitive data in logs
   - Information disclosure
   - Missing encryption
   - Insecure data storage

6. INPUT VALIDATION:
   - Missing input validation
   - Type confusion
   - Buffer overflows (C/C++)
   - Integer overflow/underflow

7. CONFIGURATION:
   - Debug mode enabled
   - Default credentials
   - Insecure defaults
   - Missing security headers

Focus on issues that could be exploited by attackers.
Consider the full context and data flow, not just individual lines."""
