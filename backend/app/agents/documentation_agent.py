"""
Documentation & Comment Agent - Ensures the codebase is well-documented and easy to understand
"""
import os
import ast
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    """Agent for analyzing documentation quality and completeness"""
    
    def __init__(self, llm_provider):
        super().__init__("Documentation & Comment Agent", "Documentation", llm_provider)
        self.doc_file_extensions = ['.md', '.rst', '.txt', '.adoc']
        self.readme_patterns = ['readme', 'read_me', 'read-me']
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze repository documentation quality"""
        self.logger.info(f"Starting documentation analysis for {repo_path}")
        
        # Find code and documentation files
        code_files = self.find_code_files(repo_path)
        doc_files = self.find_documentation_files(repo_path)
        
        if not code_files:
            return self.create_result_structure(
                score=100,
                summary="No code files found to analyze documentation"
            )
        
        # Analyze different aspects of documentation
        code_doc_analysis = await self._analyze_code_documentation(code_files, repo_path)
        readme_analysis = await self._analyze_readme_files(repo_path)
        comment_analysis = await self._analyze_inline_comments(code_files, repo_path)
        api_doc_analysis = await self._analyze_api_documentation(code_files, repo_path)
        
        # LLM analysis for documentation quality
        sample_files = self._select_sample_files(code_files, max_files=3)
        llm_analysis = await self._analyze_with_llm(sample_files, repo_path)
        
        # Combine all issues
        all_issues = (code_doc_analysis.get('issues', []) + 
                     readme_analysis.get('issues', []) + 
                     comment_analysis.get('issues', []) + 
                     api_doc_analysis.get('issues', []) + 
                     llm_analysis.get('issues', []))
        
        # Find missing documentation files
        missing_docs = self._find_missing_documentation(code_files, repo_path)
        
        # Calculate score
        score = self._calculate_documentation_score(
            all_issues, code_doc_analysis, readme_analysis, len(code_files)
        )
        
        # Generate summary and suggestions
        summary = self._generate_summary(score, code_doc_analysis, readme_analysis, len(code_files))
        suggestions = self._generate_suggestions(all_issues, missing_docs, code_doc_analysis)
        
        return self.create_result_structure(
            score=score,
            issues=all_issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def find_code_files(self, repo_path: str) -> List[str]:
        """Find code files for documentation analysis"""
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go']
        return self.find_files_by_extension(repo_path, extensions)
    
    def find_documentation_files(self, repo_path: str) -> List[str]:
        """Find documentation files"""
        doc_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_lower = file.lower()
                file_path = os.path.join(root, file)
                
                # Check for documentation files
                if (any(file_lower.endswith(ext) for ext in self.doc_file_extensions) or
                    any(pattern in file_lower for pattern in self.readme_patterns) or
                    file_lower in ['changelog', 'contributing', 'license', 'authors', 'install']):
                    doc_files.append(file_path)
        
        return doc_files
    
    async def _analyze_code_documentation(self, code_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze docstring coverage and quality in code files"""
        issues = []
        stats = {
            'total_functions': 0,
            'documented_functions': 0,
            'total_classes': 0,
            'documented_classes': 0,
            'total_modules': 0,
            'documented_modules': 0
        }
        
        for file_path in code_files:
            try:
                relative_path = os.path.relpath(file_path, repo_path)
                
                if file_path.endswith('.py'):
                    file_issues, file_stats = self._analyze_python_documentation(file_path, relative_path)
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    file_issues, file_stats = self._analyze_javascript_documentation(file_path, relative_path)
                else:
                    continue
                
                issues.extend(file_issues)
                for key, value in file_stats.items():
                    stats[key] += value
            
            except Exception as e:
                self.logger.error(f"Error analyzing documentation in {file_path}: {e}")
        
        return {'issues': issues, 'stats': stats}
    
    def _analyze_python_documentation(self, file_path: str, relative_path: str) -> tuple:
        """Analyze Python file documentation"""
        issues = []
        stats = {
            'total_functions': 0, 'documented_functions': 0,
            'total_classes': 0, 'documented_classes': 0,
            'total_modules': 0, 'documented_modules': 0
        }
        
        content = self.get_file_content(file_path)
        if not content:
            return issues, stats
        
        try:
            tree = ast.parse(content)
            
            # Check module docstring
            stats['total_modules'] = 1
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                stats['documented_modules'] = 1
            else:
                issues.append({
                    "file": relative_path,
                    "line": 1,
                    "desc": "Module missing docstring",
                    "severity": "low"
                })
            
            # Check classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    stats['total_classes'] += 1
                    class_docstring = ast.get_docstring(node)
                    if class_docstring:
                        stats['documented_classes'] += 1
                        # Check docstring quality
                        if len(class_docstring.strip()) < 10:
                            issues.append({
                                "file": relative_path,
                                "line": node.lineno,
                                "desc": f"Class '{node.name}' has very short docstring",
                                "severity": "low"
                            })
                    else:
                        issues.append({
                            "file": relative_path,
                            "line": node.lineno,
                            "desc": f"Class '{node.name}' missing docstring",
                            "severity": "medium"
                        })
                
                elif isinstance(node, ast.FunctionDef):
                    # Skip private methods and simple getters/setters
                    if node.name.startswith('_') and not node.name.startswith('__'):
                        continue
                    
                    stats['total_functions'] += 1
                    func_docstring = ast.get_docstring(node)
                    
                    if func_docstring:
                        stats['documented_functions'] += 1
                        # Check for parameter documentation
                        if node.args.args and 'param' not in func_docstring.lower():
                            issues.append({
                                "file": relative_path,
                                "line": node.lineno,
                                "desc": f"Function '{node.name}' docstring missing parameter descriptions",
                                "severity": "low"
                            })
                    else:
                        # Check if function is complex enough to need documentation
                        function_lines = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 0
                        if function_lines > 5 or len(node.args.args) > 2:
                            issues.append({
                                "file": relative_path,
                                "line": node.lineno,
                                "desc": f"Function '{node.name}' missing docstring",
                                "severity": "medium"
                            })
        
        except SyntaxError:
            issues.append({
                "file": relative_path,
                "desc": "Could not parse file for documentation analysis",
                "severity": "low"
            })
        
        return issues, stats
    
    def _analyze_javascript_documentation(self, file_path: str, relative_path: str) -> tuple:
        """Analyze JavaScript/TypeScript file documentation"""
        issues = []
        stats = {
            'total_functions': 0, 'documented_functions': 0,
            'total_classes': 0, 'documented_classes': 0,
            'total_modules': 0, 'documented_modules': 0
        }
        
        content = self.get_file_content(file_path)
        if not content:
            return issues, stats
        
        lines = content.split('\n')
        stats['total_modules'] = 1
        
        # Check for file-level JSDoc comment
        file_comment_found = False
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if '/**' in line or '/*' in line:
                file_comment_found = True
                break
        
        if file_comment_found:
            stats['documented_modules'] = 1
        else:
            issues.append({
                "file": relative_path,
                "line": 1,
                "desc": "File missing header comment/documentation",
                "severity": "low"
            })
        
        # Simple pattern matching for functions and classes
        function_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\(',
            r'(\w+)\s*:\s*function\s*\(',
            r'(\w+)\s*\([^)]*\)\s*{',  # Arrow functions
        ]
        
        class_patterns = [
            r'class\s+(\w+)',
            r'interface\s+(\w+)',
        ]
        
        for i, line in enumerate(lines, 1):
            # Check for function definitions
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    stats['total_functions'] += 1
                    
                    # Check if previous lines have JSDoc comment
                    has_jsdoc = False
                    for j in range(max(0, i-5), i):
                        if j < len(lines) and ('/**' in lines[j] or '*' in lines[j]):
                            has_jsdoc = True
                            break
                    
                    if has_jsdoc:
                        stats['documented_functions'] += 1
                    else:
                        issues.append({
                            "file": relative_path,
                            "line": i,
                            "desc": f"Function '{func_name}' missing JSDoc comment",
                            "severity": "low"
                        })
            
            # Check for class definitions
            for pattern in class_patterns:
                match = re.search(pattern, line)
                if match:
                    class_name = match.group(1)
                    stats['total_classes'] += 1
                    
                    # Check if previous lines have JSDoc comment
                    has_jsdoc = False
                    for j in range(max(0, i-5), i):
                        if j < len(lines) and ('/**' in lines[j] or '*' in lines[j]):
                            has_jsdoc = True
                            break
                    
                    if has_jsdoc:
                        stats['documented_classes'] += 1
                    else:
                        issues.append({
                            "file": relative_path,
                            "line": i,
                            "desc": f"Class '{class_name}' missing JSDoc comment",
                            "severity": "medium"
                        })
        
        return issues, stats
    
    async def _analyze_readme_files(self, repo_path: str) -> Dict[str, Any]:
        """Analyze README and other documentation files"""
        issues = []
        readme_files = []
        
        # Find README files
        for root, dirs, files in os.walk(repo_path):
            if root != repo_path:  # Only check root directory
                break
                
            for file in files:
                if any(pattern in file.lower() for pattern in self.readme_patterns):
                    readme_files.append(os.path.join(root, file))
        
        if not readme_files:
            issues.append({
                "desc": "No README file found in repository root",
                "severity": "high"
            })
            return {'issues': issues, 'readme_quality': 0}
        
        # Analyze README quality
        readme_quality = 0
        for readme_file in readme_files:
            content = self.get_file_content(readme_file)
            if content:
                quality_score = self._analyze_readme_content(content, readme_file, issues)
                readme_quality = max(readme_quality, quality_score)
        
        return {'issues': issues, 'readme_quality': readme_quality}
    
    def _analyze_readme_content(self, content: str, file_path: str, issues: List[Dict]) -> int:
        """Analyze README content quality"""
        quality_score = 0
        content_lower = content.lower()
        relative_path = os.path.basename(file_path)
        
        # Check for essential sections
        essential_sections = {
            'title': ['#', 'title'],
            'description': ['description', 'about', 'overview'],
            'installation': ['install', 'setup', 'getting started'],
            'usage': ['usage', 'example', 'how to'],
            'contributing': ['contribut', 'development'],
            'license': ['license', 'copyright']
        }
        
        sections_found = []
        for section, keywords in essential_sections.items():
            if any(keyword in content_lower for keyword in keywords):
                sections_found.append(section)
                quality_score += 15
        
        # Check README length (should be substantial)
        if len(content) < 200:
            issues.append({
                "file": relative_path,
                "desc": "README is very short - consider adding more details",
                "severity": "medium"
            })
        elif len(content) > 500:
            quality_score += 10
        
        # Check for code examples
        if '```' in content or '    ' in content:  # Code blocks
            quality_score += 15
        else:
            issues.append({
                "file": relative_path,
                "desc": "README lacks code examples",
                "severity": "low"
            })
        
        # Missing essential sections
        missing_sections = [s for s in essential_sections.keys() if s not in sections_found]
        for section in missing_sections:
            if section in ['title', 'description', 'installation']:
                issues.append({
                    "file": relative_path,
                    "desc": f"README missing {section} section",
                    "severity": "medium"
                })
            else:
                issues.append({
                    "file": relative_path,
                    "desc": f"README missing {section} section",
                    "severity": "low"
                })
        
        return min(100, quality_score)
    
    async def _analyze_inline_comments(self, code_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze inline comments quality"""
        issues = []
        
        # Sample a few files for comment analysis
        sample_files = self._select_sample_files(code_files, max_files=5)
        
        for file_path in sample_files:
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                file_issues = self._analyze_file_comments(content, relative_path)
                issues.extend(file_issues)
            
            except Exception as e:
                self.logger.error(f"Error analyzing comments in {file_path}: {e}")
        
        return {'issues': issues}
    
    def _analyze_file_comments(self, content: str, file_path: str) -> List[Dict]:
        """Analyze comments in a single file"""
        issues = []
        lines = content.split('\n')
        
        comment_lines = 0
        code_lines = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Detect comments
            is_comment = (stripped.startswith('#') or 
                         stripped.startswith('//') or 
                         stripped.startswith('/*') or 
                         stripped.startswith('*'))
            
            if is_comment:
                comment_lines += 1
                
                # Check for poor comment quality
                if len(stripped) < 5:  # Very short comments
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "desc": "Very short or unclear comment",
                        "severity": "low"
                    })
                
                # Check for TODO/FIXME without explanation
                if any(word in stripped.upper() for word in ['TODO', 'FIXME', 'HACK', 'XXX']):
                    if len(stripped) < 15:  # TODO without proper explanation
                        issues.append({
                            "file": file_path,
                            "line": i,
                            "desc": "TODO/FIXME comment lacks detailed explanation",
                            "severity": "low"
                        })
            else:
                code_lines += 1
        
        # Check comment-to-code ratio
        if code_lines > 0:
            comment_ratio = comment_lines / (comment_lines + code_lines)
            if comment_ratio < 0.05:  # Less than 5% comments
                issues.append({
                    "file": file_path,
                    "desc": f"Low comment density ({comment_ratio:.1%}) - consider adding more explanatory comments",
                    "severity": "low"
                })
        
        return issues
    
    async def _analyze_api_documentation(self, code_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze API documentation quality"""
        issues = []
        
        # Look for API-related files
        api_files = [f for f in code_files if 'api' in f.lower() or 'router' in f.lower() or 'controller' in f.lower()]
        
        for file_path in api_files[:3]:  # Check first 3 API files
            try:
                content = self.get_file_content(file_path)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Check for API endpoint documentation
                if file_path.endswith('.py'):
                    if '@app.route' in content or '@router.' in content:
                        # Flask/FastAPI endpoints
                        if '"""' not in content and "'''" not in content:
                            issues.append({
                                "file": relative_path,
                                "desc": "API endpoints lack documentation",
                                "severity": "medium"
                            })
                
                elif file_path.endswith(('.js', '.ts')):
                    if 'router.' in content or 'app.' in content:
                        # Express.js endpoints
                        if '/**' not in content:
                            issues.append({
                                "file": relative_path,
                                "desc": "API endpoints lack JSDoc documentation",
                                "severity": "medium"
                            })
            
            except Exception as e:
                self.logger.error(f"Error analyzing API documentation in {file_path}: {e}")
        
        return {'issues': issues}
    
    def _select_sample_files(self, code_files: List[str], max_files: int = 5) -> List[str]:
        """Select representative files for detailed analysis"""
        if len(code_files) <= max_files:
            return code_files
        
        # Prioritize by file size and certain patterns
        scored_files = []
        for file_path in code_files:
            score = 0
            try:
                score += os.path.getsize(file_path) // 1000  # Size score
                
                # Bonus for important files
                file_lower = file_path.lower()
                if any(pattern in file_lower for pattern in ['main', 'index', 'app', 'core']):
                    score += 1000
                if any(pattern in file_lower for pattern in ['api', 'service', 'model']):
                    score += 500
                
                scored_files.append((file_path, score))
            except OSError:
                scored_files.append((file_path, 0))
        
        # Sort by score and take top files
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in scored_files[:max_files]]
    
    async def _analyze_with_llm(self, sample_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Use LLM for documentation quality analysis"""
        issues = []
        
        for file_path in sample_files:
            try:
                content = self.get_file_content(file_path, max_size=8000)
                if not content:
                    continue
                
                relative_path = os.path.relpath(file_path, repo_path)
                
                result = await self.llm_provider.analyze_code(
                    content,
                    "documentation",
                    {"file_path": relative_path, "analysis_focus": "documentation_quality"}
                )
                
                if "issues" in result:
                    for issue in result["issues"]:
                        issue["file"] = relative_path
                        issues.append(issue)
            
            except Exception as e:
                self.logger.error(f"Error in LLM documentation analysis for {file_path}: {e}")
        
        return {"issues": issues}
    
    def _find_missing_documentation(self, code_files: List[str], repo_path: str) -> List[str]:
        """Find files that likely need documentation"""
        missing_docs = []
        
        # Files that should have good documentation
        important_patterns = ['main', 'index', 'app', 'core', 'service', 'model', 'api']
        
        for file_path in code_files:
            relative_path = os.path.relpath(file_path, repo_path)
            file_lower = relative_path.lower()
            
            # Check if it's an important file
            if any(pattern in file_lower for pattern in important_patterns):
                content = self.get_file_content(file_path)
                if content:
                    # Quick check for minimal documentation
                    has_docs = ('"""' in content or "'''" in content or 
                              '/**' in content or '/*' in content)
                    
                    if not has_docs:
                        missing_docs.append(relative_path)
        
        return missing_docs
    
    def _calculate_documentation_score(self, issues: List[Dict], code_doc_analysis: Dict, 
                                     readme_analysis: Dict, total_files: int) -> int:
        """Calculate overall documentation score"""
        base_score = 100
        
        # Penalty for issues
        severity_weights = {"low": 1, "medium": 4, "high": 10, "critical": 20}
        issue_penalty = sum(severity_weights.get(issue.get("severity", "low"), 1) for issue in issues)
        
        # Code documentation score
        stats = code_doc_analysis.get('stats', {})
        code_doc_score = 0
        
        if stats.get('total_functions', 0) > 0:
            func_coverage = stats['documented_functions'] / stats['total_functions']
            code_doc_score += func_coverage * 30
        
        if stats.get('total_classes', 0) > 0:
            class_coverage = stats['documented_classes'] / stats['total_classes']
            code_doc_score += class_coverage * 20
        
        if stats.get('total_modules', 0) > 0:
            module_coverage = stats['documented_modules'] / stats['total_modules']
            code_doc_score += module_coverage * 10
        
        # README quality bonus
        readme_quality = readme_analysis.get('readme_quality', 0)
        readme_bonus = readme_quality * 0.4  # Scale down to max 40 points
        
        # Calculate final score
        final_score = min(100, max(0, base_score - issue_penalty + code_doc_score + readme_bonus - 60))
        return int(final_score)
    
    def _generate_suggestions(self, issues: List[Dict], missing_docs: List[str], 
                            code_doc_analysis: Dict) -> List[str]:
        """Generate documentation improvement suggestions"""
        suggestions = []
        
        # README suggestions
        readme_issues = [i for i in issues if 'README' in i.get('desc', '')]
        if readme_issues or not any('README' in i.get('file', '') for i in issues):
            suggestions.append("Create or improve README with installation, usage, and contribution guidelines")
        
        # Code documentation suggestions
        stats = code_doc_analysis.get('stats', {})
        
        if stats.get('total_functions', 0) > 0:
            func_coverage = stats['documented_functions'] / stats['total_functions']
            if func_coverage < 0.6:
                suggestions.append("Add docstrings to functions, especially public APIs and complex logic")
        
        if stats.get('total_classes', 0) > 0:
            class_coverage = stats['documented_classes'] / stats['total_classes']
            if class_coverage < 0.7:
                suggestions.append("Document all public classes with their purpose and usage")
        
        # Missing documentation
        if missing_docs:
            suggestions.append(f"Add documentation to important files: {', '.join(missing_docs[:3])}")
        
        # Comment quality
        comment_issues = [i for i in issues if 'comment' in i.get('desc', '').lower()]
        if comment_issues:
            suggestions.append("Improve inline comments quality - explain 'why' not just 'what'")
        
        # API documentation
        api_issues = [i for i in issues if 'API' in i.get('desc', '')]
        if api_issues:
            suggestions.append("Add comprehensive API documentation with examples and parameters")
        
        # General suggestions
        suggestions.append("Use consistent documentation style throughout the project")
        suggestions.append("Consider generating API documentation automatically from code comments")
        
        return suggestions
    
    def _generate_summary(self, score: int, code_doc_analysis: Dict, 
                         readme_analysis: Dict, total_files: int) -> str:
        """Generate documentation analysis summary"""
        summary = f"Documentation analysis of {total_files} files completed with score {score}/100. "
        
        # Code documentation stats
        stats = code_doc_analysis.get('stats', {})
        
        if stats.get('total_functions', 0) > 0:
            func_coverage = stats['documented_functions'] / stats['total_functions']
            summary += f"Function documentation coverage: {func_coverage:.1%}. "
        
        if stats.get('total_classes', 0) > 0:
            class_coverage = stats['documented_classes'] / stats['total_classes']
            summary += f"Class documentation coverage: {class_coverage:.1%}. "
        
        # README quality
        readme_quality = readme_analysis.get('readme_quality', 0)
        if readme_quality > 70:
            summary += "Good README documentation. "
        elif readme_quality > 40:
            summary += "README needs improvement. "
        else:
            summary += "README missing or inadequate. "
        
        # Overall assessment
        if score >= 85:
            summary += "Excellent documentation quality!"
        elif score >= 70:
            summary += "Good documentation with room for improvement."
        elif score >= 50:
            summary += "Documentation needs significant enhancement."
        else:
            summary += "Poor documentation - major improvements needed."
        
        return summary
