"""
Static Tool Integration Agent - Runs conventional static tools and explains results with LLM reasoning
"""
import os
import subprocess
import json
import tempfile
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .base_agent import BaseAgent

class StaticToolAgent(BaseAgent):
    """Agent for running and analyzing static analysis tools"""
    
    def __init__(self, llm_provider):
        super().__init__("Static Tool Integration Agent", "Static Checks", llm_provider)
        self.tools_config = {
            'python': {
                'linters': ['flake8', 'pylint', 'pycodestyle'],
                'type_checkers': ['mypy'],
                'formatters': ['black', 'autopep8'],
                'security': ['bandit']
            },
            'javascript': {
                'linters': ['eslint', 'jshint'],
                'type_checkers': ['tsc'],
                'formatters': ['prettier'],
                'security': []
            },
            'typescript': {
                'linters': ['eslint', '@typescript-eslint'],
                'type_checkers': ['tsc'],
                'formatters': ['prettier'],
                'security': []
            }
        }
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run static analysis tools and analyze results"""
        self.logger.info(f"Starting static tool analysis for {repo_path}")
        
        # Detect project languages and find relevant files
        project_languages = self._detect_project_languages(repo_path)
        
        if not project_languages:
            return self.create_result_structure(
                score=100,
                summary="No supported languages detected for static analysis"
            )
        
        # Run static analysis tools for each language
        all_results = {}
        all_issues = []
        
        for language in project_languages:
            try:
                language_results = await self._analyze_language(repo_path, language)
                all_results[language] = language_results
                all_issues.extend(language_results.get('issues', []))
            
            except Exception as e:
                self.logger.error(f"Error analyzing {language}: {e}")
                all_issues.append({
                    "desc": f"Failed to analyze {language} files: {str(e)}",
                    "severity": "low"
                })
        
        # LLM analysis to explain and group results
        summary_analysis = await self._analyze_results_with_llm(all_results, repo_path)
        all_issues.extend(summary_analysis.get('issues', []))
        
        # Calculate score and generate summary
        score = self._calculate_static_score(all_issues, all_results)
        summary = self._generate_summary(score, all_results, project_languages)
        suggestions = self._generate_suggestions(all_issues, all_results)
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def _detect_project_languages(self, repo_path: str) -> List[str]:
        """Detect programming languages used in the project"""
        languages = set()
        
        # Count files by extension
        extension_counts = {}
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Map extensions to languages
        language_mappings = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go'
        }
        
        # Only include languages with significant file counts (>2 files)
        for ext, count in extension_counts.items():
            if count > 2 and ext in language_mappings:
                languages.add(language_mappings[ext])
        
        return list(languages)
    
    async def _analyze_language(self, repo_path: str, language: str) -> Dict[str, Any]:
        """Run static analysis tools for a specific language"""
        results = {
            'language': language,
            'tools_run': [],
            'issues': [],
            'tool_results': {}
        }
        
        tools_config = self.tools_config.get(language, {})
        
        # Run linters
        for linter in tools_config.get('linters', []):
            try:
                linter_result = await self._run_linter(repo_path, language, linter)
                if linter_result:
                    results['tools_run'].append(linter)
                    results['tool_results'][linter] = linter_result
                    results['issues'].extend(linter_result.get('issues', []))
            except Exception as e:
                self.logger.error(f"Error running {linter}: {e}")
        
        # Run type checkers
        for type_checker in tools_config.get('type_checkers', []):
            try:
                type_result = await self._run_type_checker(repo_path, language, type_checker)
                if type_result:
                    results['tools_run'].append(type_checker)
                    results['tool_results'][type_checker] = type_result
                    results['issues'].extend(type_result.get('issues', []))
            except Exception as e:
                self.logger.error(f"Error running {type_checker}: {e}")
        
        # Run security tools
        for security_tool in tools_config.get('security', []):
            try:
                security_result = await self._run_security_tool(repo_path, language, security_tool)
                if security_result:
                    results['tools_run'].append(security_tool)
                    results['tool_results'][security_tool] = security_result
                    results['issues'].extend(security_result.get('issues', []))
            except Exception as e:
                self.logger.error(f"Error running {security_tool}: {e}")
        
        return results
    
    async def _run_linter(self, repo_path: str, language: str, linter: str) -> Optional[Dict[str, Any]]:
        """Run a linter tool"""
        if language == 'python' and linter == 'flake8':
            return await self._run_flake8(repo_path)
        elif language == 'python' and linter == 'pylint':
            return await self._run_pylint(repo_path)
        elif language in ['javascript', 'typescript'] and linter == 'eslint':
            return await self._run_eslint(repo_path)
        
        return None
    
    async def _run_flake8(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run flake8 Python linter"""
        try:
            # Find Python files
            python_files = self.find_files_by_extension(repo_path, ['.py'])
            if not python_files:
                return None
            
            # Run flake8 with JSON-like output
            cmd = ['flake8', '--format=json'] + [os.path.relpath(f, repo_path) for f in python_files[:10]]
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            issues = []
            if result.stdout:
                # flake8 doesn't have native JSON output, parse line by line
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            file_path, line_num, col, message = parts
                            
                            # Extract error code
                            error_code = ''
                            if ' ' in message:
                                first_word = message.strip().split()[0]
                                if first_word.startswith(('E', 'W', 'F')):
                                    error_code = first_word
                            
                            severity = self._map_flake8_severity(error_code)
                            
                            issues.append({
                                "file": file_path.strip(),
                                "line": int(line_num) if line_num.isdigit() else 0,
                                "desc": message.strip(),
                                "severity": severity,
                                "tool": "flake8",
                                "code": error_code
                            })
            
            return {
                'tool': 'flake8',
                'exit_code': result.returncode,
                'issues': issues,
                'files_checked': len(python_files[:10])
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    def _map_flake8_severity(self, error_code: str) -> str:
        """Map flake8 error codes to severity levels"""
        if error_code.startswith('F'):  # Fatal errors (syntax, import issues)
            return 'high'
        elif error_code.startswith('E'):  # PEP8 errors
            if error_code.startswith('E9'):  # Runtime errors
                return 'high'
            return 'medium'
        elif error_code.startswith('W'):  # Warnings
            return 'low'
        return 'low'
    
    async def _run_pylint(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run pylint Python linter"""
        try:
            python_files = self.find_files_by_extension(repo_path, ['.py'])
            if not python_files:
                return None
            
            # Run pylint with JSON output
            cmd = ['pylint', '--output-format=json', '--exit-zero'] + [os.path.relpath(f, repo_path) for f in python_files[:5]]
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=120
            )
            
            issues = []
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    for item in pylint_data:
                        severity = self._map_pylint_severity(item.get('type', ''))
                        issues.append({
                            "file": item.get('path', ''),
                            "line": item.get('line', 0),
                            "desc": item.get('message', ''),
                            "severity": severity,
                            "tool": "pylint",
                            "code": item.get('message-id', '')
                        })
                except json.JSONDecodeError:
                    pass
            
            return {
                'tool': 'pylint',
                'exit_code': result.returncode,
                'issues': issues,
                'files_checked': len(python_files[:5])
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    def _map_pylint_severity(self, msg_type: str) -> str:
        """Map pylint message types to severity levels"""
        mapping = {
            'error': 'high',
            'fatal': 'critical',
            'warning': 'medium',
            'refactor': 'low',
            'convention': 'low',
            'info': 'low'
        }
        return mapping.get(msg_type.lower(), 'low')
    
    async def _run_eslint(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run ESLint for JavaScript/TypeScript"""
        try:
            # Find JS/TS files
            js_files = self.find_files_by_extension(repo_path, ['.js', '.jsx', '.ts', '.tsx'])
            if not js_files:
                return None
            
            # Check if eslint is available and configured
            eslint_config_files = ['.eslintrc.js', '.eslintrc.json', '.eslintrc.yml', 'eslint.config.js']
            has_config = any(
                os.path.exists(os.path.join(repo_path, config_file)) 
                for config_file in eslint_config_files
            )
            
            if not has_config:
                # Create basic ESLint config
                basic_config = {
                    "env": {"browser": True, "es2021": True, "node": True},
                    "extends": ["eslint:recommended"],
                    "parserOptions": {"ecmaVersion": 12, "sourceType": "module"},
                    "rules": {}
                }
                
                config_path = os.path.join(repo_path, '.eslintrc.json')
                with open(config_path, 'w') as f:
                    json.dump(basic_config, f, indent=2)
            
            # Run ESLint
            cmd = ['eslint', '--format=json'] + [os.path.relpath(f, repo_path) for f in js_files[:10]]
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            issues = []
            if result.stdout:
                try:
                    eslint_data = json.loads(result.stdout)
                    for file_result in eslint_data:
                        file_path = file_result.get('filePath', '')
                        for message in file_result.get('messages', []):
                            severity = self._map_eslint_severity(message.get('severity', 1))
                            issues.append({
                                "file": os.path.relpath(file_path, repo_path) if file_path else '',
                                "line": message.get('line', 0),
                                "desc": message.get('message', ''),
                                "severity": severity,
                                "tool": "eslint",
                                "code": message.get('ruleId', '')
                            })
                except json.JSONDecodeError:
                    pass
            
            return {
                'tool': 'eslint',
                'exit_code': result.returncode,
                'issues': issues,
                'files_checked': len(js_files[:10])
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    def _map_eslint_severity(self, severity: int) -> str:
        """Map ESLint severity to our levels"""
        if severity == 2:  # Error
            return 'medium'
        else:  # Warning
            return 'low'
    
    async def _run_type_checker(self, repo_path: str, language: str, type_checker: str) -> Optional[Dict[str, Any]]:
        """Run type checker"""
        if language == 'python' and type_checker == 'mypy':
            return await self._run_mypy(repo_path)
        elif language in ['javascript', 'typescript'] and type_checker == 'tsc':
            return await self._run_typescript_compiler(repo_path)
        
        return None
    
    async def _run_mypy(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run mypy type checker"""
        try:
            python_files = self.find_files_by_extension(repo_path, ['.py'])
            if not python_files:
                return None
            
            # Run mypy with JSON output
            cmd = ['mypy', '--show-error-codes', '--no-error-summary'] + [os.path.relpath(f, repo_path) for f in python_files[:5]]
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=90
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line and 'error:' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 3:
                            file_path = parts[0].strip()
                            line_num = parts[1].strip()
                            message = ':'.join(parts[2:]).replace('error:', '').strip()
                            
                            issues.append({
                                "file": file_path,
                                "line": int(line_num) if line_num.isdigit() else 0,
                                "desc": f"Type error: {message}",
                                "severity": "medium",
                                "tool": "mypy"
                            })
            
            return {
                'tool': 'mypy',
                'exit_code': result.returncode,
                'issues': issues,
                'files_checked': len(python_files[:5])
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    async def _run_typescript_compiler(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run TypeScript compiler"""
        try:
            # Check for tsconfig.json
            tsconfig_path = os.path.join(repo_path, 'tsconfig.json')
            if not os.path.exists(tsconfig_path):
                return None
            
            # Run tsc with no emit to just check types
            cmd = ['tsc', '--noEmit', '--pretty', 'false']
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if '(' in line and ')' in line and ':' in line:
                        # Parse TypeScript error format: file.ts(line,column): error message
                        match = re.search(r'(.+?)\((\d+),(\d+)\): (.+)', line)
                        if match:
                            file_path, line_num, col, message = match.groups()
                            
                            issues.append({
                                "file": os.path.relpath(file_path, repo_path),
                                "line": int(line_num),
                                "desc": f"TypeScript: {message}",
                                "severity": "medium",
                                "tool": "tsc"
                            })
            
            return {
                'tool': 'tsc',
                'exit_code': result.returncode,
                'issues': issues
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    async def _run_security_tool(self, repo_path: str, language: str, security_tool: str) -> Optional[Dict[str, Any]]:
        """Run security analysis tool"""
        if language == 'python' and security_tool == 'bandit':
            return await self._run_bandit(repo_path)
        
        return None
    
    async def _run_bandit(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Run bandit security scanner for Python"""
        try:
            python_files = self.find_files_by_extension(repo_path, ['.py'])
            if not python_files:
                return None
            
            # Run bandit with JSON output
            cmd = ['bandit', '-f', 'json', '-r', '.']
            
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            issues = []
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    for finding in bandit_data.get('results', []):
                        severity = self._map_bandit_severity(finding.get('issue_severity', 'LOW'))
                        
                        issues.append({
                            "file": os.path.relpath(finding.get('filename', ''), repo_path),
                            "line": finding.get('line_number', 0),
                            "desc": f"Security: {finding.get('issue_text', '')}",
                            "severity": severity,
                            "tool": "bandit",
                            "code": finding.get('test_id', '')
                        })
                except json.JSONDecodeError:
                    pass
            
            return {
                'tool': 'bandit',
                'exit_code': result.returncode,
                'issues': issues
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return None
    
    def _map_bandit_severity(self, bandit_severity: str) -> str:
        """Map bandit severity to our levels"""
        mapping = {
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low'
        }
        return mapping.get(bandit_severity.upper(), 'low')
    
    async def _analyze_results_with_llm(self, all_results: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Use LLM to analyze and summarize static tool results"""
        issues = []
        
        if not all_results:
            return {"issues": issues}
        
        try:
            # Prepare summary of all tool results
            summary_text = "Static Analysis Results Summary:\n\n"
            
            for language, results in all_results.items():
                summary_text += f"{language.upper()} Analysis:\n"
                summary_text += f"Tools run: {', '.join(results.get('tools_run', []))}\n"
                summary_text += f"Issues found: {len(results.get('issues', []))}\n"
                
                # Group issues by severity
                severity_counts = {}
                for issue in results.get('issues', []):
                    severity = issue.get('severity', 'low')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                if severity_counts:
                    severity_summary = ', '.join([f"{count} {severity}" for severity, count in severity_counts.items()])
                    summary_text += f"Severity breakdown: {severity_summary}\n"
                
                summary_text += "\n"
            
            # Analyze with LLM for insights
            result = await self.llm_provider.analyze_code(
                summary_text,
                "static_tools",
                {"analysis_type": "static_tool_summary", "repo_path": repo_path}
            )
            
            if "issues" in result:
                issues.extend(result["issues"])
        
        except Exception as e:
            self.logger.error(f"Error in LLM static tool analysis: {e}")
        
        return {"issues": issues}
    
    def _calculate_static_score(self, issues: List[Dict], all_results: Dict[str, Any]) -> int:
        """Calculate overall static analysis score"""
        base_score = 100
        
        # Penalty for issues
        severity_weights = {"low": 0.5, "medium": 2, "high": 8, "critical": 20}
        issue_penalty = sum(severity_weights.get(issue.get("severity", "low"), 0.5) for issue in issues)
        
        # Bonus for running tools successfully
        tools_run = sum(len(results.get('tools_run', [])) for results in all_results.values())
        tools_bonus = min(15, tools_run * 3)  # Max 15 points for running tools
        
        # Penalty for not running any tools
        if tools_run == 0:
            issue_penalty += 20
        
        # Calculate final score
        final_score = base_score - issue_penalty + tools_bonus
        return max(0, min(100, int(final_score)))
    
    def _generate_suggestions(self, issues: List[Dict], all_results: Dict[str, Any]) -> List[str]:
        """Generate static analysis improvement suggestions"""
        suggestions = []
        
        # Tool-specific suggestions
        tools_run = set()
        for results in all_results.values():
            tools_run.update(results.get('tools_run', []))
        
        if not tools_run:
            suggestions.append("Set up static analysis tools (linters, type checkers) in your development workflow")
        
        # Language-specific suggestions
        for language, results in all_results.items():
            language_tools = results.get('tools_run', [])
            
            if language == 'python':
                if 'flake8' not in language_tools and 'pylint' not in language_tools:
                    suggestions.append("Add Python linting (flake8 or pylint) to catch style and logic issues")
                if 'mypy' not in language_tools:
                    suggestions.append("Consider using mypy for Python type checking")
                if 'bandit' not in language_tools:
                    suggestions.append("Add bandit security scanning for Python code")
            
            elif language in ['javascript', 'typescript']:
                if 'eslint' not in language_tools:
                    suggestions.append("Set up ESLint for JavaScript/TypeScript code quality")
                if language == 'typescript' and 'tsc' not in language_tools:
                    suggestions.append("Enable TypeScript compiler type checking")
        
        # Issue-based suggestions
        high_severity_issues = [i for i in issues if i.get('severity') in ['high', 'critical']]
        if high_severity_issues:
            suggestions.append("Address high-severity static analysis issues immediately")
        
        security_issues = [i for i in issues if 'security' in i.get('desc', '').lower()]
        if security_issues:
            suggestions.append("Fix security issues identified by static analysis tools")
        
        type_issues = [i for i in issues if 'type' in i.get('desc', '').lower()]
        if type_issues:
            suggestions.append("Improve type annotations and fix type-related issues")
        
        # General suggestions
        suggestions.append("Integrate static analysis tools into your CI/CD pipeline")
        suggestions.append("Configure pre-commit hooks to run static analysis before commits")
        suggestions.append("Set up IDE/editor integration for real-time static analysis feedback")
        
        return suggestions
    
    def _generate_summary(self, score: int, all_results: Dict[str, Any], languages: List[str]) -> str:
        """Generate static analysis summary"""
        summary = f"Static analysis completed with score {score}/100. "
        summary += f"Analyzed {len(languages)} language(s): {', '.join(languages)}. "
        
        # Tools summary
        total_tools = sum(len(results.get('tools_run', [])) for results in all_results.values())
        total_issues = sum(len(results.get('issues', [])) for results in all_results.values())
        
        summary += f"Ran {total_tools} static analysis tools and found {total_issues} issues. "
        
        # Severity breakdown
        all_issues = []
        for results in all_results.values():
            all_issues.extend(results.get('issues', []))
        
        if all_issues:
            severity_counts = {}
            for issue in all_issues:
                severity = issue.get('severity', 'low')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            severity_parts = []
            for severity in ['critical', 'high', 'medium', 'low']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    severity_parts.append(f"{count} {severity}")
            
            if severity_parts:
                summary += f"Issue breakdown: {', '.join(severity_parts)}. "
        
        # Overall assessment
        if score >= 90:
            summary += "Excellent static analysis results!"
        elif score >= 75:
            summary += "Good code quality with minor static analysis issues."
        elif score >= 50:
            summary += "Some static analysis issues need attention."
        else:
            summary += "Significant static analysis issues require immediate action."
        
        return summary
