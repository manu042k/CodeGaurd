"""
Trend & Regression Agent - Tracks changes between multiple analysis runs over time
"""
import json
import sqlite3
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from .base_agent import BaseAgent

class TrendAgent(BaseAgent):
    """Agent for tracking trends and regressions across analysis runs"""
    
    def __init__(self, llm_provider, db_path: Optional[str] = None):
        super().__init__("Trend & Regression Agent", "Trends", llm_provider)
        
        # Database for storing historical data
        self.db_path = db_path or os.path.join(os.getcwd(), 'trend_analysis.db')
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing historical analysis data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repo_path TEXT NOT NULL,
                        commit_hash TEXT,
                        branch TEXT,
                        timestamp TEXT NOT NULL,
                        overall_score INTEGER NOT NULL,
                        category_scores TEXT NOT NULL,
                        total_issues INTEGER NOT NULL,
                        critical_issues INTEGER NOT NULL,
                        high_issues INTEGER NOT NULL,
                        medium_issues INTEGER NOT NULL,
                        low_issues INTEGER NOT NULL,
                        agent_results TEXT NOT NULL,
                        metadata TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS trend_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repo_path TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                conn.execute('''CREATE INDEX IF NOT EXISTS idx_repo_timestamp ON analysis_runs(repo_path, timestamp)''')
                conn.execute('''CREATE INDEX IF NOT EXISTS idx_alerts_repo ON trend_alerts(repo_path, resolved)''')
        
        except Exception as e:
            self.logger.error(f"Error initializing trend database: {e}")
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze trends and regressions (called after main analysis)"""
        self.logger.info(f"Starting trend analysis for {repo_path}")
        
        # Get current analysis results from context
        current_results = context.get('current_analysis') if context else None
        if not current_results:
            return self.create_result_structure(
                score=100,
                summary="No current analysis data provided for trend analysis"
            )
        
        # Store current analysis
        self._store_analysis_run(repo_path, current_results, context)
        
        # Get historical data
        historical_data = self._get_historical_data(repo_path, limit=10)
        
        if len(historical_data) < 2:
            return self.create_result_structure(
                score=100,
                summary="Insufficient historical data for trend analysis (need at least 2 runs)"
            )
        
        # Perform trend analysis
        trend_analysis = self._analyze_trends(historical_data)
        regression_analysis = self._analyze_regressions(historical_data)
        improvement_analysis = self._analyze_improvements(historical_data)
        
        # Generate alerts
        alerts = self._generate_trend_alerts(trend_analysis, regression_analysis, repo_path)
        
        # Calculate trend score
        trend_score = self._calculate_trend_score(trend_analysis, regression_analysis, improvement_analysis)
        
        # Generate insights
        insights = self._generate_trend_insights(trend_analysis, regression_analysis, improvement_analysis)
        
        # Create trend summary
        summary = self._generate_trend_summary(trend_analysis, len(historical_data))
        
        return self.create_result_structure(
            score=trend_score,
            issues=alerts,
            summary=summary,
            suggestions=insights
        )
    
    def _store_analysis_run(self, repo_path: str, analysis_results: Dict[str, Any], context: Optional[Dict] = None):
        """Store analysis run in database"""
        try:
            # Extract key metrics
            overall_score = analysis_results.get('overall_score', 0)
            category_scores = analysis_results.get('category_breakdown', {})
            all_issues = analysis_results.get('all_issues', [])
            
            # Count issues by severity
            issue_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            for issue in all_issues:
                severity = issue.get('severity', 'low')
                if severity in issue_counts:
                    issue_counts[severity] += 1
            
            # Get git information if available
            git_info = self._get_git_info(repo_path)
            
            # Prepare metadata
            metadata = {
                'execution_time': analysis_results.get('execution_time', 0),
                'agents_executed': analysis_results.get('agents_executed', []),
                'failed_agents': analysis_results.get('failed_agents', []),
                'repository_stats': context.get('repository_stats', {}) if context else {}
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO analysis_runs (
                        repo_path, commit_hash, branch, timestamp, overall_score,
                        category_scores, total_issues, critical_issues, high_issues,
                        medium_issues, low_issues, agent_results, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repo_path,
                    git_info.get('commit_hash'),
                    git_info.get('branch'),
                    datetime.utcnow().isoformat(),
                    overall_score,
                    json.dumps(category_scores),
                    len(all_issues),
                    issue_counts['critical'],
                    issue_counts['high'],
                    issue_counts['medium'],
                    issue_counts['low'],
                    json.dumps(analysis_results),
                    json.dumps(metadata)
                ))
        
        except Exception as e:
            self.logger.error(f"Error storing analysis run: {e}")
    
    def _get_git_info(self, repo_path: str) -> Dict[str, Any]:
        """Get git information about the repository"""
        try:
            import subprocess
            
            # Get current commit hash
            commit_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'commit_hash': commit_result.stdout.strip() if commit_result.returncode == 0 else None,
                'branch': branch_result.stdout.strip() if branch_result.returncode == 0 else None
            }
        
        except Exception:
            return {'commit_hash': None, 'branch': None}
    
    def _get_historical_data(self, repo_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical analysis data for the repository"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM analysis_runs 
                    WHERE repo_path = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (repo_path, limit))
                
                rows = cursor.fetchall()
                
                historical_data = []
                for row in rows:
                    data = dict(row)
                    data['category_scores'] = json.loads(data['category_scores'])
                    data['agent_results'] = json.loads(data['agent_results'])
                    if data['metadata']:
                        data['metadata'] = json.loads(data['metadata'])
                    historical_data.append(data)
                
                return historical_data
        
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
    
    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall trends in the data"""
        if len(historical_data) < 2:
            return {}
        
        # Sort by timestamp (newest first)
        historical_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        current = historical_data[0]
        previous = historical_data[1]
        
        # Calculate overall score trend
        score_change = current['overall_score'] - previous['overall_score']
        
        # Calculate category trends
        current_categories = current['category_scores']
        previous_categories = previous['category_scores']
        
        category_trends = {}
        for category in set(list(current_categories.keys()) + list(previous_categories.keys())):
            current_score = current_categories.get(category, 0)
            previous_score = previous_categories.get(category, 0)
            category_trends[category] = current_score - previous_score
        
        # Calculate issue trends
        issue_trends = {
            'total': current['total_issues'] - previous['total_issues'],
            'critical': current['critical_issues'] - previous['critical_issues'],
            'high': current['high_issues'] - previous['high_issues'],
            'medium': current['medium_issues'] - previous['medium_issues'],
            'low': current['low_issues'] - previous['low_issues']
        }
        
        # Determine trend direction
        if score_change > 5:
            trend_direction = "improving"
            trend_icon = "📈"
        elif score_change < -5:
            trend_direction = "declining"
            trend_icon = "📉"
        else:
            trend_direction = "stable"
            trend_icon = "➡️"
        
        # Calculate velocity (rate of change)
        if len(historical_data) >= 3:
            older = historical_data[2]
            time_diff_1 = datetime.fromisoformat(current['timestamp']) - datetime.fromisoformat(previous['timestamp'])
            time_diff_2 = datetime.fromisoformat(previous['timestamp']) - datetime.fromisoformat(older['timestamp'])
            
            if time_diff_1.days > 0 and time_diff_2.days > 0:
                velocity_1 = score_change / time_diff_1.days
                velocity_2 = (previous['overall_score'] - older['overall_score']) / time_diff_2.days
                acceleration = velocity_1 - velocity_2
            else:
                acceleration = 0
        else:
            acceleration = 0
        
        return {
            'overall_change': score_change,
            'trend_direction': trend_direction,
            'trend_icon': trend_icon,
            'category_trends': category_trends,
            'issue_trends': issue_trends,
            'acceleration': acceleration,
            'data_points': len(historical_data)
        }
    
    def _analyze_regressions(self, historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify regressions in code quality"""
        regressions = []
        
        if len(historical_data) < 2:
            return regressions
        
        current = historical_data[0]
        previous = historical_data[1]
        
        # Overall score regression
        score_change = current['overall_score'] - previous['overall_score']
        if score_change < -10:
            regressions.append({
                'type': 'overall_score',
                'severity': 'high' if score_change < -20 else 'medium',
                'change': score_change,
                'description': f"Overall quality score dropped by {abs(score_change)} points"
            })
        
        # Category regressions
        current_categories = current['category_scores']
        previous_categories = previous['category_scores']
        
        for category, current_score in current_categories.items():
            previous_score = previous_categories.get(category, 0)
            change = current_score - previous_score
            
            if change < -15:
                severity = 'high' if change < -25 else 'medium'
                regressions.append({
                    'type': 'category_regression',
                    'category': category,
                    'severity': severity,
                    'change': change,
                    'description': f"{category} score dropped by {abs(change)} points"
                })
        
        # Issue count regressions
        if current['critical_issues'] > previous['critical_issues']:
            increase = current['critical_issues'] - previous['critical_issues']
            regressions.append({
                'type': 'critical_issues',
                'severity': 'critical',
                'change': increase,
                'description': f"Critical issues increased by {increase}"
            })
        
        if current['high_issues'] > previous['high_issues'] + 5:
            increase = current['high_issues'] - previous['high_issues']
            regressions.append({
                'type': 'high_issues',
                'severity': 'high',
                'change': increase,
                'description': f"High-severity issues increased by {increase}"
            })
        
        return regressions
    
    def _analyze_improvements(self, historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify improvements in code quality"""
        improvements = []
        
        if len(historical_data) < 2:
            return improvements
        
        current = historical_data[0]
        previous = historical_data[1]
        
        # Overall score improvement
        score_change = current['overall_score'] - previous['overall_score']
        if score_change > 10:
            improvements.append({
                'type': 'overall_score',
                'change': score_change,
                'description': f"Overall quality score improved by {score_change} points"
            })
        
        # Category improvements
        current_categories = current['category_scores']
        previous_categories = previous['category_scores']
        
        for category, current_score in current_categories.items():
            previous_score = previous_categories.get(category, 0)
            change = current_score - previous_score
            
            if change > 15:
                improvements.append({
                    'type': 'category_improvement',
                    'category': category,
                    'change': change,
                    'description': f"{category} score improved by {change} points"
                })
        
        # Issue count improvements
        if current['critical_issues'] < previous['critical_issues']:
            decrease = previous['critical_issues'] - current['critical_issues']
            improvements.append({
                'type': 'critical_issues_resolved',
                'change': decrease,
                'description': f"Resolved {decrease} critical issues"
            })
        
        if current['high_issues'] < previous['high_issues'] - 3:
            decrease = previous['high_issues'] - current['high_issues']
            improvements.append({
                'type': 'high_issues_resolved',
                'change': decrease,
                'description': f"Resolved {decrease} high-severity issues"
            })
        
        return improvements
    
    def _generate_trend_alerts(self, trend_analysis: Dict[str, Any], 
                             regressions: List[Dict[str, Any]], repo_path: str) -> List[Dict[str, Any]]:
        """Generate alerts based on trend analysis"""
        alerts = []
        
        # Convert regressions to alert format
        for regression in regressions:
            alerts.append({
                'desc': regression['description'],
                'severity': regression['severity'],
                'type': 'regression',
                'category': regression.get('category', 'overall')
            })
        
        # Trend-based alerts
        if trend_analysis.get('overall_change', 0) < -15:
            alerts.append({
                'desc': f"Quality trend is declining ({trend_analysis.get('overall_change', 0):+d} points)",
                'severity': 'high',
                'type': 'trend_decline'
            })
        
        if trend_analysis.get('acceleration', 0) < -2:
            alerts.append({
                'desc': "Quality decline is accelerating",
                'severity': 'medium',
                'type': 'acceleration'
            })
        
        # Store alerts in database
        self._store_alerts(repo_path, alerts)
        
        return alerts
    
    def _store_alerts(self, repo_path: str, alerts: List[Dict[str, Any]]):
        """Store trend alerts in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for alert in alerts:
                    conn.execute('''
                        INSERT INTO trend_alerts (repo_path, alert_type, severity, message, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        repo_path,
                        alert.get('type', 'unknown'),
                        alert.get('severity', 'low'),
                        alert.get('desc', ''),
                        datetime.utcnow().isoformat()
                    ))
        
        except Exception as e:
            self.logger.error(f"Error storing trend alerts: {e}")
    
    def _calculate_trend_score(self, trend_analysis: Dict[str, Any], 
                             regressions: List[Dict[str, Any]], 
                             improvements: List[Dict[str, Any]]) -> int:
        """Calculate trend quality score"""
        base_score = 75  # Neutral starting point
        
        # Overall trend adjustment
        overall_change = trend_analysis.get('overall_change', 0)
        if overall_change > 10:
            base_score += 20
        elif overall_change > 5:
            base_score += 10
        elif overall_change < -10:
            base_score -= 20
        elif overall_change < -5:
            base_score -= 10
        
        # Regression penalties
        for regression in regressions:
            if regression['severity'] == 'critical':
                base_score -= 25
            elif regression['severity'] == 'high':
                base_score -= 15
            elif regression['severity'] == 'medium':
                base_score -= 8
        
        # Improvement bonuses
        for improvement in improvements:
            if improvement['type'] == 'critical_issues_resolved':
                base_score += 15
            else:
                base_score += 5
        
        # Stability bonus (consistent trend direction)
        if abs(trend_analysis.get('acceleration', 0)) < 1:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _generate_trend_insights(self, trend_analysis: Dict[str, Any], 
                               regressions: List[Dict[str, Any]], 
                               improvements: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from trend analysis"""
        insights = []
        
        # Overall trend insights
        overall_change = trend_analysis.get('overall_change', 0)
        if overall_change > 10:
            insights.append("Code quality is improving consistently - maintain current practices")
        elif overall_change < -10:
            insights.append("Code quality is declining - review recent changes and development practices")
        
        # Category-specific insights
        category_trends = trend_analysis.get('category_trends', {})
        declining_categories = [cat for cat, change in category_trends.items() if change < -10]
        improving_categories = [cat for cat, change in category_trends.items() if change > 10]
        
        if declining_categories:
            insights.append(f"Focus improvement efforts on: {', '.join(declining_categories)}")
        
        if improving_categories:
            insights.append(f"Maintain good practices in: {', '.join(improving_categories)}")
        
        # Regression insights
        if any(r['severity'] == 'critical' for r in regressions):
            insights.append("Critical regressions detected - immediate action required")
        
        # Issue trend insights
        issue_trends = trend_analysis.get('issue_trends', {})
        if issue_trends.get('critical', 0) > 0:
            insights.append("New critical issues introduced - prioritize fixing them")
        
        # Velocity insights
        acceleration = trend_analysis.get('acceleration', 0)
        if acceleration > 1:
            insights.append("Quality improvement is accelerating - excellent progress!")
        elif acceleration < -1:
            insights.append("Quality decline is accelerating - urgent intervention needed")
        
        return insights
    
    def _generate_trend_summary(self, trend_analysis: Dict[str, Any], data_points: int) -> str:
        """Generate trend analysis summary"""
        overall_change = trend_analysis.get('overall_change', 0)
        trend_direction = trend_analysis.get('trend_direction', 'stable')
        trend_icon = trend_analysis.get('trend_icon', '➡️')
        
        summary = f"Trend analysis based on {data_points} analysis runs. "
        summary += f"{trend_icon} Code quality is {trend_direction}"
        
        if overall_change != 0:
            summary += f" (change: {overall_change:+d} points)"
        
        summary += ". "
        
        # Add category highlights
        category_trends = trend_analysis.get('category_trends', {})
        if category_trends:
            best_change = max(category_trends.items(), key=lambda x: x[1])
            worst_change = min(category_trends.items(), key=lambda x: x[1])
            
            if best_change[1] > 5:
                summary += f"Best improvement: {best_change[0]} (+{best_change[1]}). "
            
            if worst_change[1] < -5:
                summary += f"Needs attention: {worst_change[0]} ({worst_change[1]:+d}). "
        
        return summary
    
    def get_trend_report(self, repo_path: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive trend report for a repository"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get recent analysis runs
                cursor = conn.execute('''
                    SELECT * FROM analysis_runs 
                    WHERE repo_path = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (repo_path, cutoff_date))
                
                runs = [dict(row) for row in cursor.fetchall()]
                
                # Get recent alerts
                cursor = conn.execute('''
                    SELECT * FROM trend_alerts 
                    WHERE repo_path = ? AND timestamp > ? AND resolved = FALSE
                    ORDER BY timestamp DESC
                ''', (repo_path, cutoff_date))
                
                alerts = [dict(row) for row in cursor.fetchall()]
                
                # Process the data
                for run in runs:
                    run['category_scores'] = json.loads(run['category_scores'])
                
                return {
                    'repo_path': repo_path,
                    'period_days': days,
                    'total_runs': len(runs),
                    'runs': runs,
                    'active_alerts': alerts,
                    'generated_at': datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            self.logger.error(f"Error generating trend report: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old trend data"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Delete old analysis runs
                cursor = conn.execute('DELETE FROM analysis_runs WHERE timestamp < ?', (cutoff_date,))
                deleted_runs = cursor.rowcount
                
                # Delete old resolved alerts
                cursor = conn.execute(
                    'DELETE FROM trend_alerts WHERE timestamp < ? AND resolved = TRUE', 
                    (cutoff_date,)
                )
                deleted_alerts = cursor.rowcount
                
                self.logger.info(f"Cleaned up {deleted_runs} old analysis runs and {deleted_alerts} old alerts")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
