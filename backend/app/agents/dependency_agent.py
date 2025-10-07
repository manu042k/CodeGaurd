"""
Dependency Analysis Agent
Analyzes project dependencies for security vulnerabilities, outdated packages, and license issues.
Uses hybrid rule-based + LLM approach.
"""

import re
import json
from typing import List, Dict, Any, Optional
import time
from pathlib import Path
from ..agents.base_agent import BaseAgent, AgentResult, Issue, Severity
from ..config import get_config_manager


class DependencyAgent(BaseAgent):
    """Agent for analyzing project dependencies"""

    # Package file patterns
    PACKAGE_FILES = {
        "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"],
        "javascript": ["package.json", "yarn.lock", "package-lock.json"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "go": ["go.mod", "go.sum"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "php": ["composer.json", "composer.lock"],
        "csharp": ["*.csproj", "packages.config"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_service: Optional[Any] = None):
        """Initialize dependency agent"""
        super().__init__(config, llm_service)
        self.config_manager = get_config_manager()
        self.rules = self.config_manager.get_rules_for_agent("dependency")

    @property
    def name(self) -> str:
        return "DependencyAgent"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Analyzes dependencies for vulnerabilities, outdated packages, and license issues"

    @property
    def supported_languages(self) -> List[str]:
        return ["python", "javascript", "typescript", "java", "go", "ruby", "rust", "php", "csharp"]

    async def _rule_based_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
        **kwargs
    ) -> AgentResult:
        """
        Fast rule-based dependency analysis
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            language: Programming language
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with dependency issues
        """
        start_time = time.time()
        issues: List[Issue] = []

        try:
            self.log_info(f"Running rule-based dependency analysis on {file_path}")

            # Detect package file type
            file_type = self._detect_package_file_type(file_path)
            
            if not file_type:
                # Not a dependency file
                return self._create_result(
                    file_path=file_path,
                    execution_time=time.time() - start_time
                )

            # Parse dependencies
            dependencies = self._parse_dependencies(file_content, file_type, language)

            # Check for known vulnerable patterns
            issues.extend(self._check_known_vulnerable_packages(
                dependencies, file_path, language
            ))

            # Check for outdated package patterns
            issues.extend(self._check_outdated_patterns(
                dependencies, file_path, language
            ))

            # Check for insecure version constraints
            issues.extend(self._check_version_constraints(
                dependencies, file_path, language
            ))

            # Check for deprecated packages
            issues.extend(self._check_deprecated_packages(
                dependencies, file_path, language
            ))

            execution_time = time.time() - start_time
            score = self.calculate_score(issues)

            metrics = {
                "total_dependencies": len(dependencies),
                "total_issues": len(issues),
                "critical_issues": sum(1 for i in issues if i.severity == Severity.CRITICAL),
                "high_issues": sum(1 for i in issues if i.severity == Severity.HIGH),
                "file_type": file_type,
            }

            self.log_info(f"Found {len(issues)} dependency issues in {file_path}")

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

    def _detect_package_file_type(self, file_path: str) -> Optional[str]:
        """Detect type of package file"""
        filename = Path(file_path).name.lower()
        
        if filename == "requirements.txt" or filename.endswith(".txt"):
            return "requirements"
        elif filename == "package.json":
            return "npm"
        elif filename == "pipfile":
            return "pipfile"
        elif filename == "pyproject.toml":
            return "pyproject"
        elif filename == "pom.xml":
            return "maven"
        elif filename.endswith("build.gradle"):
            return "gradle"
        elif filename == "go.mod":
            return "gomod"
        elif filename == "gemfile":
            return "gemfile"
        elif filename == "cargo.toml":
            return "cargo"
        elif filename == "composer.json":
            return "composer"
        
        return None

    def _parse_dependencies(
        self, content: str, file_type: str, language: str
    ) -> List[Dict[str, Any]]:
        """Parse dependencies from file content"""
        dependencies = []

        if file_type == "requirements":
            dependencies = self._parse_requirements_txt(content)
        elif file_type == "npm":
            dependencies = self._parse_package_json(content)
        elif file_type == "pipfile":
            dependencies = self._parse_pipfile(content)
        elif file_type == "gomod":
            dependencies = self._parse_go_mod(content)
        elif file_type == "gemfile":
            dependencies = self._parse_gemfile(content)

        return dependencies

    def _parse_requirements_txt(self, content: str) -> List[Dict[str, Any]]:
        """Parse requirements.txt file"""
        dependencies = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse package and version
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*([><=!~]+)\s*(.+)$', line)
            if match:
                name, operator, version = match.groups()
                dependencies.append({
                    "name": name,
                    "version": version.strip(),
                    "operator": operator.strip(),
                    "raw": line
                })
            elif '==' not in line and '>=' not in line:
                # Package without version
                dependencies.append({
                    "name": line,
                    "version": None,
                    "operator": None,
                    "raw": line
                })

        return dependencies

    def _parse_package_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse package.json file"""
        dependencies = []
        
        try:
            data = json.loads(content)
            
            # Parse dependencies
            for section in ["dependencies", "devDependencies"]:
                if section in data:
                    for name, version in data[section].items():
                        dependencies.append({
                            "name": name,
                            "version": version.strip('^~'),
                            "operator": self._extract_npm_operator(version),
                            "dev": section == "devDependencies",
                            "raw": f"{name}@{version}"
                        })
        
        except json.JSONDecodeError:
            self.log_error("Failed to parse package.json")

        return dependencies

    def _parse_pipfile(self, content: str) -> List[Dict[str, Any]]:
        """Parse Pipfile"""
        dependencies = []
        
        # Simple TOML-like parsing
        in_packages = False
        for line in content.split('\n'):
            line = line.strip()
            
            if line == "[packages]" or line == "[dev-packages]":
                in_packages = True
                continue
            
            if line.startswith('[') and in_packages:
                in_packages = False
                continue
            
            if in_packages and '=' in line:
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', line)
                if match:
                    name, version = match.groups()
                    dependencies.append({
                        "name": name,
                        "version": version.strip('*'),
                        "raw": line
                    })

        return dependencies

    def _parse_go_mod(self, content: str) -> List[Dict[str, Any]]:
        """Parse go.mod file"""
        dependencies = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('require'):
                continue
            
            match = re.match(r'^([a-zA-Z0-9/_.-]+)\s+v([0-9.]+)', line)
            if match:
                name, version = match.groups()
                dependencies.append({
                    "name": name,
                    "version": version,
                    "raw": line
                })

        return dependencies

    def _parse_gemfile(self, content: str) -> List[Dict[str, Any]]:
        """Parse Gemfile"""
        dependencies = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('gem'):
                match = re.match(r"gem\s+'([^']+)'(?:,\s+'([^']+)')?", line)
                if match:
                    name = match.group(1)
                    version = match.group(2) if match.group(2) else None
                    dependencies.append({
                        "name": name,
                        "version": version.strip('~>') if version else None,
                        "raw": line
                    })

        return dependencies

    def _extract_npm_operator(self, version_string: str) -> str:
        """Extract version operator from npm version string"""
        if version_string.startswith('^'):
            return '^'
        elif version_string.startswith('~'):
            return '~'
        elif version_string.startswith('>='):
            return '>='
        elif version_string.startswith('>'):
            return '>'
        else:
            return '=='

    def _check_known_vulnerable_packages(
        self, dependencies: List[Dict[str, Any]], file_path: str, language: str
    ) -> List[Issue]:
        """Check for known vulnerable packages"""
        issues = []
        
        # Known vulnerable packages (sample list)
        vulnerable_packages = {
            "python": {
                "django": {"<2.2.28", "<3.2.13"},
                "requests": {"<2.27.0"},
                "pillow": {"<9.0.0"},
                "pyyaml": {"<5.4"},
            },
            "javascript": {
                "lodash": {"<4.17.21"},
                "axios": {"<0.21.1"},
                "jquery": {"<3.5.0"},
                "express": {"<4.17.3"},
            }
        }
        
        vuln_db = vulnerable_packages.get(language, {})
        
        for dep in dependencies:
            pkg_name = dep["name"].lower()
            if pkg_name in vuln_db:
                issues.append(Issue(
                    title=f"Potentially Vulnerable Package: {dep['name']}",
                    description=f"Package '{dep['name']}' may have known security vulnerabilities",
                    severity=Severity.HIGH,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Update {dep['name']} to the latest secure version",
                    rule_id="VULNERABLE_PACKAGE",
                    category="dependency",
                    metadata={"package": dep["name"], "version": dep.get("version")}
                ))

        return issues

    def _check_outdated_patterns(
        self, dependencies: List[Dict[str, Any]], file_path: str, language: str
    ) -> List[Issue]:
        """Check for obviously outdated packages"""
        issues = []
        
        for dep in dependencies:
            version = dep.get("version")
            if not version:
                issues.append(Issue(
                    title=f"Unpinned Dependency: {dep['name']}",
                    description=f"Package '{dep['name']}' has no version specified",
                    severity=Severity.MEDIUM,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Pin {dep['name']} to a specific version for reproducibility",
                    rule_id="UNPINNED_DEPENDENCY",
                    category="dependency",
                ))
            elif version and self._looks_very_old(version):
                issues.append(Issue(
                    title=f"Potentially Outdated Package: {dep['name']}",
                    description=f"Package '{dep['name']}' version {version} appears very old",
                    severity=Severity.LOW,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Check if {dep['name']} has newer versions available",
                    rule_id="OUTDATED_PACKAGE",
                    category="dependency",
                ))

        return issues

    def _looks_very_old(self, version: str) -> bool:
        """Heuristic to detect very old versions"""
        # Extract major version
        match = re.match(r'^v?([0-9]+)', version)
        if match:
            major = int(match.group(1))
            # Major version 0 or 1 might be old (context-dependent)
            return major == 0
        return False

    def _check_version_constraints(
        self, dependencies: List[Dict[str, Any]], file_path: str, language: str
    ) -> List[Issue]:
        """Check for insecure version constraints"""
        issues = []
        
        for dep in dependencies:
            operator = dep.get("operator", "")
            
            # Check for wildcard versions
            if dep.get("version") == "*" or dep.get("version") == "latest":
                issues.append(Issue(
                    title=f"Wildcard Version: {dep['name']}",
                    description=f"Package '{dep['name']}' uses wildcard version which may introduce breaking changes",
                    severity=Severity.MEDIUM,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Pin {dep['name']} to a specific version range",
                    rule_id="WILDCARD_VERSION",
                    category="dependency",
                ))
            
            # Check for >= without upper bound
            elif operator == ">=":
                issues.append(Issue(
                    title=f"Unbounded Version Range: {dep['name']}",
                    description=f"Package '{dep['name']}' uses >= without upper bound, may introduce breaking changes",
                    severity=Severity.LOW,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Use a bounded range like >={dep.get('version')},<{int(dep.get('version', '2').split('.')[0]) + 1}.0",
                    rule_id="UNBOUNDED_VERSION",
                    category="dependency",
                ))

        return issues

    def _check_deprecated_packages(
        self, dependencies: List[Dict[str, Any]], file_path: str, language: str
    ) -> List[Issue]:
        """Check for deprecated packages"""
        issues = []
        
        # Known deprecated packages (sample list)
        deprecated_packages = {
            "python": ["sha", "md5", "pycrypto"],
            "javascript": ["request", "bower", "node-uuid"],
        }
        
        deprecated_list = deprecated_packages.get(language, [])
        
        for dep in dependencies:
            if dep["name"].lower() in deprecated_list:
                issues.append(Issue(
                    title=f"Deprecated Package: {dep['name']}",
                    description=f"Package '{dep['name']}' is deprecated and no longer maintained",
                    severity=Severity.MEDIUM,
                    file_path=file_path,
                    code_snippet=dep["raw"],
                    suggestion=f"Replace {dep['name']} with a maintained alternative",
                    rule_id="DEPRECATED_PACKAGE",
                    category="dependency",
                ))

        return issues

    def _get_agent_specific_instructions(self) -> str:
        """Dependency-specific instructions for LLM analysis"""
        return """Perform comprehensive dependency analysis. Focus on:

1. SECURITY VULNERABILITIES:
   - Known CVEs in specific versions
   - Transitive dependency vulnerabilities
   - Supply chain attack risks
   - Typosquatting attempts

2. LICENSE COMPATIBILITY:
   - Incompatible license combinations
   - GPL/AGPL restrictions
   - Commercial use restrictions
   - Attribution requirements

3. MAINTENANCE STATUS:
   - Abandoned packages (no updates in 2+ years)
   - Deprecated packages
   - Better maintained alternatives
   - Active security patches

4. VERSION CONFLICTS:
   - Conflicting version requirements
   - Peer dependency issues
   - Breaking changes in updates
   - Compatibility problems

5. BEST PRACTICES:
   - Missing lock files
   - Overly permissive version ranges
   - Too many dependencies (bloat)
   - Unused dependencies

6. SUPPLY CHAIN RISKS:
   - Package ownership changes
   - Recently created packages
   - Suspicious package names
   - Unusual update patterns

Consider the specific ecosystem ({language}) and modern best practices.
Suggest specific alternatives where applicable."""
