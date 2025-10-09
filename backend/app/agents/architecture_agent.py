"""
Architecture & Design Agent - Examines system structure, modularity, and design principles adherence
"""
import os
import ast
import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict, deque
from .base_agent import BaseAgent

class ArchitectureAgent(BaseAgent):
    """Agent for analyzing software architecture and design patterns"""
    
    def __init__(self, llm_provider):
        super().__init__("Architecture & Design Agent", "Architecture", llm_provider)
        self.dependency_graph = defaultdict(set)
        self.module_structure = {}
        self.design_patterns = []
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze repository architecture and design"""
        self.logger.info(f"Starting architecture analysis for {repo_path}")
        
        # Reset state for new analysis
        self.dependency_graph.clear()
        self.module_structure.clear()
        self.design_patterns.clear()
        
        # Find and analyze code files
        code_files = self.find_code_files(repo_path)
        
        if not code_files:
            return self.create_result_structure(
                score=100,
                summary="No code files found to analyze architecture"
            )
        
        # Analyze project structure
        structure_analysis = await self._analyze_project_structure(repo_path, code_files)
        
        # Analyze dependencies and coupling
        dependency_analysis = await self._analyze_dependencies(code_files, repo_path)
        
        # Analyze design patterns
        pattern_analysis = await self._analyze_design_patterns(code_files, repo_path)
        
        # LLM analysis for high-level architecture insights
        llm_analysis = await self._analyze_with_llm(code_files[:3], repo_path)  # Sample files
        
        # Combine all analyses
        all_issues = (structure_analysis.get('issues', []) + 
                     dependency_analysis.get('issues', []) + 
                     pattern_analysis.get('issues', []) + 
                     llm_analysis.get('issues', []))
        
        # Calculate overall score
        score = self._calculate_architecture_score(all_issues, structure_analysis, dependency_analysis)
        
        # Generate summary and suggestions
        summary = self._generate_summary(score, structure_analysis, dependency_analysis, len(code_files))
        suggestions = self._generate_suggestions(all_issues, structure_analysis, dependency_analysis)
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def find_code_files(self, repo_path: str) -> List[str]:
        """Find code files for architecture analysis"""
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go']
        return self.find_files_by_extension(repo_path, extensions)
    
    async def _analyze_project_structure(self, repo_path: str, code_files: List[str]) -> Dict[str, Any]:
        """Analyze the overall project structure and organization"""
        issues = []
        
        # Analyze directory structure
        dir_structure = self._analyze_directory_structure(repo_path)
        
        # Check for common architectural patterns
        has_separation = self._check_separation_of_concerns(repo_path, code_files)
        
        # Check for proper layering
        layering_issues = self._check_layering(repo_path, code_files)
        issues.extend(layering_issues)
        
        # Check for configuration management
        config_issues = self._check_configuration_management(repo_path)
        issues.extend(config_issues)
        
        return {
            'directory_structure': dir_structure,
            'separation_of_concerns': has_separation,
            'issues': issues
        }
    
    def _analyze_directory_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze directory structure for architectural patterns"""
        structure = {
            'depth': 0,
            'directories': [],
            'common_patterns': [],
            'organization_score': 0
        }
        
        # Get directory tree
        for root, dirs, files in os.walk(repo_path):
            level = root.replace(repo_path, '').count(os.sep)
            structure['depth'] = max(structure['depth'], level)
            
            if level <= 3:  # Only track top-level structure
                rel_path = os.path.relpath(root, repo_path)
                if rel_path != '.':
                    structure['directories'].append(rel_path)
        
        # Check for common architectural patterns
        common_dirs = ['src', 'lib', 'app', 'components', 'services', 'models', 'controllers', 'views', 'utils', 'config']
        found_patterns = [d for d in common_dirs if any(d in dir_name.lower() for dir_name in structure['directories'])]
        structure['common_patterns'] = found_patterns
        
        # Score organization (0-100)
        structure['organization_score'] = min(100, len(found_patterns) * 15 + (50 if structure['depth'] <= 5 else 0))
        
        return structure
    
    def _check_separation_of_concerns(self, repo_path: str, code_files: List[str]) -> Dict[str, Any]:
        """Check for proper separation of concerns"""
        concerns = {
            'models': [],
            'views': [],
            'controllers': [],
            'services': [],
            'utilities': [],
            'tests': [],
            'config': []
        }
        
        for file_path in code_files:
            rel_path = os.path.relpath(file_path, repo_path).lower()
            
            if 'model' in rel_path or 'entity' in rel_path:
                concerns['models'].append(file_path)
            elif 'view' in rel_path or 'template' in rel_path or 'component' in rel_path:
                concerns['views'].append(file_path)
            elif 'controller' in rel_path or 'router' in rel_path or 'handler' in rel_path:
                concerns['controllers'].append(file_path)
            elif 'service' in rel_path or 'business' in rel_path:
                concerns['services'].append(file_path)
            elif 'util' in rel_path or 'helper' in rel_path:
                concerns['utilities'].append(file_path)
            elif 'test' in rel_path or 'spec' in rel_path:
                concerns['tests'].append(file_path)
            elif 'config' in rel_path or 'setting' in rel_path:
                concerns['config'].append(file_path)
        
        # Calculate separation score
        total_files = len(code_files)
        categorized_files = sum(len(files) for files in concerns.values())
        separation_score = (categorized_files / total_files * 100) if total_files > 0 else 0
        
        return {
            'concerns': concerns,
            'separation_score': separation_score,
            'total_files': total_files,
            'categorized_files': categorized_files
        }
    
    def _check_layering(self, repo_path: str, code_files: List[str]) -> List[Dict]:
        """Check for proper architectural layering"""
        issues = []
        
        # Define typical layers
        layers = {
            'presentation': ['view', 'component', 'ui', 'frontend', 'client'],
            'business': ['service', 'business', 'logic', 'core'],
            'data': ['model', 'entity', 'dao', 'repository', 'database', 'db'],
            'infrastructure': ['config', 'util', 'helper', 'common', 'shared']
        }
        
        layer_files = {layer: [] for layer in layers}
        
        # Categorize files into layers
        for file_path in code_files:
            rel_path = os.path.relpath(file_path, repo_path).lower()
            
            for layer, keywords in layers.items():
                if any(keyword in rel_path for keyword in keywords):
                    layer_files[layer].append(file_path)
                    break
        
        # Check for layer violations (simplified)
        for layer, files in layer_files.items():
            if not files:
                continue
            
            # Sample check: presentation layer shouldn't directly access data layer
            if layer == 'presentation':
                for file_path in files[:3]:  # Check first 3 files
                    content = self.get_file_content(file_path)
                    if content and any(keyword in content.lower() for keyword in ['database', 'sql', 'query']):
                        issues.append({
                            "file": os.path.relpath(file_path, repo_path),
                            "desc": "Presentation layer may be directly accessing data layer",
                            "severity": "medium"
                        })
        
        return issues
    
    def _check_configuration_management(self, repo_path: str) -> List[Dict]:
        """Check configuration management practices"""
        issues = []
        
        # Look for configuration files
        config_files = []
        config_patterns = ['.env', 'config', 'settings', '.ini', '.conf', '.yml', '.yaml', '.json']
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(pattern in file.lower() for pattern in config_patterns):
                    config_files.append(os.path.join(root, file))
        
        if not config_files:
            issues.append({
                "desc": "No configuration files found - consider centralizing configuration",
                "severity": "low"
            })
        elif len(config_files) > 10:
            issues.append({
                "desc": f"Many configuration files found ({len(config_files)}) - consider consolidation",
                "severity": "low"
            })
        
        return issues
    
    async def _analyze_dependencies(self, code_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze module dependencies and coupling"""
        issues = []
        
        # Build dependency graph
        for file_path in code_files:
            try:
                self._extract_dependencies(file_path, repo_path)
            except Exception as e:
                self.logger.error(f"Error extracting dependencies from {file_path}: {e}")
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies()
        for cycle in circular_deps:
            issues.append({
                "desc": f"Circular dependency detected: {' -> '.join(cycle)}",
                "severity": "high"
            })
        
        # Analyze coupling
        coupling_analysis = self._analyze_coupling()
        
        # Check for highly coupled modules
        for module, coupling_score in coupling_analysis.items():
            if coupling_score > 0.8:  # High coupling threshold
                issues.append({
                    "desc": f"Module '{module}' has high coupling (score: {coupling_score:.2f})",
                    "severity": "medium"
                })
        
        return {
            'dependency_graph': dict(self.dependency_graph),
            'circular_dependencies': circular_deps,
            'coupling_analysis': coupling_analysis,
            'issues': issues
        }
    
    def _extract_dependencies(self, file_path: str, repo_path: str):
        """Extract dependencies from a code file"""
        content = self.get_file_content(file_path)
        if not content:
            return
        
        module_name = os.path.relpath(file_path, repo_path)
        
        # Extract imports based on file type
        if file_path.endswith('.py'):
            self._extract_python_dependencies(content, module_name)
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            self._extract_javascript_dependencies(content, module_name)
    
    def _extract_python_dependencies(self, content: str, module_name: str):
        """Extract Python import dependencies"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependency_graph[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.dependency_graph[module_name].add(node.module)
        
        except SyntaxError:
            pass  # Skip files with syntax errors
    
    def _extract_javascript_dependencies(self, content: str, module_name: str):
        """Extract JavaScript/TypeScript import dependencies"""
        import_patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'import\s*\(\s*["\']([^"\']+)["\']\s*\)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.dependency_graph[module_name].add(match)
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in self.dependency_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _analyze_coupling(self) -> Dict[str, float]:
        """Analyze coupling between modules"""
        coupling_scores = {}
        
        for module, dependencies in self.dependency_graph.items():
            if not dependencies:
                coupling_scores[module] = 0.0
                continue
            
            # Simple coupling metric: number of dependencies / total modules
            total_modules = len(self.dependency_graph)
            coupling_score = len(dependencies) / max(total_modules - 1, 1)
            coupling_scores[module] = min(1.0, coupling_score)
        
        return coupling_scores
    
    async def _analyze_design_patterns(self, code_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze usage of design patterns"""
        issues = []
        patterns_found = []
        
        # Sample analysis for common patterns
        for file_path in code_files[:10]:  # Analyze first 10 files
            content = self.get_file_content(file_path)
            if not content:
                continue
            
            relative_path = os.path.relpath(file_path, repo_path)
            
            # Check for Singleton pattern (anti-pattern warning)
            if self._detect_singleton_pattern(content):
                patterns_found.append("Singleton")
                issues.append({
                    "file": relative_path,
                    "desc": "Singleton pattern detected - consider dependency injection instead",
                    "severity": "low"
                })
            
            # Check for Factory pattern
            if self._detect_factory_pattern(content):
                patterns_found.append("Factory")
            
            # Check for Observer pattern
            if self._detect_observer_pattern(content):
                patterns_found.append("Observer")
        
        return {
            'patterns_found': list(set(patterns_found)),
            'issues': issues
        }
    
    def _detect_singleton_pattern(self, content: str) -> bool:
        """Detect Singleton pattern in code"""
        singleton_indicators = [
            r'class.*Singleton',
            r'_instance\s*=\s*None',
            r'def\s+__new__.*if.*not.*instance',
            r'getInstance\(\)',
            r'private\s+static.*instance'
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in singleton_indicators)
    
    def _detect_factory_pattern(self, content: str) -> bool:
        """Detect Factory pattern in code"""
        factory_indicators = [
            r'class.*Factory',
            r'def\s+create.*\(',
            r'def\s+make.*\(',
            r'Factory\s*\(',
            r'createInstance'
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in factory_indicators)
    
    def _detect_observer_pattern(self, content: str) -> bool:
        """Detect Observer pattern in code"""
        observer_indicators = [
            r'class.*Observer',
            r'def\s+notify.*\(',
            r'def\s+update.*\(',
            r'addEventListener',
            r'subscribe.*\(',
            r'emit.*\('
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in observer_indicators)
    
    async def _analyze_with_llm(self, sample_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Use LLM for high-level architecture analysis"""
        issues = []
        
        if not sample_files:
            return {"issues": issues}
        
        # Combine sample files for analysis
        combined_content = ""
        for file_path in sample_files:
            content = self.get_file_content(file_path, max_size=5000)  # Smaller chunks for architecture
            if content:
                relative_path = os.path.relpath(file_path, repo_path)
                combined_content += f"\n\n=== {relative_path} ===\n{content}"
        
        if combined_content:
            try:
                result = await self.llm_provider.analyze_code(
                    combined_content,
                    "architecture",
                    {"analysis_type": "high_level_architecture", "file_count": len(sample_files)}
                )
                
                if "issues" in result:
                    issues.extend(result["issues"])
            
            except Exception as e:
                self.logger.error(f"Error in LLM architecture analysis: {e}")
        
        return {"issues": issues}
    
    def _calculate_architecture_score(self, issues: List[Dict], structure_analysis: Dict, 
                                    dependency_analysis: Dict) -> int:
        """Calculate overall architecture score"""
        base_score = 100
        
        # Penalty for issues
        severity_weights = {"low": 2, "medium": 8, "high": 20, "critical": 40}
        issue_penalty = sum(severity_weights.get(issue.get("severity", "low"), 2) for issue in issues)
        
        # Bonus for good structure
        structure_bonus = 0
        if structure_analysis.get('directory_structure', {}).get('organization_score', 0) > 70:
            structure_bonus += 10
        
        if structure_analysis.get('separation_of_concerns', {}).get('separation_score', 0) > 60:
            structure_bonus += 15
        
        # Penalty for circular dependencies
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        circular_penalty = len(circular_deps) * 15
        
        # Calculate final score
        final_score = base_score - issue_penalty + structure_bonus - circular_penalty
        return max(0, min(100, final_score))
    
    def _generate_suggestions(self, issues: List[Dict], structure_analysis: Dict, 
                            dependency_analysis: Dict) -> List[str]:
        """Generate architecture improvement suggestions"""
        suggestions = []
        
        # Structure-based suggestions
        org_score = structure_analysis.get('directory_structure', {}).get('organization_score', 0)
        if org_score < 50:
            suggestions.append("Improve project organization by using standard directory structures (src/, lib/, components/)")
        
        sep_score = structure_analysis.get('separation_of_concerns', {}).get('separation_score', 0)
        if sep_score < 60:
            suggestions.append("Better separate concerns by organizing code into distinct layers (models, views, controllers)")
        
        # Dependency-based suggestions
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        if circular_deps:
            suggestions.append("Resolve circular dependencies by introducing interfaces or restructuring modules")
        
        coupling_issues = [issue for issue in issues if "coupling" in issue.get("desc", "").lower()]
        if coupling_issues:
            suggestions.append("Reduce coupling by using dependency injection and interface-based design")
        
        # Pattern-based suggestions
        singleton_issues = [issue for issue in issues if "singleton" in issue.get("desc", "").lower()]
        if singleton_issues:
            suggestions.append("Replace Singleton patterns with dependency injection for better testability")
        
        # General suggestions
        suggestions.append("Consider implementing SOLID principles for better maintainability")
        suggestions.append("Use design patterns appropriately to solve recurring problems")
        suggestions.append("Regularly review and refactor architecture to prevent technical debt")
        
        return suggestions
    
    def _generate_summary(self, score: int, structure_analysis: Dict, 
                         dependency_analysis: Dict, total_files: int) -> str:
        """Generate architecture analysis summary"""
        summary = f"Architecture analysis of {total_files} files completed with score {score}/100. "
        
        # Structure summary
        org_score = structure_analysis.get('directory_structure', {}).get('organization_score', 0)
        sep_score = structure_analysis.get('separation_of_concerns', {}).get('separation_score', 0)
        
        if org_score > 70 and sep_score > 60:
            summary += "Good project organization and separation of concerns. "
        elif org_score > 50 or sep_score > 40:
            summary += "Moderate project structure with room for improvement. "
        else:
            summary += "Project structure needs significant improvement. "
        
        # Dependency summary
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        if circular_deps:
            summary += f"Found {len(circular_deps)} circular dependencies that need attention. "
        else:
            summary += "No circular dependencies detected. "
        
        # Overall assessment
        if score >= 85:
            summary += "Excellent architectural design!"
        elif score >= 70:
            summary += "Good architecture with minor areas for improvement."
        elif score >= 50:
            summary += "Architecture has some issues that should be addressed."
        else:
            summary += "Architecture needs significant restructuring."
        
        return summary
