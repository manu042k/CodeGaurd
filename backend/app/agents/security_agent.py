"""
Security Agent - Evaluates the repository for potential security vulnerabilities and compliance issues
"""
import os
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_agent import BaseAgent

class SecurityAgent(BaseAgent):
    """Agent for analyzing security vulnerabilities and compliance issues"""
    
    def __init__(self, llm_provider):
        super().__init__("Security Agent", "Security", llm_provider)
        self.secret_patterns = self._load_secret_patterns()
        self.vulnerability_patterns = self._load_vulnerability_patterns()
    
    def _load_secret_patterns(self) -> Dict[str, str]:
        """Load patterns for detecting secrets and credentials"""
        return {
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'secret_key': r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?',
            'token': r'(?i)(token|auth[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
            'private_key': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            'aws_access_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret_key': r'(?i)aws[_-]?secret[_-]?access[_-]?key.*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
            'github_token': r'ghp_[a-zA-Z0-9]{36}',
            'jwt_token': r'eyJ[a-zA-Z0-9_\-]*\.eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*',
            'database_url': r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\']?(postgresql|mysql|mongodb)://[^"\'\s]+["\']?',
            'smtp_password': r'(?i)smtp[_-]?password\s*[=:]\s*["\']?([^"\'\s]{6,})["\']?'
        }
    
    def _load_vulnerability_patterns(self) -> Dict[str, Dict]:
        """Load patterns for detecting common vulnerabilities"""
        return {
            'sql_injection': {
                'patterns': [
                    r'execute\s*\(\s*["\'].*\+.*["\']',  # String concatenation in SQL
                    r'cursor\.execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',  # Python string formatting in SQL
                    r'query\s*=\s*["\'][^"\']*\+[^"\']*["\']',  # Query string concatenation
                    r'SELECT.*WHERE.*=.*\+',  # SQL concatenation
                ],
                'severity': 'high',
                'cwe': 'CWE-89'
            },
            'xss': {
                'patterns': [
                    r'innerHTML\s*=\s*[^;]+\+',  # JavaScript innerHTML with concatenation
                    r'document\.write\s*\(\s*[^)]*\+',  # document.write with concatenation
                    r'eval\s*\(\s*[^)]*\+',  # eval with concatenation
                    r'\$\{[^}]*user[^}]*\}',  # Template literal with user input
                ],
                'severity': 'high',
                'cwe': 'CWE-79'
            },
            'command_injection': {
                'patterns': [
                    r'os\.system\s*\(\s*[^)]*\+',  # os.system with concatenation
                    r'subprocess\.(call|run|Popen)\s*\(\s*[^)]*\+',  # subprocess with concatenation
                    r'exec\s*\(\s*[^)]*\+',  # exec with concatenation
                    r'shell_exec\s*\(\s*[^)]*\.\s*\$',  # PHP shell_exec with variables
                ],
                'severity': 'critical',
                'cwe': 'CWE-78'
            },
            'path_traversal': {
                'patterns': [
                    r'open\s*\(\s*[^)]*\+.*\.\./.*\)',  # File operations with path traversal
                    r'file_get_contents\s*\(\s*\$_[GET|POST]',  # PHP file operations with user input
                    r'readFile\s*\(\s*[^)]*\+',  # File read with concatenation
                ],
                'severity': 'high',
                'cwe': 'CWE-22'
            },
            'insecure_deserialization': {
                'patterns': [
                    r'pickle\.loads?\s*\(',  # Python pickle
                    r'yaml\.load\s*\(\s*[^,)]*\)',  # YAML load without safe_load
                    r'JSON\.parse\s*\(\s*[^)]*user',  # JSON parse with user input
                    r'unserialize\s*\(\s*\$_',  # PHP unserialize with user input
                ],
                'severity': 'high',
                'cwe': 'CWE-502'
            },
            'weak_crypto': {
                'patterns': [
                    r'hashlib\.(md5|sha1)\(',  # Weak hash functions
                    r'crypto\.createHash\s*\(\s*["\']md5["\']',  # Node.js weak hash
                    r'DES|RC4|MD5|SHA1',  # Weak encryption algorithms
                ],
                'severity': 'medium',
                'cwe': 'CWE-327'
            }
        }
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze repository for security vulnerabilities"""
        self.logger.info(f"Starting security analysis for {repo_path}")
        
        # Find relevant files
        code_files = self.find_security_relevant_files(repo_path)
        config_files = self.find_config_files(repo_path)
        
        if not code_files and not config_files:
            return self.create_result_structure(
                score=100,
                summary="No files found to analyze for security issues"
            )
        
        # Perform security analysis
        secret_issues = await self._scan_for_secrets(code_files + config_files, repo_path)
        vulnerability_issues = await self._scan_for_vulnerabilities(code_files, repo_path)
        config_issues = await self._analyze_config_security(config_files, repo_path)
        
        # LLM analysis on sample files
        sample_files = self._select_sample_files(code_files, max_files=3)
        llm_issues = await self._analyze_with_llm(sample_files, repo_path)
        
        # Combine all issues
        all_issues = secret_issues + vulnerability_issues + config_issues + llm_issues
        
        # Calculate score and generate summary
        score = self._calculate_security_score(all_issues)
        recommendations = self._generate_recommendations(all_issues)
        summary = self._generate_summary(score, all_issues, len(code_files))
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=recommendations
        )
    
    def find_security_relevant_files(self, repo_path: str) -> List[str]:
        """Find code files relevant for security analysis"""
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.php', '.rb', '.go', '.cs', '.cpp', '.c', '.h']
        return self.find_files_by_extension(repo_path, extensions)
    
    def find_config_files(self, repo_path: str) -> List[str]:
        """Find configuration files that might contain secrets"""
        config_patterns = [
            '*.env*', '*.config.*', '*.yml', '*.yaml', '*.json', '*.ini', '*.cfg', '*.conf',
            'Dockerfile*', 'docker-compose*', '*.properties', '*.pem', '*.key', '*.crt'
        ]
        
        config_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories but check hidden files
            dirs[:] = [d for d in dirs if not d.startswith('.git')]
            
            for file in files:
                file_path = os.path.join(root, file)
                if (file.startswith('.env') or 
                    any(file.endswith(ext.replace('*', '')) for ext in config_patterns) or
                    file in ['config', 'settings', 'secrets']):
                    config_files.append(file_path)
        
        return config_files
    
    async def _scan_for_secrets(self, files: List[str], repo_path: str) -> List[Dict]:
        """Scan files for hardcoded secrets and credentials"""
        issues = []
        
        for file_path in files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                for line_num, line in enumerate(content.split('\n'), 1):
                    for secret_type, pattern in self.secret_patterns.items():
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            # Skip obvious placeholder values
                            if self._is_placeholder_value(match.group()):
                                continue
                            
                            issues.append({
                                "file": relative_path,
                                "line": line_num,
                                "desc": f"Potential {secret_type.replace('_', ' ')} detected",
                                "severity": "critical" if secret_type in ['private_key', 'aws_secret_key'] else "high",
                                "cwe": "CWE-798",
                                "pattern": secret_type
                            })
            
            except Exception as e:
                self.logger.error(f"Error scanning file {file_path} for secrets: {e}")
        
        return issues
    
    def _is_placeholder_value(self, value: str) -> bool:
        """Check if a value is likely a placeholder rather than a real secret"""
        placeholders = [
            'your_api_key', 'your_secret', 'changeme', 'replace_me', 'example',
            'dummy', 'test', 'placeholder', 'xxx', 'yyy', 'zzz', '123456',
            'password', 'secret', 'token', 'key'
        ]
        
        value_lower = value.lower()
        return (len(value) < 8 or 
                any(placeholder in value_lower for placeholder in placeholders) or
                value in ['""', "''", '[]', '{}', 'null', 'none', 'undefined'])
    
    async def _scan_for_vulnerabilities(self, files: List[str], repo_path: str) -> List[Dict]:
        """Scan code files for common vulnerability patterns"""
        issues = []
        
        for file_path in files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                for vuln_type, vuln_info in self.vulnerability_patterns.items():
                    for pattern in vuln_info['patterns']:
                        for line_num, line in enumerate(content.split('\n'), 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    "file": relative_path,
                                    "line": line_num,
                                    "desc": f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                                    "severity": vuln_info['severity'],
                                    "cwe": vuln_info['cwe'],
                                    "pattern": vuln_type
                                })
            
            except Exception as e:
                self.logger.error(f"Error scanning file {file_path} for vulnerabilities: {e}")
        
        return issues
    
    async def _analyze_config_security(self, config_files: List[str], repo_path: str) -> List[Dict]:
        """Analyze configuration files for security issues"""
        issues = []
        
        for file_path in config_files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Check for common misconfigurations
                if 'docker' in file_path.lower():
                    issues.extend(self._check_docker_security(content, relative_path))
                
                if '.env' in file_path:
                    issues.extend(self._check_env_security(content, relative_path))
                
                if file_path.endswith(('.yml', '.yaml')):
                    issues.extend(self._check_yaml_security(content, relative_path))
            
            except Exception as e:
                self.logger.error(f"Error analyzing config file {file_path}: {e}")
        
        return issues
    
    def _check_docker_security(self, content: str, file_path: str) -> List[Dict]:
        """Check Docker files for security issues"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip().upper()
            
            # Check for running as root
            if line_stripped.startswith('USER ROOT') or 'UID=0' in line_stripped:
                issues.append({
                    "file": file_path,
                    "line": line_num,
                    "desc": "Container running as root user",
                    "severity": "high",
                    "cwe": "CWE-250"
                })
            
            # Check for ADD instead of COPY
            if line_stripped.startswith('ADD ') and not line_stripped.startswith('ADD --'):
                issues.append({
                    "file": file_path,
                    "line": line_num,
                    "desc": "Use COPY instead of ADD for local files",
                    "severity": "low",
                    "cwe": "CWE-693"
                })
        
        return issues
    
    def _check_env_security(self, content: str, file_path: str) -> List[Dict]:
        """Check environment files for security issues"""
        issues = []
        
        # Check if .env file is not in .gitignore
        gitignore_path = os.path.join(os.path.dirname(file_path), '.gitignore')
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
                if '.env' not in gitignore_content:
                    issues.append({
                        "file": file_path,
                        "desc": ".env file may not be properly ignored by git",
                        "severity": "medium",
                        "cwe": "CWE-200"
                    })
        except FileNotFoundError:
            issues.append({
                "file": file_path,
                "desc": "No .gitignore found - .env file may be committed to repository",
                "severity": "high",
                "cwe": "CWE-200"
            })
        
        return issues
    
    def _check_yaml_security(self, content: str, file_path: str) -> List[Dict]:
        """Check YAML files for security issues"""
        issues = []
        
        try:
            import yaml
            # Try to parse YAML
            data = yaml.safe_load(content)
            
            # Check for potential secrets in YAML values
            if isinstance(data, dict):
                self._check_dict_for_secrets(data, file_path, issues)
        
        except ImportError:
            # YAML library not available, skip detailed analysis
            pass
        except Exception as e:
            issues.append({
                "file": file_path,
                "desc": f"YAML parsing error: {str(e)}",
                "severity": "low"
            })
        
        return issues
    
    def _check_dict_for_secrets(self, data: dict, file_path: str, issues: List[Dict], path: str = ""):
        """Recursively check dictionary for potential secrets"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                self._check_dict_for_secrets(value, file_path, issues, current_path)
            elif isinstance(value, str):
                # Check if key suggests it's a secret
                if any(secret_word in key.lower() for secret_word in ['password', 'secret', 'key', 'token']):
                    if not self._is_placeholder_value(value):
                        issues.append({
                            "file": file_path,
                            "desc": f"Potential secret in configuration: {current_path}",
                            "severity": "medium",
                            "cwe": "CWE-798"
                        })
    
    def _select_sample_files(self, code_files: List[str], max_files: int = 3) -> List[str]:
        """Select representative files for LLM analysis"""
        if len(code_files) <= max_files:
            return code_files
        
        # Prioritize certain file types and larger files
        priority_extensions = ['.py', '.js', '.ts', '.php', '.java']
        
        prioritized = []
        others = []
        
        for file_path in code_files:
            if any(file_path.endswith(ext) for ext in priority_extensions):
                prioritized.append(file_path)
            else:
                others.append(file_path)
        
        # Take from prioritized first, then others
        result = prioritized[:max_files]
        if len(result) < max_files:
            result.extend(others[:max_files - len(result)])
        
        return result
    
    async def _analyze_with_llm(self, sample_files: List[str], repo_path: str) -> List[Dict]:
        """Use LLM for security analysis"""
        issues = []
        
        for file_path in sample_files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                result = await self.llm_provider.analyze_code(
                    content,
                    "security",
                    {"file_path": relative_path, "file_type": Path(file_path).suffix}
                )
                
                if "issues" in result:
                    for issue in result["issues"]:
                        issue["file"] = relative_path
                        issues.append(issue)
            
            except Exception as e:
                self.logger.error(f"Error in LLM security analysis for {file_path}: {e}")
        
        return issues
    
    def _calculate_security_score(self, issues: List[Dict]) -> int:
        """Calculate overall security score"""
        if not issues:
            return 100
        
        # Weight by severity
        severity_weights = {"low": 1, "medium": 5, "high": 15, "critical": 30}
        total_penalty = sum(severity_weights.get(issue.get("severity", "low"), 1) for issue in issues)
        
        # Cap the penalty to ensure minimum score
        penalty = min(85, total_penalty)
        
        return max(15, 100 - penalty)
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Categorize issues
        issue_types = {}
        severity_counts = {}
        
        for issue in issues:
            issue_type = issue.get("pattern", "other")
            severity = issue.get("severity", "low")
            
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate specific recommendations
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("URGENT: Address critical security vulnerabilities immediately")
        
        if issue_types.get("api_key", 0) > 0 or issue_types.get("secret_key", 0) > 0:
            recommendations.append("Move secrets to environment variables or secure key management")
        
        if issue_types.get("sql_injection", 0) > 0:
            recommendations.append("Use parameterized queries to prevent SQL injection")
        
        if issue_types.get("xss", 0) > 0:
            recommendations.append("Implement proper input validation and output encoding")
        
        if issue_types.get("command_injection", 0) > 0:
            recommendations.append("Avoid dynamic command execution; use safer alternatives")
        
        if any(".env" in issue.get("file", "") for issue in issues):
            recommendations.append("Ensure environment files are properly ignored by version control")
        
        recommendations.append("Implement regular security scanning in CI/CD pipeline")
        recommendations.append("Consider using security-focused linting tools")
        
        return recommendations
    
    def _generate_summary(self, score: int, issues: List[Dict], total_files: int) -> str:
        """Generate security analysis summary"""
        severity_counts = {}
        for issue in issues:
            severity = issue.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary = f"Security analysis of {total_files} files completed with score {score}/100. "
        
        if issues:
            critical = severity_counts.get("critical", 0)
            high = severity_counts.get("high", 0)
            medium = severity_counts.get("medium", 0)
            low = severity_counts.get("low", 0)
            
            issue_parts = []
            if critical: issue_parts.append(f"{critical} critical")
            if high: issue_parts.append(f"{high} high")
            if medium: issue_parts.append(f"{medium} medium")
            if low: issue_parts.append(f"{low} low")
            
            summary += f"Found {len(issues)} security issues: {', '.join(issue_parts)}."
            
            if critical > 0:
                summary += " IMMEDIATE ACTION REQUIRED for critical vulnerabilities."
            elif high > 0:
                summary += " High-priority security issues need prompt attention."
        else:
            summary += "No security vulnerabilities detected."
        
        return summary
