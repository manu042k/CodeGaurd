"""
Summary & Scoring Agent - Aggregates results from all agents and generates unified reports
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_agent import BaseAgent

class SummaryAgent(BaseAgent):
    """Agent for aggregating and summarizing results from all other agents"""
    
    def __init__(self, llm_provider):
        super().__init__("Summary & Scoring Agent", "Summary", llm_provider)
        self.category_weights = {
            "Quality": 0.20,
            "Security": 0.25,
            "Architecture": 0.15,
            "Documentation": 0.10,
            "Testing": 0.15,
            "Dependencies": 0.10,
            "Static Checks": 0.05
        }
    
    def aggregate_results(self, agent_results: Dict[str, Dict[str, Any]], 
                         repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Aggregate results from all agents into a unified report"""
        self.logger.info(f"Aggregating results from {len(agent_results)} agents")
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(agent_results)
        
        # Create category breakdown
        category_breakdown = self._create_category_breakdown(agent_results)
        
        # Generate insights and recommendations
        insights = self._generate_insights(agent_results, overall_score)
        recommendations = self._generate_recommendations(agent_results, overall_score)
        
        # Create executive summary
        executive_summary = self._create_executive_summary(
            overall_score, category_breakdown, agent_results
        )
        
        # Compile all issues with priorities
        all_issues = self._compile_prioritized_issues(agent_results)
        
        # Generate trend analysis if historical data available
        trends = self._analyze_trends(context.get('historical_data', []) if context else [])
        
        # Create dashboard data
        dashboard_data = self._create_dashboard_data(
            overall_score, category_breakdown, all_issues, trends
        )
        
        # Generate detailed report
        detailed_report = self._create_detailed_report(agent_results, repo_path)
        
        return {
            "overall_score": overall_score,
            "category_breakdown": category_breakdown,
            "executive_summary": executive_summary,
            "insights": insights,
            "recommendations": recommendations,
            "all_issues": all_issues,
            "trends": trends,
            "dashboard_data": dashboard_data,
            "detailed_report": detailed_report,
            "analysis_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "agents_run": list(agent_results.keys()),
                "total_issues": len(all_issues),
                "repo_path": repo_path,
                "version": "1.0"
            }
        }
    
    def _calculate_overall_score(self, agent_results: Dict[str, Dict[str, Any]]) -> int:
        """Calculate weighted overall score from all agent results"""
        weighted_sum = 0
        total_weight = 0
        
        for agent_name, result in agent_results.items():
            category = result.get('category', 'Other')
            score = result.get('score', 0)
            weight = self.category_weights.get(category, 0.05)
            
            weighted_sum += score * weight
            total_weight += weight
        
        # Normalize if we have different agents than expected
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = 0
        
        return min(100, max(0, int(round(overall_score))))
    
    def _create_category_breakdown(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Create breakdown of scores by category"""
        category_scores = {}
        
        for agent_name, result in agent_results.items():
            category = result.get('category', 'Other')
            score = result.get('score', 0)
            
            # If multiple agents per category, take average
            if category in category_scores:
                category_scores[category] = (category_scores[category] + score) // 2
            else:
                category_scores[category] = score
        
        return category_scores
    
    def _generate_insights(self, agent_results: Dict[str, Dict[str, Any]], overall_score: int) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        # Overall assessment
        if overall_score >= 90:
            insights.append("🎉 Excellent codebase quality! Your project demonstrates outstanding practices across all areas.")
        elif overall_score >= 80:
            insights.append("✅ Strong codebase foundation with high-quality practices and minor areas for improvement.")
        elif overall_score >= 70:
            insights.append("👍 Good codebase quality with several areas that could benefit from attention.")
        elif overall_score >= 60:
            insights.append("⚠️  Moderate codebase quality - several important improvements needed.")
        else:
            insights.append("🚨 Significant quality issues detected - immediate attention required.")
        
        # Category-specific insights
        category_breakdown = self._create_category_breakdown(agent_results)
        
        # Find strongest and weakest areas
        if category_breakdown:
            best_category = max(category_breakdown.items(), key=lambda x: x[1])
            worst_category = min(category_breakdown.items(), key=lambda x: x[1])
            
            if best_category[1] >= 85:
                insights.append(f"🏆 Strongest area: {best_category[0]} (Score: {best_category[1]}/100)")
            
            if worst_category[1] < 60:
                insights.append(f"🎯 Priority improvement area: {worst_category[0]} (Score: {worst_category[1]}/100)")
        
        # Security-specific insights
        security_result = None
        for result in agent_results.values():
            if result.get('category') == 'Security':
                security_result = result
                break
        
        if security_result:
            security_score = security_result.get('score', 0)
            security_issues = security_result.get('issues', [])
            critical_security = [i for i in security_issues if i.get('severity') == 'critical']
            
            if critical_security:
                insights.append(f"🔒 CRITICAL: {len(critical_security)} critical security vulnerabilities require immediate attention!")
            elif security_score >= 90:
                insights.append("🔒 Excellent security posture with no major vulnerabilities detected.")
            elif security_score < 70:
                insights.append("🔒 Security improvements needed - consider implementing additional security measures.")
        
        # Testing insights
        testing_result = None
        for result in agent_results.values():
            if result.get('category') == 'Testing':
                testing_result = result
                break
        
        if testing_result:
            testing_score = testing_result.get('score', 0)
            if testing_score < 50:
                insights.append("🧪 Low test coverage detected - consider implementing comprehensive testing strategy.")
            elif testing_score >= 80:
                insights.append("🧪 Strong testing practices contributing to code reliability.")
        
        # Technical debt insights
        architecture_result = None
        quality_result = None
        
        for result in agent_results.values():
            if result.get('category') == 'Architecture':
                architecture_result = result
            elif result.get('category') == 'Quality':
                quality_result = result
        
        if architecture_result and quality_result:
            avg_structural_score = (architecture_result.get('score', 0) + quality_result.get('score', 0)) // 2
            if avg_structural_score < 65:
                insights.append("🏗️ Technical debt accumulation detected - consider refactoring initiatives.")
        
        return insights
    
    def _generate_recommendations(self, agent_results: Dict[str, Dict[str, Any]], overall_score: int) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Collect all suggestions with priorities
        all_suggestions = []
        for agent_name, result in agent_results.items():
            category = result.get('category', 'Other')
            score = result.get('score', 0)
            suggestions = result.get('suggestions', [])
            
            for suggestion in suggestions:
                priority = self._calculate_suggestion_priority(category, score, suggestion)
                all_suggestions.append({
                    "category": category,
                    "agent": agent_name,
                    "suggestion": suggestion,
                    "priority": priority,
                    "category_score": score
                })
        
        # Sort by priority and group
        all_suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Create prioritized recommendations
        high_priority = [s for s in all_suggestions if s['priority'] >= 8]
        medium_priority = [s for s in all_suggestions if 5 <= s['priority'] < 8]
        low_priority = [s for s in all_suggestions if s['priority'] < 5]
        
        if high_priority:
            recommendations.append({
                "priority": "HIGH",
                "title": "Immediate Actions Required",
                "description": "Critical issues that should be addressed immediately",
                "items": [item['suggestion'] for item in high_priority[:5]],  # Top 5
                "count": len(high_priority)
            })
        
        if medium_priority:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Important Improvements",
                "description": "Significant improvements that should be planned",
                "items": [item['suggestion'] for item in medium_priority[:7]],  # Top 7
                "count": len(medium_priority)
            })
        
        if low_priority:
            recommendations.append({
                "priority": "LOW",
                "title": "Enhancement Opportunities",
                "description": "Good practices and optimizations for future consideration",
                "items": [item['suggestion'] for item in low_priority[:5]],  # Top 5
                "count": len(low_priority)
            })
        
        return recommendations
    
    def _calculate_suggestion_priority(self, category: str, score: int, suggestion: str) -> int:
        """Calculate priority score for a suggestion (0-10)"""
        base_priority = 5
        
        # Category importance multiplier
        category_multipliers = {
            "Security": 2.0,
            "Quality": 1.5,
            "Testing": 1.3,
            "Architecture": 1.2,
            "Documentation": 1.0,
            "Dependencies": 1.4,
            "Static Checks": 1.0
        }
        
        multiplier = category_multipliers.get(category, 1.0)
        
        # Score-based adjustment (lower scores = higher priority)
        if score < 40:
            score_adjustment = 3
        elif score < 60:
            score_adjustment = 2
        elif score < 80:
            score_adjustment = 1
        else:
            score_adjustment = 0
        
        # Keyword-based priority boost
        high_priority_keywords = ['critical', 'security', 'vulnerability', 'urgent', 'immediate', 'fix']
        medium_priority_keywords = ['improve', 'enhance', 'add', 'implement', 'consider']
        
        suggestion_lower = suggestion.lower()
        
        if any(keyword in suggestion_lower for keyword in high_priority_keywords):
            keyword_boost = 2
        elif any(keyword in suggestion_lower for keyword in medium_priority_keywords):
            keyword_boost = 1
        else:
            keyword_boost = 0
        
        final_priority = (base_priority + score_adjustment + keyword_boost) * multiplier
        return min(10, max(0, int(final_priority)))
    
    def _create_executive_summary(self, overall_score: int, category_breakdown: Dict[str, int], 
                                agent_results: Dict[str, Dict[str, Any]]) -> str:
        """Create executive summary text"""
        summary_parts = []
        
        # Overall assessment
        summary_parts.append(f"Overall code quality score: {overall_score}/100")
        
        # Score interpretation
        if overall_score >= 90:
            grade = "A"
            assessment = "Excellent"
        elif overall_score >= 80:
            grade = "B"
            assessment = "Good"
        elif overall_score >= 70:
            grade = "C"
            assessment = "Satisfactory"
        elif overall_score >= 60:
            grade = "D"
            assessment = "Needs Improvement"
        else:
            grade = "F"
            assessment = "Poor"
        
        summary_parts.append(f"Quality Grade: {grade} ({assessment})")
        
        # Category highlights
        if category_breakdown:
            best_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)
            worst_categories = sorted(category_breakdown.items(), key=lambda x: x[1])
            
            if best_categories[0][1] >= 85:
                summary_parts.append(f"Strongest area: {best_categories[0][0]} ({best_categories[0][1]}/100)")
            
            if worst_categories[0][1] < 60:
                summary_parts.append(f"Needs attention: {worst_categories[0][0]} ({worst_categories[0][1]}/100)")
        
        # Issue count summary
        total_issues = sum(len(result.get('issues', [])) for result in agent_results.values())
        critical_issues = sum(
            len([i for i in result.get('issues', []) if i.get('severity') == 'critical'])
            for result in agent_results.values()
        )
        high_issues = sum(
            len([i for i in result.get('issues', []) if i.get('severity') == 'high'])
            for result in agent_results.values()
        )
        
        if critical_issues > 0:
            summary_parts.append(f"🚨 {critical_issues} critical issues requiring immediate attention")
        if high_issues > 0:
            summary_parts.append(f"⚠️ {high_issues} high-priority issues identified")
        
        summary_parts.append(f"Total issues found: {total_issues}")
        
        return ". ".join(summary_parts) + "."
    
    def _compile_prioritized_issues(self, agent_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compile and prioritize all issues from agents"""
        all_issues = []
        
        for agent_name, result in agent_results.items():
            category = result.get('category', 'Other')
            issues = result.get('issues', [])
            
            for issue in issues:
                enhanced_issue = issue.copy()
                enhanced_issue['agent'] = agent_name
                enhanced_issue['category'] = category
                enhanced_issue['priority_score'] = self._calculate_issue_priority(issue, category)
                all_issues.append(enhanced_issue)
        
        # Sort by priority score (descending) and then by severity
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        all_issues.sort(
            key=lambda x: (x['priority_score'], severity_order.get(x.get('severity', 'low'), 1)),
            reverse=True
        )
        
        return all_issues
    
    def _calculate_issue_priority(self, issue: Dict[str, Any], category: str) -> int:
        """Calculate priority score for an issue"""
        base_score = 5
        
        # Severity multiplier
        severity_multipliers = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        severity_multiplier = severity_multipliers.get(issue.get('severity', 'low'), 1)
        
        # Category importance
        category_multipliers = {
            "Security": 2.0,
            "Quality": 1.2,
            "Testing": 1.1,
            "Architecture": 1.3,
            "Documentation": 0.8,
            "Dependencies": 1.5,
            "Static Checks": 1.0
        }
        category_multiplier = category_multipliers.get(category, 1.0)
        
        return int(base_score * severity_multiplier * category_multiplier)
    
    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends from historical analysis data"""
        if not historical_data or len(historical_data) < 2:
            return {"available": False, "message": "Insufficient historical data for trend analysis"}
        
        # Sort by timestamp
        historical_data.sort(key=lambda x: x.get('timestamp', ''))
        
        current = historical_data[-1]
        previous = historical_data[-2]
        
        # Calculate score changes
        current_score = current.get('overall_score', 0)
        previous_score = previous.get('overall_score', 0)
        score_change = current_score - previous_score
        
        # Calculate category changes
        current_categories = current.get('category_breakdown', {})
        previous_categories = previous.get('category_breakdown', {})
        
        category_changes = {}
        for category in set(list(current_categories.keys()) + list(previous_categories.keys())):
            current_cat_score = current_categories.get(category, 0)
            previous_cat_score = previous_categories.get(category, 0)
            category_changes[category] = current_cat_score - previous_cat_score
        
        # Generate trend summary
        if score_change > 5:
            trend_direction = "improving"
            trend_icon = "📈"
        elif score_change < -5:
            trend_direction = "declining"
            trend_icon = "📉"
        else:
            trend_direction = "stable"
            trend_icon = "➡️"
        
        return {
            "available": True,
            "overall_change": score_change,
            "trend_direction": trend_direction,
            "trend_icon": trend_icon,
            "category_changes": category_changes,
            "summary": f"{trend_icon} Code quality is {trend_direction} (change: {score_change:+d} points)",
            "analysis_count": len(historical_data)
        }
    
    def _create_dashboard_data(self, overall_score: int, category_breakdown: Dict[str, int], 
                             all_issues: List[Dict[str, Any]], trends: Dict[str, Any]) -> Dict[str, Any]:
        """Create data structure optimized for dashboard visualization"""
        
        # Severity distribution
        severity_distribution = {}
        for issue in all_issues:
            severity = issue.get('severity', 'low')
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # Category distribution
        category_distribution = {}
        for issue in all_issues:
            category = issue.get('category', 'Other')
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        # Score ranges for visualization
        score_ranges = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0
        }
        
        for category, score in category_breakdown.items():
            if score >= 85:
                score_ranges["excellent"] += 1
            elif score >= 70:
                score_ranges["good"] += 1
            elif score >= 50:
                score_ranges["fair"] += 1
            else:
                score_ranges["poor"] += 1
        
        return {
            "overall_score": overall_score,
            "category_scores": category_breakdown,
            "severity_distribution": severity_distribution,
            "category_distribution": category_distribution,
            "score_ranges": score_ranges,
            "trends": trends,
            "metrics": {
                "total_issues": len(all_issues),
                "critical_issues": severity_distribution.get('critical', 0),
                "high_issues": severity_distribution.get('high', 0),
                "categories_analyzed": len(category_breakdown),
                "improvement_areas": len([s for s in category_breakdown.values() if s < 70])
            }
        }
    
    def _create_detailed_report(self, agent_results: Dict[str, Dict[str, Any]], repo_path: str) -> str:
        """Create detailed markdown report"""
        report_lines = []
        
        # Header
        report_lines.extend([
            "# Code Quality Analysis Report",
            "",
            f"**Repository:** `{repo_path}`",
            f"**Analysis Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
        ])
        
        # Overall Score
        overall_score = self._calculate_overall_score(agent_results)
        category_breakdown = self._create_category_breakdown(agent_results)
        
        report_lines.extend([
            "## 📊 Overall Results",
            "",
            f"**Overall Score:** {overall_score}/100",
            "",
            "### Category Breakdown",
            ""
        ])
        
        for category, score in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
            status_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            report_lines.append(f"- {status_emoji} **{category}:** {score}/100")
        
        report_lines.append("")
        
        # Detailed Agent Results
        report_lines.extend([
            "## 🔍 Detailed Analysis",
            ""
        ])
        
        for agent_name, result in agent_results.items():
            category = result.get('category', 'Other')
            score = result.get('score', 0)
            summary = result.get('summary', '')
            issues = result.get('issues', [])
            suggestions = result.get('suggestions', [])
            
            report_lines.extend([
                f"### {category} ({agent_name})",
                "",
                f"**Score:** {score}/100",
                "",
                f"**Summary:** {summary}",
                ""
            ])
            
            if issues:
                report_lines.extend([
                    "**Issues Found:**",
                    ""
                ])
                
                # Group issues by severity
                severity_groups = {}
                for issue in issues:
                    severity = issue.get('severity', 'low')
                    if severity not in severity_groups:
                        severity_groups[severity] = []
                    severity_groups[severity].append(issue)
                
                for severity in ['critical', 'high', 'medium', 'low']:
                    if severity in severity_groups:
                        severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}
                        report_lines.append(f"**{severity_emoji.get(severity, '')} {severity.title()} Severity:**")
                        report_lines.append("")
                        
                        for issue in severity_groups[severity][:10]:  # Limit to 10 per severity
                            file_info = f" in `{issue['file']}`" if issue.get('file') else ""
                            line_info = f" (line {issue['line']})" if issue.get('line') else ""
                            report_lines.append(f"- {issue.get('desc', 'No description')}{file_info}{line_info}")
                        
                        if len(severity_groups[severity]) > 10:
                            report_lines.append(f"- ... and {len(severity_groups[severity]) - 10} more")
                        
                        report_lines.append("")
            
            if suggestions:
                report_lines.extend([
                    "**Recommendations:**",
                    ""
                ])
                for suggestion in suggestions[:5]:  # Top 5 suggestions
                    report_lines.append(f"- {suggestion}")
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    async def generate_llm_summary(self, aggregated_results: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Generate additional insights using LLM"""
        try:
            # Prepare summary data for LLM analysis
            summary_data = {
                "overall_score": aggregated_results["overall_score"],
                "category_breakdown": aggregated_results["category_breakdown"],
                "total_issues": len(aggregated_results["all_issues"]),
                "critical_issues": len([i for i in aggregated_results["all_issues"] if i.get('severity') == 'critical']),
                "high_issues": len([i for i in aggregated_results["all_issues"] if i.get('severity') == 'high']),
                "top_categories": sorted(
                    aggregated_results["category_breakdown"].items(), 
                    key=lambda x: x[1], reverse=True
                )[:3]
            }
            
            prompt = f"""
            Based on this code quality analysis summary, provide strategic insights and actionable recommendations:
            
            {json.dumps(summary_data, indent=2)}
            
            Please provide:
            1. Strategic assessment of the codebase health
            2. Priority areas for improvement
            3. Recommended next steps for the development team
            4. Long-term quality improvement roadmap
            """
            
            llm_response = await self.llm_provider.generate_completion(
                prompt,
                "You are a senior software engineering consultant providing strategic code quality advice."
            )
            
            return {
                "llm_insights": llm_response,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error generating LLM summary: {e}")
            return {
                "llm_insights": "LLM analysis unavailable",
                "error": str(e)
            }

    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze and summarize results from other agents
        
        Args:
            repo_path: Path to the repository
            context: Context containing agent_results from other agents
            
        Returns:
            Dict containing summary analysis results in standard format
        """
        try:
            # Get agent results from context
            agent_results = context.get('agent_results', {}) if context else {}
            
            if not agent_results:
                return {
                    'agent': self.name,
                    'category': self.category,
                    'score': 0,
                    'summary': 'No agent results available for summarization',
                    'issues': [],
                    'suggestions': ['Run individual agents first to generate summary'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0'
                }
            
            # Use existing aggregate_results method
            summary_result = self.aggregate_results(agent_results, repo_path, context)
            
            # Convert to standard agent format
            return {
                'agent': self.name,
                'category': self.category,
                'score': summary_result.get('overall_score', 0),
                'summary': summary_result.get('executive_summary', 'Summary analysis completed'),
                'issues': summary_result.get('prioritized_issues', [])[:10],  # Top 10 issues
                'suggestions': summary_result.get('key_recommendations', [])[:5],  # Top 5 recommendations
                'full_report': summary_result,  # Include full detailed report
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
        except Exception as e:
            self.logger.error(f"Summary analysis failed: {e}")
            return {
                'agent': self.name,
                'category': self.category,
                'score': 0,
                'summary': f'Summary analysis failed: {str(e)}',
                'issues': [],
                'suggestions': [],
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
