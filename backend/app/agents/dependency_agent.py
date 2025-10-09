"""
Dependency & License Agent - Reviews third-party dependencies and licensing issues
"""
import os
import json
import re
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .base_agent import BaseAgent

class DependencyAgent(BaseAgent):
    """Agent for analyzing dependencies, licenses, and package management"""
    
    def __init__(self, llm_provider):
        super().__init__("Dependency & License Agent", "Dependencies", llm_provider)
        self.risky_licenses = ['GPL', 'AGPL', 'LGPL', 'SSPL', 'BSL']
        self.safe_licenses = ['MIT', 'Apache', 'BSD', 'ISC', 'Unlicense']
        self.dependency_files = {
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock'],
            'javascript': ['package.json', 'package-lock.json', 'yarn.lock', 'npm-shrinkwrap.json'],
            'java': ['pom.xml', 'build.gradle', 'gradle.properties'],
            'ruby': ['Gemfile', 'Gemfile.lock'],
            'php': ['composer.json', 'composer.lock'],
            'go': ['go.mod', 'go.sum'],
            'rust': ['Cargo.toml', 'Cargo.lock']
        }
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze repository dependencies and licenses"""
        self.logger.info(f"Starting dependency analysis for {repo_path}")
        
        # Find dependency files
        dependency_files = self.find_dependency_files(repo_path)
        
        if not dependency_files:
            return self.create_result_structure(
                score=95,
                summary="No dependency files found - no dependencies to analyze"
            )
        
        # Analyze different aspects
        dependency_analysis = await self._analyze_dependencies(dependency_files, repo_path)
        security_analysis = await self._analyze_security_vulnerabilities(dependency_files, repo_path)
        license_analysis = await self._analyze_licenses(dependency_files, repo_path)
        management_analysis = await self._analyze_dependency_management(dependency_files, repo_path)
        
        # LLM analysis for dependency best practices
        llm_analysis = await self._analyze_with_llm(dependency_files[:2], repo_path)
        
        # Combine all issues
        all_issues = (dependency_analysis.get('issues', []) + 
                     security_analysis.get('issues', []) + 
                     license_analysis.get('issues', []) + 
                     management_analysis.get('issues', []) + 
                     llm_analysis.get('issues', []))
        
        # Calculate score
        score = self._calculate_dependency_score(
            all_issues, dependency_analysis, security_analysis, license_analysis
        )
        
        # Generate summary and suggestions
        summary = self._generate_summary(score, dependency_analysis, security_analysis, license_analysis)
        suggestions = self._generate_suggestions(all_issues, dependency_analysis, security_analysis)
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def find_dependency_files(self, repo_path: str) -> List[Tuple[str, str]]:
        """Find dependency files and their types"""
        found_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common exclude patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'dist', 'build']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Determine file type and ecosystem
                for ecosystem, patterns in self.dependency_files.items():
                    if any(pattern in file.lower() for pattern in patterns):
                        found_files.append((file_path, ecosystem))
                        break
        
        return found_files
    
    async def _analyze_dependencies(self, dependency_files: List[Tuple[str, str]], repo_path: str) -> Dict[str, Any]:
        """Analyze dependency management and versions"""
        issues = []
        dependencies = {}
        
        for file_path, ecosystem in dependency_files:
            try:
                relative_path = os.path.relpath(file_path, repo_path)
                file_deps = self._parse_dependency_file(file_path, ecosystem)
                
                if file_deps:
                    dependencies[relative_path] = file_deps
                    
                    # Analyze dependencies
                    file_issues = self._analyze_file_dependencies(file_deps, relative_path, ecosystem)
                    issues.extend(file_issues)
                
            except Exception as e:
                self.logger.error(f"Error analyzing dependency file {file_path}: {e}")
                issues.append({
                    "file": os.path.relpath(file_path, repo_path),
                    "desc": f"Could not parse dependency file: {str(e)}",
                    "severity": "low"
                })
        
        return {
            "issues": issues,
            "dependencies": dependencies,
            "total_dependencies": sum(len(deps) for deps in dependencies.values())
        }
    
    def _parse_dependency_file(self, file_path: str, ecosystem: str) -> Dict[str, Any]:
        """Parse a dependency file based on its ecosystem"""
        dependencies = {}
        
        try:
            if ecosystem == 'python':
                dependencies = self._parse_python_dependencies(file_path)
            elif ecosystem == 'javascript':
                dependencies = self._parse_javascript_dependencies(file_path)
            elif ecosystem == 'java':
                dependencies = self._parse_java_dependencies(file_path)
            # Add more ecosystems as needed
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
        
        return dependencies
    
    def _parse_python_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Parse Python dependency files"""
        dependencies = {}
        file_name = os.path.basename(file_path).lower()
        
        if file_name == 'requirements.txt':
            content = self.get_file_content(file_path)
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package==version or package>=version
                        match = re.match(r'^([a-zA-Z0-9_\-\.]+)([>=<~!]+)(.+)$', line)
                        if match:
                            package, operator, version = match.groups()
                            dependencies[package] = {
                                'version': version.strip(),
                                'operator': operator,
                                'raw': line
                            }
                        elif '==' not in line and '>=' not in line and '<=' not in line:
                            # Package without version specification
                            dependencies[line] = {
                                'version': 'unspecified',
                                'operator': '',
                                'raw': line
                            }
        
        elif file_name == 'pyproject.toml':
            # Basic TOML parsing for dependencies
            content = self.get_file_content(file_path)
            if content and '[tool.poetry.dependencies]' in content:
                in_deps = False
                for line in content.split('\n'):
                    if '[tool.poetry.dependencies]' in line:
                        in_deps = True
                        continue
                    elif line.startswith('[') and in_deps:
                        break
                    elif in_deps and '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            package = parts[0].strip()
                            version = parts[1].strip().strip('"\'')
                            dependencies[package] = {
                                'version': version,
                                'operator': '==',
                                'raw': line.strip()
                            }
        
        return dependencies
    
    def _parse_javascript_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Parse JavaScript dependency files"""
        dependencies = {}
        file_name = os.path.basename(file_path).lower()
        
        if file_name == 'package.json':
            content = self.get_file_content(file_path)
            if content:
                try:
                    data = json.loads(content)
                    
                    # Parse dependencies and devDependencies
                    for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                        if dep_type in data:
                            for package, version in data[dep_type].items():
                                dependencies[package] = {
                                    'version': version,
                                    'type': dep_type,
                                    'raw': f"{package}: {version}"
                                }
                except json.JSONDecodeError:
                    pass
        
        return dependencies
    
    def _parse_java_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Parse Java dependency files (basic XML parsing for Maven)"""
        dependencies = {}
        
        if file_path.endswith('pom.xml'):
            content = self.get_file_content(file_path)
            if content:
                # Simple regex-based parsing for Maven dependencies
                dependency_pattern = r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?<version>(.*?)</version>.*?</dependency>'
                matches = re.findall(dependency_pattern, content, re.DOTALL)
                
                for group_id, artifact_id, version in matches:
                    package_name = f"{group_id.strip()}:{artifact_id.strip()}"
                    dependencies[package_name] = {
                        'version': version.strip(),
                        'groupId': group_id.strip(),
                        'artifactId': artifact_id.strip(),
                        'raw': f"{package_name}:{version.strip()}"
                    }
        
        return dependencies
    
    def _analyze_file_dependencies(self, dependencies: Dict[str, Any], file_path: str, ecosystem: str) -> List[Dict]:
        """Analyze dependencies in a single file"""
        issues = []
        
        # Check for unspecified versions
        unspecified_count = 0
        for package, info in dependencies.items():
            if info.get('version') in ['unspecified', '*', 'latest', '']:
                unspecified_count += 1
                issues.append({
                    "file": file_path,
                    "desc": f"Package '{package}' has unspecified version",
                    "severity": "medium",
                    "package": package
                })
        
        # Check for potentially outdated version patterns
        outdated_patterns = ['^0.', '^1.', '~0.', '~1.'] if ecosystem == 'javascript' else []
        for package, info in dependencies.items():
            version = info.get('version', '')
            if any(version.startswith(pattern) for pattern in outdated_patterns):
                issues.append({
                    "file": file_path,
                    "desc": f"Package '{package}' may be using outdated version ({version})",
                    "severity": "low",
                    "package": package
                })
        
        # Check for excessive number of dependencies
        if len(dependencies) > 50:
            issues.append({
                "file": file_path,
                "desc": f"Large number of dependencies ({len(dependencies)}) - consider dependency cleanup",
                "severity": "low"
            })
        
        return issues
    
    async def _analyze_security_vulnerabilities(self, dependency_files: List[Tuple[str, str]], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies for security vulnerabilities"""
        issues = []
        
        # Try to run security audit tools if available
        for file_path, ecosystem in dependency_files:
            relative_path = os.path.relpath(file_path, repo_path)
            
            try:
                if ecosystem == 'python':
                    # Try pip-audit or safety if available
                    audit_issues = await self._run_python_security_audit(file_path, relative_path)
                    issues.extend(audit_issues)
                elif ecosystem == 'javascript':
                    # Try npm audit
                    audit_issues = await self._run_npm_security_audit(file_path, relative_path)
                    issues.extend(audit_issues)
            
            except Exception as e:
                self.logger.error(f"Error running security audit for {file_path}: {e}")
        
        return {"issues": issues}
    
    async def _run_python_security_audit(self, file_path: str, relative_path: str) -> List[Dict]:
        """Run Python security audit using pip-audit or safety"""
        issues = []
        
        try:
            # Try pip-audit first
            result = subprocess.run(
                ['pip-audit', '--format', 'json', '--requirement', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    for vulnerability in audit_data.get('vulnerabilities', []):
                        issues.append({
                            "file": relative_path,
                            "desc": f"Security vulnerability in {vulnerability.get('package', 'unknown')}: {vulnerability.get('description', 'No description')}",
                            "severity": "high",
                            "package": vulnerability.get('package'),
                            "vulnerability_id": vulnerability.get('id')
                        })
                except json.JSONDecodeError:
                    pass
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # pip-audit not available or timeout
            pass
        
        return issues
    
    async def _run_npm_security_audit(self, file_path: str, relative_path: str) -> List[Dict]:
        """Run npm security audit"""
        issues = []
        
        try:
            # Change to directory containing package.json
            package_dir = os.path.dirname(file_path)
            
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=package_dir,
                capture_output=True, text=True, timeout=30
            )
            
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    
                    # Parse npm audit output
                    vulnerabilities = audit_data.get('vulnerabilities', {})
                    for package, vuln_info in vulnerabilities.items():
                        severity = vuln_info.get('severity', 'unknown')
                        issues.append({
                            "file": relative_path,
                            "desc": f"Security vulnerability in {package}: {severity} severity",
                            "severity": "critical" if severity == "critical" else "high" if severity == "high" else "medium",
                            "package": package
                        })
                
                except json.JSONDecodeError:
                    pass
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # npm not available or timeout
            pass
        
        return issues
    
    async def _analyze_licenses(self, dependency_files: List[Tuple[str, str]], repo_path: str) -> Dict[str, Any]:
        """Analyze dependency licenses"""
        issues = []
        license_info = {}
        
        # For now, we'll do basic license analysis
        # In a production system, you'd want to use proper license detection tools
        
        for file_path, ecosystem in dependency_files:
            relative_path = os.path.relpath(file_path, repo_path)
            dependencies = self._parse_dependency_file(file_path, ecosystem)
            
            # Check for known problematic packages (example list)
            problematic_packages = {
                'python': ['gpgme', 'pycrypto'],
                'javascript': ['natives', 'event-stream'],
            }
            
            for package in dependencies.keys():
                if package in problematic_packages.get(ecosystem, []):
                    issues.append({
                        "file": relative_path,
                        "desc": f"Package '{package}' has known licensing/security issues",
                        "severity": "medium",
                        "package": package
                    })
        
        # Check for license file in repository
        license_files = []
        for root, dirs, files in os.walk(repo_path):
            if root != repo_path:  # Only check root directory
                break
            for file in files:
                if file.lower() in ['license', 'licence', 'license.txt', 'license.md', 'copying']:
                    license_files.append(file)
        
        if not license_files:
            issues.append({
                "desc": "No LICENSE file found in repository root",
                "severity": "medium"
            })
        
        return {"issues": issues, "license_files": license_files}
    
    async def _analyze_dependency_management(self, dependency_files: List[Tuple[str, str]], repo_path: str) -> Dict[str, Any]:
        """Analyze dependency management practices"""
        issues = []
        
        # Check for lock files
        ecosystems_found = set(ecosystem for _, ecosystem in dependency_files)
        
        for ecosystem in ecosystems_found:
            ecosystem_files = [f for f, e in dependency_files if e == ecosystem]
            
            if ecosystem == 'python':
                has_requirements = any('requirements.txt' in f for f in ecosystem_files)
                has_lock = any('poetry.lock' in f or 'Pipfile.lock' in f for f in ecosystem_files)
                
                if has_requirements and not has_lock:
                    issues.append({
                        "desc": "Python project lacks dependency lock file (consider using poetry or pipenv)",
                        "severity": "low"
                    })
            
            elif ecosystem == 'javascript':
                has_package_json = any('package.json' in f for f in ecosystem_files)
                has_lock = any('package-lock.json' in f or 'yarn.lock' in f for f in ecosystem_files)
                
                if has_package_json and not has_lock:
                    issues.append({
                        "desc": "JavaScript project lacks lock file (package-lock.json or yarn.lock)",
                        "severity": "medium"
                    })
        
        # Check for multiple package managers in same ecosystem
        js_files = [f for f, e in dependency_files if e == 'javascript']
        if js_files:
            has_npm = any('package-lock.json' in f for f in js_files)
            has_yarn = any('yarn.lock' in f for f in js_files)
            
            if has_npm and has_yarn:
                issues.append({
                    "desc": "Mixed package managers detected (npm and yarn) - choose one for consistency",
                    "severity": "low"
                })
        
        return {"issues": issues}
    
    async def _analyze_with_llm(self, sample_files: List[Tuple[str, str]], repo_path: str) -> Dict[str, Any]:
        """Use LLM for dependency analysis"""
        issues = []
        
        for file_path, ecosystem in sample_files:
            try:
                content = self.get_file_content(file_path, max_size=10000)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                result = await self.llm_provider.analyze_code(
                    content,
                    "dependencies",
                    {"file_path": relative_path, "ecosystem": ecosystem, "analysis_type": "dependency_management"}
                )
                
                if "issues" in result:
                    for issue in result["issues"]:
                        issue["file"] = relative_path
                        issues.append(issue)
            
            except Exception as e:
                self.logger.error(f"Error in LLM dependency analysis for {file_path}: {e}")
        
        return {"issues": issues}
    
    def _calculate_dependency_score(self, issues: List[Dict], dependency_analysis: Dict, 
                                  security_analysis: Dict, license_analysis: Dict) -> int:
        """Calculate overall dependency score"""
        base_score = 100
        
        # Penalty for issues by severity
        severity_weights = {"low": 1, "medium": 5, "high": 15, "critical": 30}
        issue_penalty = sum(severity_weights.get(issue.get("severity", "low"), 1) for issue in issues)
        
        # Bonus for good practices
        bonus = 0
        
        # Bonus for having lock files
        management_issues = [i for i in issues if 'lock file' in i.get('desc', '').lower()]
        if not management_issues:
            bonus += 10
        
        # Bonus for not having security vulnerabilities
        security_issues = [i for i in issues if 'vulnerability' in i.get('desc', '').lower()]
        if not security_issues:
            bonus += 20
        
        # Bonus for having license file
        license_issues = [i for i in issues if 'LICENSE' in i.get('desc', '')]
        if not license_issues:
            bonus += 5
        
        # Calculate final score
        final_score = base_score - issue_penalty + bonus
        return max(0, min(100, final_score))
    
    def _generate_suggestions(self, issues: List[Dict], dependency_analysis: Dict, 
                            security_analysis: Dict) -> List[str]:
        """Generate dependency improvement suggestions"""
        suggestions = []
        
        # Security suggestions
        security_issues = [i for i in issues if 'vulnerability' in i.get('desc', '').lower()]
        if security_issues:
            suggestions.append("Update vulnerable dependencies immediately")
            suggestions.append("Set up automated security scanning in CI/CD pipeline")
        
        # Version management suggestions
        version_issues = [i for i in issues if 'version' in i.get('desc', '').lower()]
        if version_issues:
            suggestions.append("Pin dependency versions to ensure reproducible builds")
        
        # Lock file suggestions
        lock_issues = [i for i in issues if 'lock' in i.get('desc', '').lower()]
        if lock_issues:
            suggestions.append("Use lock files to ensure consistent dependency versions across environments")
        
        # License suggestions
        license_issues = [i for i in issues if 'license' in i.get('desc', '').lower() or 'LICENSE' in i.get('desc', '')]
        if license_issues:
            suggestions.append("Add a LICENSE file and review dependency licenses for compatibility")
        
        # Dependency count suggestions
        count_issues = [i for i in issues if 'number of dependencies' in i.get('desc', '')]
        if count_issues:
            suggestions.append("Review and remove unused dependencies to reduce attack surface")
        
        # General suggestions
        suggestions.append("Regularly update dependencies to latest stable versions")
        suggestions.append("Use dependency scanning tools in your development workflow")
        suggestions.append("Consider using dependabot or similar tools for automated updates")
        
        return suggestions
    
    def _generate_summary(self, score: int, dependency_analysis: Dict, 
                         security_analysis: Dict, license_analysis: Dict) -> str:
        """Generate dependency analysis summary"""
        total_deps = dependency_analysis.get('total_dependencies', 0)
        summary = f"Dependency analysis completed with score {score}/100. "
        summary += f"Found {total_deps} total dependencies across all files. "
        
        # Security summary
        security_issues = security_analysis.get('issues', [])
        critical_security = [i for i in security_issues if i.get('severity') == 'critical']
        high_security = [i for i in security_issues if i.get('severity') == 'high']
        
        if critical_security:
            summary += f"CRITICAL: {len(critical_security)} critical security vulnerabilities found. "
        elif high_security:
            summary += f"WARNING: {len(high_security)} high-severity security issues found. "
        elif security_issues:
            summary += f"{len(security_issues)} security issues found. "
        else:
            summary += "No security vulnerabilities detected. "
        
        # License summary
        license_files = license_analysis.get('license_files', [])
        if license_files:
            summary += "Project has license documentation. "
        else:
            summary += "No license file found. "
        
        # Overall assessment
        if score >= 90:
            summary += "Excellent dependency management!"
        elif score >= 75:
            summary += "Good dependency practices with minor improvements needed."
        elif score >= 50:
            summary += "Dependency management needs attention."
        else:
            summary += "Significant dependency issues require immediate action."
        
        return summary
